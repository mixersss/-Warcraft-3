"""Capture classic server 0x4637e0 stall writer; stub game data, retain native field order."""
import argparse,hashlib,json,struct,sys
from pathlib import Path
from inspect_pdb import pe_info

def main():
 p=argparse.ArgumentParser();p.add_argument('exe',type=Path);p.add_argument('--output',type=Path);a=p.parse_args();raw=a.exe.read_bytes()
 assert hashlib.sha256(raw).hexdigest()=='f60aa51c8a8d08ee097bc4a6003b5a07dd97f6dc5d6ea8ae4c8425fa3660f6c5'
 from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
 from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EAX,UC_X86_REG_ECX,UC_X86_REG_EIP
 u=Uc(UC_ARCH_X86,UC_MODE_32);base,sections,*_=pe_info(raw);u.mem_map(base,0x400000)
 for s in sections:u.mem_write(base+s['rva'],raw[s['raw']:s['raw']+s['raw_size']])
 u.mem_map(0,4096);u.mem_map(0x1000000,0x200000);u.mem_map(0x2000000,0x100000);u.mem_map(0xf00000,4096)
 def put(addr,n):u.mem_write(addr,struct.pack('<I',n))
 def arg(n):return struct.unpack('<I',u.mem_read(u.reg_read(UC_X86_REG_ESP)+4*n,4))[0]
 def ret(n=0,pop=0):
  sp=u.reg_read(UC_X86_REG_ESP);ip=arg(0);u.reg_write(UC_X86_REG_EAX,n);u.reg_write(UC_X86_REG_ESP,sp+4+pop);u.reg_write(UC_X86_REG_EIP,ip)
 result=bytearray();mode={'instance':False}
 def hook(uc,addr,size,unused):
  if addr in (0x523a40,0x524a30,0x524b30,0x524c40):
   width={0x523a40:2,0x524a30:1,0x524b30:2,0x524c40:4}[addr]
   result.extend((arg(1)&((1<<(8*width))-1)).to_bytes(width,'big'));ret(1,4)
  elif addr==0x529ce0:ret(arg(1),4)
  elif addr==0x416250:ret(456)
  elif addr==0x4d99a0:ret(0x2008000)
  elif addr==0x524e60:
   b=bytes(u.mem_read(arg(1),100)).split(b'\0')[0]+b'\0';result.extend(struct.pack('>H',len(b))+b);ret(1,4)
  elif addr==0x461ab0:ret(885,8)
  elif addr==0x418ce0:put(0x2009134,50);ret(0x2009000) # cdecl
  elif addr==0x423360:ret(0x200a000,8)
  elif addr==0x463d80:ret(1)
  elif addr==0x418110:ret(123 if mode['instance'] else 0,4)
  elif addr==0x463d60:ret(int(mode['instance']))
  elif addr==0x41dbd0:ret(u.reg_read(UC_X86_REG_ECX),4)
  elif addr==0x41dc60:ret()
  elif addr==0x201f000:ret(1,60) # virtual send, packet by value + staller
 u.hook_add(UC_HOOK_CODE,hook)
 put(0x2000000,0x2001000);put(0x2001030,0x201f000)
 u.mem_write(0x2008010,b'\x01Market\0');u.mem_write(0x2008054,struct.pack('<IBBBxH',25000,0,7,2,885))
 u.mem_write(0x200a004,struct.pack('<4H',100,100,0,0));u.mem_write(0x200a00c,b'\x00')
 for i in range(5):u.mem_write(0x200a016+i*4,struct.pack('<HH',i+1,10+i))
 fixtures={}
 for instance in (False,True):
  mode['instance']=instance;result.clear();u.mem_write(0x1100000,struct.pack('<III',0xf00000,0x2000000,0x2002000))
  u.reg_write(UC_X86_REG_ESP,0x1100000);u.reg_write(UC_X86_REG_ECX,0x2003000);u.emu_start(0x4637e0,0xf00000,count=100000)
  assert result[:2]==struct.pack('>H',854)
  fixtures['instance' if instance else 'plain']=bytes(result[2:]).hex()
 sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
 from market import read_offers
 for name,payload in fixtures.items():
  owner,offers=read_offers(bytes.fromhex(payload));assert owner==456 and offers[0][2].identity==885
  assert len(offers[0][2].instance_attributes)==(5 if name=='instance' else 0)
 if a.output:a.output.write_text(json.dumps({'server_sha256':hashlib.sha256(raw).hexdigest(),'writer':'0x4637e0','fixtures':fixtures},indent=2)+'\n')
 print('Native stall server writer captured: plain/instance fields, no modern expiration/tradable bytes.')
if __name__=='__main__':main()
