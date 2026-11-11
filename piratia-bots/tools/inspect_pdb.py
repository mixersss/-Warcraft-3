"""Read PE sections and matching MSF7/PDB public symbols without executing inputs."""
import argparse
import hashlib
import json
import struct
from pathlib import Path


def pe_info(data):
    if data[:2] != b'MZ':
        raise ValueError('Not a PE executable')
    pe = struct.unpack_from('<I', data, 60)[0]
    if data[pe:pe+4] != b'PE\0\0':
        raise ValueError('Invalid PE signature')
    count = struct.unpack_from('<H', data, pe + 6)[0]
    optional_size = struct.unpack_from('<H', data, pe + 20)[0]
    optional = pe + 24
    if struct.unpack_from('<H', data, optional)[0] != 0x10b:
        raise ValueError('Expected 32-bit PE')
    image_base = struct.unpack_from('<I', data, optional + 28)[0]
    sections = []
    for i in range(count):
        start = optional + optional_size + 40 * i
        size, rva, raw_size, raw = struct.unpack_from('<IIII', data, start + 8)
        sections.append(dict(name=data[start:start+8].rstrip(b'\0').decode('ascii'),
                             size=size, rva=rva, raw_size=raw_size, raw=raw))
    debug = data.index(b'RSDS')
    return image_base, sections, data[debug+4:debug+20], struct.unpack_from('<I', data, debug+20)[0]


def pdb_streams(data):
    if not data.startswith(b'Microsoft C/C++ MSF 7.00'):
        raise ValueError('Expected MSF7 PDB')
    block_size, _, blocks_total, directory_size, _, block_map = struct.unpack_from('<6I', data, 32)
    if block_size not in (512, 1024, 2048, 4096) or blocks_total * block_size > len(data):
        raise ValueError('Invalid MSF block layout')
    count = (directory_size + block_size - 1) // block_size
    pages = struct.unpack_from('<' + 'I' * count, data, block_map * block_size)
    directory = b''.join(data[p*block_size:(p+1)*block_size] for p in pages)[:directory_size]
    n = struct.unpack_from('<I', directory)[0]
    sizes = struct.unpack_from('<' + 'I' * n, directory, 4)
    position = 4 + n * 4
    streams = []
    for size in sizes:
        if size == 0xffffffff:
            streams.append(b'')
            continue
        count = (size + block_size - 1) // block_size
        pages = struct.unpack_from('<' + 'I' * count, directory, position)
        position += count * 4
        if any(p >= blocks_total for p in pages):
            raise ValueError('PDB page outside file')
        streams.append(b''.join(data[p*block_size:(p+1)*block_size] for p in pages)[:size])
    return streams


def inspect(exe, pdb):
    image_base, sections, guid, age = pe_info(exe)
    streams = pdb_streams(pdb)
    if streams[1][12:28] != guid or struct.unpack_from('<I', streams[1], 8)[0] != age:
        raise ValueError('PDB GUID/age does not match executable')
    index = struct.unpack_from('<H', streams[3], 20)[0]
    stream = streams[index]
    position = 0
    symbols = []
    while position + 4 <= len(stream):
        size, kind = struct.unpack_from('<HH', stream, position)
        if size < 2 or position + size + 2 > len(stream):
            raise ValueError('Invalid symbol record')
        record = stream[position+4:position+size+2]
        if kind == 0x110e and len(record) >= 10:
            _, offset, segment = struct.unpack_from('<IIH', record)
            if 1 <= segment <= len(sections):
                section = sections[segment-1]
                symbols.append(dict(name=record[10:].split(b'\0')[0].decode('cp1252', errors='replace'),
                                    rva=section['rva'] + offset,
                                    va=image_base + section['rva'] + offset,
                                    file_offset=section['raw'] + offset if offset < section['raw_size'] else None))
        position += size + 2
    return dict(exe_sha256=hashlib.sha256(exe).hexdigest(),
                pdb_sha256=hashlib.sha256(pdb).hexdigest(),
                pdb_matches=True, image_base=image_base, sections=sections, symbols=symbols)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exe', type=Path)
    parser.add_argument('pdb', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = inspect(args.exe.read_bytes(), args.pdb.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(f"Matched EXE/PDB; {len(result['symbols'])} public symbols. No input executed or changed.")
