"""Explicit invasion NPC bounty; checked-in Classic defaults, no external build dependency."""
import json
from pathlib import Path
ROOT=Path(__file__).parent
STOCK=json.loads((ROOT/'src/classic-bounty44.json').read_text())['units']
def profiles(entries):
 out=dict(STOCK)
 for base,raw,mods in entries:
  assert base in STOCK,('Unknown bounty stock base',base,raw)
  fields={k:v for k,_,v in mods}
  out[raw]=[int(fields.get(k,STOCK[base][n]))for n,k in enumerate(['ubba','ubdi','ubsi'])]
 return out
def generated(entries):
 # Stock summons may be produced by native NPC abilities, so cover stock as well.
 data=sorted((raw,values)for raw,values in profiles(entries).items()if any(values))
 out=[];names=[]
 for start in range(0,len(data),20):
  name='Invasion44Data'+str(start//20);names.append(name)
  out.append('function '+name+' takes nothing returns nothing')
  for raw,values in data[start:start+20]:
   for col,v in enumerate(values):out.append(f"    call SaveInteger(Invasion44Bounty,'{raw}',{col},{v})")
  out.append('endfunction')
 out+=['function Invasion44Load takes nothing returns nothing']
 for name in names:out.append(f'    call ExecuteFunc("{name}")')
 return '\n'.join(out+['endfunction'])
