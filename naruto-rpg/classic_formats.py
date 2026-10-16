import struct,zlib
MASK=0xffffffff
MPQ_SECTOR_SHIFT=3
MPQ_SECTOR_SIZE=4096


def i(*values: int) -> bytes:
    return struct.pack('<' + 'i' * len(values), *values)

def f(*values: float) -> bytes:
    return struct.pack('<' + 'f' * len(values), *values)

def s(value: str) -> bytes:
    return value.encode('utf-8') + b'\0'

def object_table(entries: list, extended: bool) -> bytes:
    data = bytearray(i(len(entries)))
    for original, custom, changes in entries:
        data += original.encode('ascii') + custom.encode('ascii') + i(len(changes))
        for change in changes:
            field, kind, value = change[:3]
            data += field.encode('ascii') + i(kind)
            if extended:
                data += i(*change[3:]) if len(change) == 5 else i(0, 0)
            data += s(value) if kind == 3 else f(value) if kind in (1, 2) else i(value)
            data += custom.encode('ascii')
    return bytes(data)

def objects(entries: list, extended: bool = False, original_entries: list | None = None) -> bytes:
    return i(2)+object_table(original_entries or [], extended)+object_table(entries, extended)

def crypt_table() -> list[int]:
    table = [0]*0x500
    seed = 0x100001
    for low in range(256):
        for high in range(5):
            seed = (seed*125+3) % 0x2AAAAB
            upper = (seed & 0xFFFF) << 16
            seed = (seed*125+3) % 0x2AAAAB
            table[high*256+low] = upper | (seed & 0xFFFF)
    return table

CRYPT=crypt_table()

def mpq_hash(name: str, kind: int) -> int:
    a, b = 0x7FED7FED, 0xEEEEEEEE
    for char in name.replace('/', '\\').upper().encode('ascii'):
        a = (CRYPT[kind*256+char] ^ (a+b)) & MASK
        b = (char+a+b+(b << 5)+3) & MASK
    return a

def encrypt_table(data: bytes, key: int) -> bytes:
    seed = 0xEEEEEEEE
    out = bytearray()
    for (value,) in struct.iter_unpack('<I', data):
        seed = (seed+CRYPT[0x400+(key & 255)]) & MASK
        out += struct.pack('<I', value ^ ((key+seed) & MASK))
        key = ((((~key & MASK) << 21)+0x11111111) | (key >> 11)) & MASK
        seed = (value+seed+(seed << 5)+3) & MASK
    return bytes(out)

def sector_file(payload: bytes) -> bytes:
    if not payload:
        return b''
    count = (len(payload)+MPQ_SECTOR_SIZE-1)//MPQ_SECTOR_SIZE
    offsets = [(count+1)*4]
    chunks = []
    for start in range(0,len(payload),MPQ_SECTOR_SIZE):
        raw = payload[start:start+MPQ_SECTOR_SIZE]
        compressed = b'\x02'+zlib.compress(raw,9)
        stored = compressed if len(compressed)<len(raw) else raw
        chunks.append(stored)
        offsets.append(offsets[-1]+len(stored))
    return struct.pack('<'+'I'*len(offsets),*offsets)+b''.join(chunks)

def archive(files: dict[str, bytes], name: str) -> bytes:
    files = dict(files)
    files['(listfile)'] = ('\r\n'.join(sorted(files))+'\r\n(listfile)\r\n').encode('ascii')
    # The Warcraft header is outside the MPQ, padded to a 512-byte boundary.
    wrapper = b'HM3W'+i(0)+s(name)+i(0x60, 12)
    assert len(wrapper) < 512
    wrapper = wrapper.ljust(512, b'\0')
    table_size = 4
    while table_size < len(files)*2:
        table_size *= 2
    hashes = [b'\xff'*16 for _ in range(table_size)]
    blocks, content = bytearray(), bytearray()
    for block, (filename, payload) in enumerate(sorted(files.items())):
        slot = mpq_hash(filename, 0) % table_size
        while hashes[slot] != b'\xff'*16:
            slot = (slot+1) % table_size
        hashes[slot] = struct.pack('<IIHHI', mpq_hash(filename, 1), mpq_hash(filename, 2), 0, 0, block)
        # Use ordinary sector files, as Classic World Editor does. The 0.4.0
        # compressed SINGLE_UNIT layout passed modern readers but the user's
        # 1.26 Storm reader failed in SFile.cpp. Keep each inflate bounded to
        # 4096 bytes and include an explicit sector-offset table.
        stored = sector_file(payload)
        flags = 0x80000200 if payload else 0x80000000
        blocks += struct.pack('<IIII', 32+len(content), len(stored), len(payload), flags)
        content += stored
    hash_pos = 32+len(content)
    block_pos = hash_pos+16*table_size
    hashes_bytes = encrypt_table(b''.join(hashes), mpq_hash('(hash table)', 3))
    blocks_bytes = encrypt_table(bytes(blocks), mpq_hash('(block table)', 3))
    length = block_pos+len(blocks_bytes)
    header = struct.pack('<4sIIHHIIII', b'MPQ\x1a', 32, length, 0, MPQ_SECTOR_SHIFT, hash_pos, block_pos, table_size, len(files))
    return wrapper+header+content+hashes_bytes+blocks_bytes
