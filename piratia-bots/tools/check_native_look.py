"""Developer-only capture of the classic client's default character LOOK.

Requires Unicorn. Runs native initialization/copies; stubs UI-only validation,
text formatting and final network submission. Not a live creation test.
Usage: python tools/check_native_look.py /path/to/Game.exe
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
    emulator.mem_map(0x1000000, 0x200000)
    emulator.mem_map(0x2000000, 0x100000)
    emulator.mem_map(0xf00000, 0x1000)

    def put(address, value):
        emulator.mem_write(address, struct.pack('<I', value))

    def return_from_stub(value=0):
        stack = emulator.reg_read(UC_X86_REG_ESP)
        address = struct.unpack('<I', emulator.mem_read(stack, 4))[0]
        emulator.reg_write(UC_X86_REG_ESP, stack + 4)
        emulator.reg_write(UC_X86_REG_EAX, value)
        emulator.reg_write(UC_X86_REG_EIP, address)

    scene, model, edit = 0x2000000, 0x2001000, 0x2002000
    put(scene + 0x2ac, 0)
    put(scene + 0x2dc, model)
    # Read the actual character creator selection tables from the mapped EXE.
    # CharacterInfo model part IDs are not valid creation appearance IDs.
    hairs = struct.unpack('<4I', emulator.mem_read(0x655848, 16))
    faces = struct.unpack('<4I', emulator.mem_read(0x655868, 16))
    if hairs != (2000, 2062, 2124, 2291) or faces != (2554, 2554, 2554, 2554):
        raise AssertionError('Unexpected native character creator selection tables')
    for offset, value in ((0x10, 1), (0x334, hairs[0]), (0x338, faces[0])):
        emulator.mem_write(model + offset, struct.pack('<H', value))
    put(0x670270, edit)
    put(0x6702e0, 0)
    put(0x670304, 0x2003000)
    emulator.mem_write(edit + 0xc0, b'Bot12345678\0')
    emulator.mem_write(0x2003000, b'Argent City\0')
    capture = []

    def hook(uc, address, size, unused):
        if address == 0x46d6a0:  # LOOK constructor, zeroed again by native caller.
            return_from_stub(emulator.reg_read(UC_X86_REG_ECX))
        elif address == 0x597090:  # LookData2String validation/UI formatting only.
            return_from_stub(1)
        elif address == 0x507cb0:  # CS_NewCha: capture third argument before network.
            stack = emulator.reg_read(UC_X86_REG_ESP)
            pointer = struct.unpack('<I', emulator.mem_read(stack + 12, 4))[0]
            capture.append(bytes(emulator.mem_read(pointer, 1626)))
            return_from_stub()
        elif address == 0x40c690:  # UI waiting indicator.
            return_from_stub()

    emulator.hook_add(UC_HOOK_CODE, hook)
    emulator.reg_write(UC_X86_REG_ECX, scene)
    put(0x1100000, 0xf00000)
    emulator.reg_write(UC_X86_REG_ESP, 0x1100000)
    emulator.emu_start(0x4c16c0, 0xf00000, count=1000000)
    expected = bytearray(1626)
    for index, value in ((2, 1), (166, 250), (167, 9), (326, 1), (1624, 208), (1625, 7)):
        expected[index] = value
    if capture != [bytes(expected)]:
        raise AssertionError('Native creation LOOK differs from the captured golden layout')
    print('Native classic UI creation LOOK matches the 1626-byte golden payload.')
    print(f'Appearance read from native creator tables: hair={hairs[0]}, face={faces[0]}.')
    print('Windows game server acceptance is not tested by this capture.')


if __name__ == '__main__':
    main()
