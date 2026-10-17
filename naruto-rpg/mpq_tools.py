"""Native StormLib reads; library retained with the cloud toolchain."""
import ctypes as c
from pathlib import Path
TOOLCHAIN=Path('/workspace/.warcraft-tools')
S=c.CDLL(str(TOOLCHAIN/'libstorm.so'))
S.SFileOpenArchive.argtypes=[c.c_char_p,c.c_uint32,c.c_uint32,c.POINTER(c.c_void_p)];S.SFileOpenArchive.restype=c.c_bool
S.SFileOpenFileEx.argtypes=[c.c_void_p,c.c_char_p,c.c_uint32,c.POINTER(c.c_void_p)];S.SFileOpenFileEx.restype=c.c_bool
S.SFileGetFileSize.argtypes=[c.c_void_p,c.POINTER(c.c_uint32)];S.SFileGetFileSize.restype=c.c_uint32
S.SFileReadFile.argtypes=[c.c_void_p,c.c_void_p,c.c_uint32,c.POINTER(c.c_uint32),c.c_void_p];S.SFileReadFile.restype=c.c_bool
S.SFileCloseFile.argtypes=[c.c_void_p];S.SFileCloseArchive.argtypes=[c.c_void_p]
class StormArchive:
 def __init__(self,path):
  self.handle=c.c_void_p();assert S.SFileOpenArchive(str(path).encode(),0,0x100,c.byref(self.handle)),path
 def read(self,name):
  h=c.c_void_p();assert S.SFileOpenFileEx(self.handle,name.encode(),0,c.byref(h)),name
  size=S.SFileGetFileSize(h,None);data=c.create_string_buffer(size);got=c.c_uint32()
  try:assert S.SFileReadFile(h,data,size,c.byref(got),None) and got.value==size,name
  finally:S.SFileCloseFile(h)
  return data.raw
 def close(self):S.SFileCloseArchive(self.handle)
