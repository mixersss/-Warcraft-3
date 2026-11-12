"""Add checked search locations inside real owner spawn rectangles; never change spawn counts."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from navigation import Navigation

def main():
 p=argparse.ArgumentParser();p.add_argument('resource',type=Path);resource=p.parse_args().resource
 data=json.loads((ROOT/'assets/regions.json').read_text())
 for city,region in data.items():
  nav=Navigation(ROOT/'assets'/region['navigation']);added=0
  for line in (resource/city/(city+'ChaSpn.txt')).read_text(encoding='gb18030').splitlines():
   a=line.split('\t')
   if len(a)<8 or not a[0].isdigit():continue
   lo=tuple(map(int,a[1].split(',')));hi=tuple(map(int,a[2].split(',')))
   if hi[0]<=lo[0] or hi[1]<=lo[1]:continue
   for model in a[4].split(','):
    record=region['farms'].get(str(int(model))) if model.isdigit() else None
    if not record:continue
    cap=64 if record['level']<=5 else 16
    if len(record['points'])>=cap:continue
    anchor=tuple(record['points'][0])
    for fx,fy in tuple((x,y) for x in (.15,.38,.62,.85) for y in (.15,.38,.62,.85)):
     goal=nav.nearest((int(lo[0]+(hi[0]-lo[0])*fx),int(lo[1]+(hi[1]-lo[1])*fy)),4)
     if goal and all(__import__('math').dist(goal,old)>500 for old in record['points']) and nav.path(anchor,goal):
      record['points'].append(list(goal));added+=1
     if len(record['points'])>=cap:break
  print(city,'added',added,'numeric farm destinations',flush=True)
 (ROOT/'assets/regions.json').write_text(json.dumps(data,separators=(',',':'),ensure_ascii=False)+'\n')
if __name__=='__main__':main()
