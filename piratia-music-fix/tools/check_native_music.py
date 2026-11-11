"""Check codec selection in the exact SDL_mixer image from the owner's private dump.

Stubs file I/O and CRT helpers; stops on decoder entry. Does not decode or play audio.
Requires development-only Unicorn; the dump is never copied into a release.
"""
import argparse
import struct
from minidump_memory import Dump


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dump');args=p.parse_args()
    d=Dump(args.dump)
    mixer=next(m for m in d.modules if m['name']=='SDL_mixer.dll')
    if mixer['base']!=0xd70000 or mixer['stamp']!=0x41ae7f06:
        p.error('Unexpected native SDL_mixer image')
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EAX,UC_X86_REG_EIP
    for magic,expected in ((b'OggS','vorbis'),(b'\xff\xfb\x90\x00','smpeg')):
        u=Uc(UC_ARCH_X86,UC_MODE_32)
        u.mem_map(mixer['base'],mixer['size'])
        u.mem_write(mixer['base'],d.read(mixer['base'],mixer['size']))
        u.mem_map(0x1000000,0x200000);u.mem_map(0x2000000,0x200000)
        filename=0x2000000
        u.mem_write(filename,b'music/unchanged-name.mp3\0')
        imports={0xda1084:'fopen',0xda1080:'fread',0xda107c:'fclose',0xda1078:'strrchr',0xda1068:'malloc',0xda1074:'toupper'}
        stubs={0x2010000+i*0x20:name for i,name in enumerate(imports.values())}
        for i,address in enumerate(imports):u.mem_write(address,struct.pack('<I',0x2010000+i*0x20))
        route=[]
        def arg(i):return struct.unpack('<I',u.mem_read(u.reg_read(UC_X86_REG_ESP)+4*i,4))[0]
        def ret(value):
            sp=u.reg_read(UC_X86_REG_ESP);back=arg(0)
            u.reg_write(UC_X86_REG_ESP,sp+4);u.reg_write(UC_X86_REG_EAX,value);u.reg_write(UC_X86_REG_EIP,back)
        def hook(uc,address,size,unused):
            if address in (0xd75630,0xd76322):
                route.append('vorbis' if address==0xd75630 else 'smpeg');u.emu_stop();return
            name=stubs.get(address)
            if name=='fopen':ret(0x2001000)
            elif name=='fread':u.mem_write(arg(1),magic);ret(1)
            elif name=='fclose':ret(0)
            elif name=='strrchr':ret(filename+len(b'music/unchanged-name'))
            elif name=='malloc':ret(0x2005000)
            elif name=='toupper':ret(ord(chr(arg(1)&255).upper()))
        u.hook_add(UC_HOOK_CODE,hook)
        u.mem_write(0x1100000,struct.pack('<II',0x2100000,filename))
        u.reg_write(UC_X86_REG_ESP,0x1100000)
        u.emu_start(0xd74900,0x2100000,count=100000)
        if route!=[expected]:raise AssertionError(f'Native music routing mismatch: {route}')
        print('Unchanged .mp3 filename,',magic.hex(),'header ->',expected)
    print('Native codec selection confirmed; real Windows playback remains untested.')


if __name__=='__main__':main()
