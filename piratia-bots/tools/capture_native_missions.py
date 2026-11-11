"""Capture the classic server journal writer, stopping before transport submission."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from inspect_pdb import pe_info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exe',type=Path)
    parser.add_argument('output',type=Path)
    args = parser.parse_args()
    raw = args.exe.read_bytes()
    if hashlib.sha256(raw).hexdigest()!='f60aa51c8a8d08ee097bc4a6003b5a07dd97f6dc5d6ea8ae4c8425fa3660f6c5':
        parser.error('Unexpected server executable')
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EAX,UC_X86_REG_ECX,UC_X86_REG_EIP
    u=Uc(UC_ARCH_X86,UC_MODE_32)
    base,sections,*_=pe_info(raw)
    u.mem_map(base,0x400000)
    for section in sections:
        u.mem_write(base+section['rva'],raw[section['raw']:section['raw']+section['raw_size']])
    u.mem_map(0,0x1000)
    u.mem_map(0x1000000,0x200000)
    u.mem_map(0x2000000,0x100000)
    result=bytearray()
    def arg(i):
        return struct.unpack('<I',u.mem_read(u.reg_read(UC_X86_REG_ESP)+4*i,4))[0]
    def ret(pop,value=1):
        sp=u.reg_read(UC_X86_REG_ESP)
        address=arg(0)
        u.reg_write(UC_X86_REG_ESP,sp+4+pop)
        u.reg_write(UC_X86_REG_EAX,value)
        u.reg_write(UC_X86_REG_EIP,address)
    def hook(uc,address,size,unused):
        if address==0x529ce0:
            ret(4,arg(1))
        elif address in (0x523a40,0x524a30,0x524b30):
            width=1 if address==0x524a30 else 2
            result.extend((arg(1)&((1<<(width*8))-1)).to_bytes(width,'big'))
            ret(4)
    u.hook_add(UC_HOOK_CODE,hook)
    u.mem_write(0x2000502,b'\x02')
    for i,(identity,state) in enumerate(((701,0),(62,1))):
        u.mem_write(0x2000504+i*0x6c,struct.pack('<HB',identity,state))
    u.mem_write(0x1100000,struct.pack('<I',0))
    u.reg_write(UC_X86_REG_ESP,0x1100000)
    u.reg_write(UC_X86_REG_ECX,0x2000000)
    u.emu_start(0x47e3f0,0x47e4a3,count=100000)
    assert bytes(result)==struct.pack('>HBHBHB',828,2,701,0,62,1)
    args.output.write_text(json.dumps({'journal_packet':result.hex(),'source':'native MisGetMisLog 0x47e3f0; synthetic two-row journal; transport not executed'},indent=2)+'\n')
    print('Native classic journal writer captured; no live server test.')


if __name__=='__main__':main()
