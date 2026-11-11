"""Capture the supplied classic client's BeginPlay serialization calls.

Uses optional Unicorn, stubs SDK packet allocation/writers and network submission.
Checks the native choice of writer and its argument; not a live server test.
"""
import argparse
import hashlib
import struct
from pathlib import Path

from inspect_pdb import pe_info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exe', type=Path)
    raw = parser.parse_args().exe.read_bytes()
    if hashlib.sha256(raw).hexdigest() != 'c819f09bacb1f058f6040a5fe3bdab7d6264ade44c89cd93123b54c471653dd8':
        parser.error('Executable is not the audited classic client')
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EIP

    base, sections, *_ = pe_info(raw)
    emulator = Uc(UC_ARCH_X86, UC_MODE_32)
    emulator.mem_map(base, 0x400000)
    for section in sections:
        emulator.mem_write(base + section['rva'], raw[section['raw']:section['raw'] + section['raw_size']])
    emulator.mem_map(0, 0x1000)  # SEH head, no OS handlers run.
    emulator.mem_map(0x1000000, 0x200000)
    emulator.mem_map(0x2000000, 0x100000)
    emulator.mem_map(0xf00000, 0x1000)

    def put(address, value):
        emulator.mem_write(address, struct.pack('<I', value))

    def stack_arg(index):
        stack = emulator.reg_read(UC_X86_REG_ESP)
        return struct.unpack('<I', emulator.mem_read(stack + 4 * index, 4))[0]

    def return_stub(argument_bytes, value=0):
        stack = emulator.reg_read(UC_X86_REG_ESP)
        address = struct.unpack('<I', emulator.mem_read(stack, 4))[0]
        emulator.reg_write(UC_X86_REG_ESP, stack + 4 + argument_bytes)
        emulator.reg_write(UC_X86_REG_EAX, value)
        emulator.reg_write(UC_X86_REG_EIP, address)

    writes, submitted = [], []

    def hook(uc, address, size, unused):
        if address == 0x5516c0:  # GetWPacket by-value output pointer.
            return_stub(4, stack_arg(1))
        elif address == 0x54eb40:  # WriteCmd(u16).
            writes.append(('command', stack_arg(1)))
            return_stub(4, 1)
        elif address == 0x54f330:  # WriteString(char const*).
            pointer = stack_arg(1)
            value = bytes(emulator.mem_read(pointer, 32)).split(b'\0')[0]
            writes.append(('string', value))
            return_stub(4, 1)
        elif address == 0x5194c0:  # SendPacketMessage.
            submitted.append(True)
            return_stub(4)
        elif address == 0x500560:  # Temporary WPacket destructor.
            return_stub(0)

    emulator.hook_add(UC_HOOK_CODE, hook)
    put(0x2000004, 0x2001000)
    emulator.mem_write(0x2002000, b'Bot12345678\0')
    put(0x1100000, 0xf00000)
    put(0x1100004, 0x2002000)
    emulator.reg_write(UC_X86_REG_ESP, 0x1100000)
    emulator.reg_write(UC_X86_REG_ECX, 0x2000000)
    emulator.emu_start(0x51a4d0, 0xf00000, count=100000)
    if writes != [('command', 433), ('string', b'Bot12345678')] or submitted != [True]:
        raise AssertionError(f'Unexpected native BeginPlay writes: {writes}')
    print('Native classic BeginPlay writes command 433 and character-name string.')
    # The UI hashes the PIN at 0x46390e with md5string (0x577680).
    # Verify the actual format constant, then capture CS_CreatePassword2.
    if bytes(emulator.mem_read(0x614ac8, 5)).split(b'\0')[0] != b'%02X':
        raise AssertionError('Unexpected native MD5 hex case format')
    writes.clear()
    submitted.clear()
    digest = b'25F9E794323B453885F5181F1B624D0B'
    emulator.mem_write(0x2002000, digest + b'\0')
    put(0x6c2508, 0x2001000)
    put(0x1100000, 0xf00000)
    put(0x1100004, 0x2002000)
    emulator.reg_write(UC_X86_REG_ESP, 0x1100000)
    emulator.emu_start(0x507e40, 0xf00000, count=100000)
    if writes != [('command', 346), ('string', digest)] or submitted != [True]:
        raise AssertionError('Unexpected native secondary-password request')
    print('Native secondary-password creation writes command 346 and uppercase MD5 string.')
    print('This capture checks the EXE serialization calls, not live map entry.')


if __name__ == '__main__':
    main()
