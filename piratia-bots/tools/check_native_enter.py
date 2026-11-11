"""Capture the supplied classic client's BeginPlay serialization calls.

Uses optional Unicorn, stubs SDK packet allocation/writers and network submission.
Checks the native choice of writer and its argument; not a live server test.
"""
import argparse
import hashlib
import struct
import sys
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
        elif address == 0x54efe0:
            writes.append(('long', stack_arg(1)))
            return_stub(4, 1)
        elif address == 0x54ebe0:
            writes.append(('char', stack_arg(1) & 255))
            return_stub(4, 1)
        elif address == 0x54ee40:
            writes.append(('short', stack_arg(1) & 65535))
            return_stub(4, 1)
        elif address == 0x56ce90:  # Localized log format, not packet content.
            return_stub(4, 0x2007000)
        elif address == 0x5b7470:  # Stack-cookie check, no packet effects.
            return_stub(4)
        elif address == 0x54f180:
            writes.append(('sequence', bytes(emulator.mem_read(stack_arg(1), stack_arg(2) & 65535))))
            return_stub(8, 1)
        elif address == 0x571270:  # variadic logging; caller removes its arguments
            return_stub(0)
        elif address == 0x201f000:  # GetTickCount import stub
            return_stub(0, 1000)

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
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
    from hunter import movement, normal_attack
    emulator.mem_write(0x6001d0, struct.pack('<I', 0x201f000))
    put(0x2003014, 123)
    points = ((223200,278700),(223700,278900))
    for kind in (1, 2, 8):
        writes.clear()
        submitted.clear()
        put(0x200131c, kind)
        emulator.mem_write(0x2004000, bytes(0x200))
        if kind == 1:
            emulator.mem_write(0x2004004, struct.pack('<iiii', *points[0], *points[1]))
            put(0x2004104, 2)
            expected = movement(123,1,points)
        elif kind == 8:
            emulator.mem_write(0x2004000,struct.pack('<II',456,1456))
            from hunter import action_header
            expected = action_header(123,8,8)+struct.pack('>II',456,1456)
        else:
            emulator.mem_write(0x2004000, b'\x01\x02')
            put(0x2004004,25)
            put(0x2004008,456)
            put(0x200400c,1456)
            emulator.mem_write(0x2004014,struct.pack('<iiii',*points[0],*points[0]))
            put(0x2004114,2)
            expected = normal_attack(123,2,1,25,456,1456,points[0])
        emulator.mem_write(0x1100000,struct.pack('<5I',0xf00000,0x2003000,kind,0x2004000,0))
        emulator.reg_write(UC_X86_REG_ESP,0x1100000)
        emulator.reg_write(UC_X86_REG_ECX,0x2000000)
        emulator.emu_start(0x5198b0,0xf00000,count=1000000)
        encoded = bytearray()
        if not writes or writes[0] != ('command',6) or submitted != [True]:
            raise AssertionError('Native action did not send the expected command')
        for field, value in writes[1:]:
            if field == 'long': encoded.extend(struct.pack('>I',value))
            elif field == 'char': encoded.append(value)
            elif field == 'sequence': encoded.extend(struct.pack('>H',len(value))+value)
            else: raise AssertionError('Unexpected action writer')
        if bytes(encoded) != expected:
            raise AssertionError(f'Action {kind} does not match native serialization calls')
    print('Movement, normal attack and item pickup match native BeginAction serialization.')
    from social import say_request
    from progression import attribute_request
    text = 'Привет :)'
    emulator.mem_write(0x2002000, text.encode('cp1251') + b'\0')
    for address, expected in ((0x51a6f0, [('command', 1), ('sequence', text.encode('cp1251')+b'\0')]),
                              (0x51a780, [('command', 8), ('char', 1), ('short', 25), ('long', 17)])):
        writes.clear()
        submitted.clear()
        if address == 0x51a780:
            emulator.mem_write(0x2002000, bytes(0x400))
            # Native CChaAttr: changed-bit mask +0x34c, values +0x24.
            emulator.mem_write(0x200234f, b'\x02')  # changed STR=25
            put(0x2002088, 17)  # 0x24 + 25*4
        put(0x1100000, 0xf00000)
        put(0x1100004, 0x2002000)
        emulator.reg_write(UC_X86_REG_ESP, 0x1100000)
        emulator.reg_write(UC_X86_REG_ECX, 0x2000000)
        emulator.emu_start(address, 0xf00000, count=1000000)
        if writes != expected or submitted != [True]:
            raise AssertionError(f'Unexpected native speech/attribute writes: {writes}')
    assert say_request(text) == struct.pack('>H',len(text.encode('cp1251'))+1)+text.encode('cp1251')+b'\0'
    assert attribute_request(25,17) == b'\x01'+struct.pack('>HI',25,17)
    print('Local chat and base-attribute request match native classic serializers.')
    from adventure import talk_request,select_request,commit_request
    requests = [(0x508200,(456,0),talk_request(456)),
                (0x508cf0,(456,2),select_request(456,2)),
                (0x508c30,(456,6,0,0),commit_request(456,6)),
                (0x508c30,(456,7,0,0),commit_request(456,7))]
    for address,arguments,expected in requests:
        writes.clear()
        submitted.clear()
        emulator.mem_write(0x1100000,struct.pack('<'+'I'*(len(arguments)+1),0xf00000,*arguments))
        emulator.reg_write(UC_X86_REG_ESP,0x1100000)
        emulator.emu_start(address,0xf00000,count=1000000)
        if not writes or writes[0]!=('command',301) or submitted!=[True]:
            raise AssertionError('Unexpected native NPC request')
        body = b''
        for kind,value in writes[1:]:
            body += struct.pack({'char':'>B','short':'>H','long':'>I'}[kind],value)
        if body!=expected:
            raise AssertionError(f'Native NPC request mismatch at {address:x}')
    print('NPC talk, quest selection, accept and delivery match native client serializers.')
    print('This capture checks the EXE serialization calls, not live map entry.')


if __name__ == '__main__':
    main()
