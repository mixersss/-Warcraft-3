"""Synthetic fixtures from the supplied GameServer's native world writers.

Unicorn development tool. Getters provide synthetic actors; native WriteBaseInfo,
WriteLookData, append-look, skillbag, state and event writers run. Packet writers
capture bytes. Inventory/skill getters supply synthetic data; no live session runs.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from inspect_pdb import pe_info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exe', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    raw = args.exe.read_bytes()
    if hashlib.sha256(raw).hexdigest() != 'f60aa51c8a8d08ee097bc4a6003b5a07dd97f6dc5d6ea8ae4c8425fa3660f6c5':
        parser.error('Unexpected GameServer executable')
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EIP
    base, sections, *_ = pe_info(raw)
    u = Uc(UC_ARCH_X86, UC_MODE_32)
    u.mem_map(base, 0x400000)
    for s in sections:
        u.mem_write(base+s['rva'], raw[s['raw']:s['raw']+s['raw_size']])
    u.mem_map(0x1000000, 0x200000)
    u.mem_map(0x2000000, 0x100000)
    u.mem_map(0xf00000, 0x1000)
    actor, pos, radius, event, empty = 0x2000000, 0x2010000, 0x2011000, 0x2012000, 0x2013000
    state = {}
    result = bytearray()

    def put(address, value):
        u.mem_write(address, struct.pack('<I', value))

    def arg(index):
        return struct.unpack('<I', u.mem_read(u.reg_read(UC_X86_REG_ESP)+4*index, 4))[0]

    def ret(value=0, pop=0):
        sp = u.reg_read(UC_X86_REG_ESP)
        address = arg(0)
        u.reg_write(UC_X86_REG_ESP, sp+4+pop)
        u.reg_write(UC_X86_REG_EAX, value)
        u.reg_write(UC_X86_REG_EIP, address)

    def hook(uc, address, size, unused):
        if address in (0x524a30,0x524b30,0x524c40):
            width = {0x524a30:1,0x524b30:2,0x524c40:4}[address]
            result.extend((arg(1) & ((1 << (width*8))-1)).to_bytes(width,'big'))
            ret(1,4)
        elif address == 0x524e60:
            value = bytes(u.mem_read(arg(1),100)).split(b'\0')[0]+b'\0'
            result.extend(struct.pack('>H',len(value))+value)
            ret(1,4)
        elif address == 0x4013c0:
            ret(state['attrs'].get(arg(1),0),4)
        elif address == 0x4d8db0:  # CKitbag::IsSingleChange
            ret(1 if state.get('bag') and (arg(1)&65535) in state['bag_changed'] else 0,8)
        elif address == 0x423360:  # CKitbag::GetGridContByID
            ret((0x201a000+(arg(1)&65535)*256 if state.get('bag') and (arg(1)&65535) in state['bag_items'] else
                 0x2016000 if state.get('append') and (arg(1)&65535)==0 else 0),8)
        elif address == 0x417070:
            ret(6)
        elif address == 0x418ce0:
            kind=43 if (arg(1)&65535)==3988 else 22
            put(0x2019134,kind)
            ret(0x2019000)
        elif address == 0x4ee6c0:
            ret(0,4)
        elif address == 0x4c5550:  # ItemIsAppendLook, synthetic known append item
            ret(1,4)
        elif address == 0x4e5a60:  # changed skill count
            ret(0 if state.get("empty_skills") else 2)
        elif address == 0x4e5a80:  # skill grid getter
            ret(0x2017000+arg(1)*16,4)
        elif address == 0x4dd070:  # temporary skill-table data getter
            ret(0x2018000+(0 if (arg(1) & 65535)==25 else 64),8)
        elif address in getters:
            ret(getters[address]())

    getters = {0x415630:lambda:0, 0x42bcc0:lambda:state['model'],
               0x416250:lambda:state['id'],0x416270:lambda:state['handle'],
               0x4c3b80:lambda:actor,0x4e5710:lambda:0,
               0x4d7bf0:lambda:0,0x4d79d0:lambda:empty,0x4d7b30:lambda:empty,
               0x4d7af0:lambda:empty,0x445460:lambda:1,0x416bb0:lambda:pos,
               0x4bd3e0:lambda:radius,0x4160e0:lambda:0,0x41b250:lambda:0,
               0x4c49b0:lambda:event,0x417d60:lambda:0,0x201f000:lambda:1,
               0x5040e0:lambda:0,0x4c3b40:lambda:actor,
               0x4b8250:lambda:0,0x4b94b0:lambda:0,0x4b96b0:lambda:0}
    u.hook_add(UC_HOOK_CODE,hook)
    put(actor,0x201e000)
    put(0x201e018,0x201f000)
    put(radius,40)
    u.mem_write(0x2016000,struct.pack('<H',777))
    u.mem_write(0x20160a0,b'\x01')
    for index,skill in enumerate((25,28)):
        u.mem_write(0x2017000+index*16,struct.pack('<BBH',1,1,skill))
        u.mem_write(0x2018000+index*64+0x18,struct.pack('<I',1000))
        u.mem_write(0x2018000+index*64+0x1c,struct.pack('<4H',index,150,1,0))

    def call(address, arguments):
        u.mem_write(0x1100000,struct.pack('<'+'I'*(len(arguments)+1),0xf00000,*arguments))
        u.reg_write(UC_X86_REG_ESP,0x1100000)
        u.reg_write(UC_X86_REG_ECX,actor)
        u.emu_start(address,0xf00000,count=1000000)

    fixtures = {}
    for label, model, identity, control, x, y in (
            ('own',1,123,1,223200,278700),('monster',75,456,5,223600,278900),
            ('own_worn',1,123,1,223200,278700),('own_append',1,123,1,223200,278700),
            ('own_sword_update',1,123,1,223200,278700)):
        state.update(model=model,id=identity,handle=identity+1000,
                     attrs={0:1,1:100,10:control,31:100,43:150,44:480},append=label=='own_append')
        state['empty_skills']=label=='own_sword_update'
        u.mem_write(actor+0x4974,struct.pack('<H',28 if label=='own_sword_update' else 25))
        u.mem_write(actor+0x1e4,b'SyntheticActor\0')
        u.mem_write(actor+0x6e32,struct.pack('<H',model))
        u.mem_write(actor+0x7488,struct.pack('<H',2000))
        u.mem_write(actor+0x6e34,bytes(1620))
        if label == 'own_worn':
            u.mem_write(actor+0x6e34,struct.pack('<HH',123,1))
            u.mem_write(actor+0x6e34+0xa0,b'\x01')
            u.mem_write(actor+0x6e34+0x9e,b'\x01')
        u.mem_write(pos,struct.pack('<ii',x,y))
        result.clear()
        call(0x4e54b0,[0x2014000])
        fixtures[label+'_base'] = bytes(result).hex()
        result.clear()
        call(0x4e6070,[actor+0x4d20,0x2014000,1])
        fixtures[label+'_append'] = bytes(result).hex()
        result.clear()
        call(0x4e5790,[0x2014000,1 if label=="own_sword_update" else 0])
        fixtures[label+'_skills'] = bytes(result).hex()
        result.clear()
        call(0x505e80,[0x2014000])
        fixtures[label+'_states'] = bytes(result).hex()
        result.clear()
        call(0x506090,[0x2014000,0,44,0])
        fixtures[label+'_attrs'] = bytes(result).hex()
    state['append']=False
    state['bag']=True
    state['bag_changed']={0,1,2,3}
    state['bag_items']={0:289,1:1847,3:3988}
    for slot,identity in state['bag_items'].items():
        ptr=0x201a000+slot*256
        u.mem_write(ptr,bytes(200))
        u.mem_write(ptr,struct.pack('<6H',identity,1,100,100,50,50))
        u.mem_write(ptr+0xa0,b'\x01')
        if slot==0:
            u.mem_write(ptr+0x9e,b'\x01')
            u.mem_write(ptr+0x16,struct.pack('<10H',25,1,26,2,27,3,28,4,29,5))
    result.clear()
    call(0x4e5b00,[actor+0x4d20,0x2014000,0])
    fixtures['bag_init']=bytes(result).hex()
    state['bag_changed']={0,5}
    state['bag_items']={5:1}
    u.mem_write(0x201a000+5*256,bytes(200))
    u.mem_write(0x201a000+5*256,struct.pack('<6H',1,1,100,100,50,50))
    u.mem_write(0x201a000+5*256+0xa0,b'\x01')
    result.clear()
    call(0x4e5b00,[actor+0x4d20,0x2014000,1])
    fixtures['bag_delta']=bytes(result).hex()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(fixtures,indent=2)+'\n')
    print('Captured synthetic native base/attribute writer fixtures; no live game test.')


if __name__ == '__main__':
    main()
