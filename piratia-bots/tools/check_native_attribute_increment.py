"""Execute owner's native Cmd_ReassignAttr until stat writes; compare increment vs total."""
import argparse,hashlib,struct
from inspect_pdb import pe_info
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('exe',type=Path);raw=p.parse_args().exe.read_bytes()
 assert hashlib.sha256(raw).hexdigest()=='f60aa51c8a8d08ee097bc4a6003b5a07dd97f6dc5d6ea8ae4c8425fa3660f6c5'
 from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
 from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EAX,UC_X86_REG_ECX,UC_X86_REG_EIP
 u=Uc(UC_ARCH_X86,UC_MODE_32);base,sections,*_=pe_info(raw);u.mem_map(base,0x400000)
 for s in sections:u.mem_write(base+s['rva'],raw[s['raw']:s['raw']+s['raw_size']])
 u.mem_map(0,4096);u.mem_map(0x1000000,0x200000);u.mem_map(0x2000000,0x100000);u.mem_map(0xf00000,4096)
 state={}
 def arg(i):return struct.unpack('<I',u.mem_read(u.reg_read(UC_X86_REG_ESP)+i*4,4))[0]
 def ret(value=0,pop=0):
  sp=u.reg_read(UC_X86_REG_ESP);ip=arg(0);u.reg_write(UC_X86_REG_EAX,value);u.reg_write(UC_X86_REG_ESP,sp+4+pop);u.reg_write(UC_X86_REG_EIP,ip)
 def hook(uc,a,size,unused):
  if a in (0x4e046d,0x4e04ef):u.emu_stop()
  elif a==0x42fcc0:ret()
  elif a==0x4d9080:ret(0,4)
  elif a==0x523bb0:ret(1)
  elif a==0x4e0510:ret(1000,4)
  elif a==0x4013c0:ret(state['attrs'].get(arg(1),5),4)
  elif a==0x523c00:
   state['shorts']+=1;ret(25 if state['shorts']==1 else 0)
  elif a==0x523c80:ret(state['increment'])
  elif a==0x5035e0:
   state['attrs'][arg(1)]=arg(2);state['writes']+=1;ret(1,12)
 u.hook_add(UC_HOOK_CODE,hook)
 for increment in (1,6):
  state.update(attrs={6:4,50:5},shorts=0,writes=0,increment=increment)
  u.mem_write(0x1100000,struct.pack('<II',0xf00000,0x2001000))
  u.reg_write(UC_X86_REG_ESP,0x1100000);u.reg_write(UC_X86_REG_ECX,0x2000000)
  u.emu_start(0x4e01a0,0xf00000,count=100000)
  expected={6:3,50:6} if increment==1 else {6:4,50:5}
  assert state['attrs']==expected,(increment,state)
 print('Native server confirms: increment1 spends one AP and adds one STR; total6 with four AP is refused.')
if __name__=='__main__':main()
