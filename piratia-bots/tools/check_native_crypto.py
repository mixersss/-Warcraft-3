"""Optional developer check: emulate crypto routines from the exact supplied PE.

Requires Unicorn 2.1.4, only for development. No Windows process or imports run.
Usage: python tools/check_native_crypto.py /path/to/GateServer.exe
"""
import argparse
import hashlib
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from classic_crypto import Noise, packet_b, password_key, triple_des
from inspect_pdb import pe_info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exe', type=Path)
    args = parser.parse_args()
    raw = args.exe.read_bytes()
    expected = 'a8d6eaa1922ae3d80044a5764a32cbe8a670af727fb2d63e7741b263fbfae89b'
    if hashlib.sha256(raw).hexdigest() != expected:
        parser.error('Executable does not match the audited GateServer build')
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
    from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EAX

    base, sections, *_ = pe_info(raw)
    emulator = Uc(UC_ARCH_X86, UC_MODE_32)
    emulator.mem_map(base, 0x200000)
    emulator.mem_write(base, raw[:0x400])
    for section in sections:
        emulator.mem_write(base + section['rva'],
                           raw[section['raw']:section['raw'] + section['raw_size']])
    emulator.mem_map(0x1000000, 0x200000)
    emulator.mem_map(0x2000000, 0x100000)
    emulator.mem_map(0xf00000, 0x1000)

    def call(address, parameters):
        stack = 0x1100000
        emulator.mem_write(stack, struct.pack('<' + 'I' * (len(parameters) + 1),
                                             0xf00000, *parameters))
        emulator.reg_write(UC_X86_REG_ESP, stack)
        emulator.emu_start(address, 0xf00000, count=10000000)
        return emulator.reg_read(UC_X86_REG_EAX)

    data_ptr, out_ptr, key_ptr = 0x2000000, 0x2001000, 0x2002000
    key, data = bytes.fromhex('83f12a007f92'), bytes(range(67))
    emulator.mem_write(data_ptr, data)
    emulator.mem_write(key_ptr, key)
    call(0x42b6b0, [data_ptr, len(data), key_ptr, len(key), 1])
    if bytes(emulator.mem_read(data_ptr, len(data))) != packet_b(data, key):
        raise AssertionError('Native B encrypt differs')
    call(0x42b6b0, [data_ptr, len(data), key_ptr, len(key), 0])
    if bytes(emulator.mem_read(data_ptr, len(data))) != data:
        raise AssertionError('Native B decrypt differs')

    seed = bytes([1, 2, 4, 8])
    for address, decrypt in ((0x42e5a0, False), (0x42e6e0, True)):
        noise = Noise(seed)
        emulator.mem_write(key_ptr, seed)
        for count in (2, 4, 7, 8, 9, 32, 33, 67, 8):
            emulator.mem_write(data_ptr, data[:count])
            call(address, [key_ptr, data_ptr, count])
            actual = bytes(emulator.mem_read(data_ptr, count))
            state = bytes(emulator.mem_read(key_ptr, 4))
            if actual != noise.transform(data[:count], decrypt) or state != noise.key:
                raise AssertionError('Native Noise data/state differs')

    key = password_key('test12345')
    for decrypt in (False, True):
        data = bytes(range(24))
        emulator.mem_write(data_ptr, data)
        emulator.mem_write(key_ptr, key)
        success = call(0x42d910, [int(decrypt), 0, data_ptr, out_ptr,
                                len(data), key_ptr, len(key)])
        if not success or bytes(emulator.mem_read(out_ptr, len(data))) != triple_des(data, key, decrypt):
            raise AssertionError('Native 3DES differs')
    print('Native B, stateful Noise and 3DES encryption/decryption match.')
    print('This is not a Windows server login or gameplay test.')


if __name__ == '__main__':
    main()
