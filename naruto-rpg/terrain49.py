"""Seal only the northern outer corridor to Hokage; keep south entrance and source scenery."""
import json,struct
from pathlib import Path
def pathing(original):
 d=bytearray(original);w,h=struct.unpack_from('<II',d,8)
 assert (w,h)==(1024,1024)
 x0,y0,x1,y1=json.loads((Path(__file__).parent/'src/balance49.json').read_text())['northHokageBarrier']['bounds']
 for y in range((y0+16384)//32,(y1+16384)//32):
  for x in range((x0+16384)//32,(x1+16384)//32):d[16+y*w+x]|=2
 return bytes(d)
