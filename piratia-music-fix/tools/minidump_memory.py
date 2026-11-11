"""Read minidump metadata/memory locally; never uploads dump contents."""
import mmap,struct,bisect
from pathlib import Path
class Dump:
 def __init__(self,path):
  self.file=open(path,'rb');self.b=mmap.mmap(self.file.fileno(),0,access=mmap.ACCESS_READ)
  n,offset=self.unpack('<II',8);self.streams={}
  for i in range(n):
   kind,size,rva=self.unpack('<III',offset+12*i)
   if kind:self.streams[kind]=(rva,size)
  rva,_=self.streams[9];count,offset=self.unpack('<QQ',rva);self.blocks=[]
  for i in range(count):
   start,size=self.unpack('<QQ',rva+16+i*16);self.blocks.append((start,start+size,offset));offset+=size
  self.blocks.sort();self.starts=[b[0] for b in self.blocks]
  rva,_=self.streams[3];self.threads=[]
  for i in range(self.unpack('<I',rva)[0]):
   t=self.unpack('<IIIIQQIIII',rva+4+i*48)
   self.threads.append(dict(zip(('id','suspend','priority_class','priority','teb','stack','stack_size','stack_rva','context_size','context_rva'),t)))
  rva,_=self.streams[4];self.modules=[]
  for i in range(self.unpack('<I',rva)[0]):
   q=rva+4+i*108;base,size,check,stamp,name=self.unpack('<QIIII',q)
   ln=self.unpack('<I',name)[0];name=self.b[name+4:name+4+ln].decode('utf-16le').replace('\\','/').split('/')[-1]
   self.modules.append({'base':base,'size':size,'stamp':stamp,'name':name})
 def unpack(self,fmt,offset):return struct.unpack_from(fmt,self.b,offset)
 def read(self,address,size):
  out=bytearray()
  while size:
   i=bisect.bisect_right(self.starts,address)-1
   if i<0 or not self.blocks[i][0]<=address<self.blocks[i][1]:raise ValueError(f'Unmapped {address:x}')
   start,end,offset=self.blocks[i];amount=min(size,end-address);out+=self.b[offset+address-start:offset+address-start+amount];size-=amount;address+=amount
  return bytes(out)
 def u32(self,address):return struct.unpack('<I',self.read(address,4))[0]
 def u64(self,address):return struct.unpack('<Q',self.read(address,8))[0]
 def module(self,address):
  for m in self.modules:
   if m['base']<=address<m['base']+m['size']:return m
 def where(self,address):
  m=self.module(address);return f"{m['name']}+0x{address-m['base']:x}" if m else f'0x{address:x}'
