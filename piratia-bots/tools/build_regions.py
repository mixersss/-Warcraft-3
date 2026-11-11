"""Derive three numeric navigation crops and beginner mob catalogs from owner resources."""
import argparse
import base64
import json
import struct
import sys
import zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from navigation import Navigation

REGIONS={
 'garner':{'origin':[1850,2400],'width':650,'height':550,'birthplace':'Argent City','label':'Аргент',
           'spawns':[(223200,278700),(219400,277900),(224500,270300)]},
 'magicsea':{'origin':[600,3200],'width':950,'height':600,'birthplace':'Shaitan City','label':'Шайтан',
             'spawns':[(89100,357500),(81900,365400),(84500,350200)]},
 'darkblue':{'origin':[1000,200],'width':750,'height':650,'birthplace':'Icicle Castle','label':'Ледяной город',
             'spawns':[(131600,53600),(134200,48100),(130500,50300)]},
}


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('resource',type=Path);args=p.parse_args()
 actors={}
 for line in (args.resource/'CharacterInfo.txt').read_bytes().decode('gb18030',errors='replace').splitlines():
  a=line.split('\t')
  if a[0].isdigit() and len(a)>70 and a[4]=='5':
   level,hp=int(a[60]),int(a[61])
   if 1<=level<=15 and 0<hp<2000 and int(a[0])<500:
    actors[int(a[0])]={'level':level,'hp':hp,'drops':[int(n) for n in (a[46]+','+a[51]).split(',') if n.isdigit() and int(n)]}
 result={}
 for name,info in REGIONS.items():
  raw=(args.resource/name/(name+'.blk')).read_bytes();w,h=struct.unpack_from('<II',raw)
  if (w,h)!=(8192,8192):raise ValueError('Unknown block format')
  ox,oy=info['origin'];width,height=info['width'],info['height']
  def blocked(x,y):return bool(raw[8+y*(w//8)+x//8]&(1<<(7-x%8)))
  cells=bytearray(int(not any(blocked(x*2+1+dx,y*2+1+dy) for dx in (-1,0,1) for dy in (-1,0,1)))
                  for y in range(oy,oy+height) for x in range(ox,ox+width))
  data={'map':name,'origin':[ox,oy],'width':width,'height':height,'cell_cm':100,
        'source':'numeric crop of supplied .blk; 3x3 clearance; no map/model assets',
        'walkable_zlib':base64.b64encode(zlib.compress(cells,9)).decode(),'waypoints':[]}
  nav_path=ROOT/'assets'/(name+'-navigation.json');nav_path.write_text(json.dumps(data,separators=(',',':'))+'\n')
  nav=Navigation(nav_path)
  spawn=nav.nearest(info['spawns'][0],12)
  if not spawn:raise ValueError('Spawn not clear: '+name)
  farm={}
  for line in (args.resource/name/(name+'ChaSpn.txt')).read_bytes().decode('gb18030',errors='replace').splitlines():
   a=line.split('\t')
   if len(a)<8 or not a[0].isdigit():continue
   lo=tuple(map(int,a[1].split(',')));hi=tuple(map(int,a[2].split(',')))
   if hi[0]<lo[0] or hi[1]<lo[1]:continue
   models=[int(i) for i in a[4].split(',') if i.isdigit() and int(i) in actors]
   if not models:continue
   x1,x2=max(lo[0],ox*100),min(hi[0],(ox+width)*100)
   y1,y2=max(lo[1],oy*100),min(hi[1],(oy+height)*100)
   if x1>=x2 or y1>=y2:continue
   # Four sampled points inside the real spawn rectangle, closest to home first.
   points=[(int(x1+(x2-x1)*x),int(y1+(y2-y1)*y)) for x,y in ((.5,.5),(.25,.25),(.75,.75),(.25,.75))]
   points.sort(key=lambda pt:(pt[0]-spawn[0])**2+(pt[1]-spawn[1])**2)
   goal=None
   for pt in points:
    candidate=nav.nearest(pt,12)
    if candidate and nav.path(spawn,candidate):goal=candidate;break
   if not goal:continue
   for model in models:
    record=farm.setdefault(str(model),dict(actors[model],points=[]))
    if goal not in record['points'] and len(record['points'])<3:record['points'].append(goal)
  # Limit point sets by proximity, retaining low-level and profession-required species.
  for record in farm.values():record['points'].sort(key=lambda pt:(pt[0]-spawn[0])**2+(pt[1]-spawn[1])**2)
  beginner=[p for r in farm.values() if r['level']<=3 for p in r['points']]
  beginner.sort(key=lambda pt:(pt[0]-spawn[0])**2+(pt[1]-spawn[1])**2)
  data['waypoints']=beginner[:6]
  if not data['waypoints']:raise ValueError('No reachable beginner farm: '+name)
  nav_path.write_text(json.dumps(data,separators=(',',':'))+'\n')
  result[name]={k:v for k,v in info.items() if k not in ('origin','width','height')}
  result[name]['farms']=farm
  result[name]['navigation']=nav_path.name
  print(name,'species',len(farm),'levels',sorted(set(r['level'] for r in farm.values())),flush=True)
 (ROOT/'assets/regions.json').write_text(json.dumps(result,separators=(',',':'),ensure_ascii=False)+'\n')


if __name__=='__main__':main()
