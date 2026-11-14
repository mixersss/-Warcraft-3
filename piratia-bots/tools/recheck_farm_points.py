"""Recheck numeric farm goals against new ground geometry and original spawn bounds.

Build-time numpy/scipy only; no server spawn edits or teleport assumptions.
"""
import argparse
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from navigation import Navigation


def recheck(resource):
    import numpy as np
    from scipy.ndimage import label
    path=ROOT/'assets/regions.json';regions=json.loads(path.read_text());audit={}
    for name,region in regions.items():
        nav=Navigation(ROOT/'assets'/region['navigation'])
        grid=np.frombuffer(nav.cells,dtype=np.uint8).reshape(nav.height,nav.width)
        labels,_=label(grid)
        home=nav.nearest(region['spawns'][0],12)
        if not home:raise ValueError('Home has no ground: '+name)
        cx,cy=nav.cell(home);component=labels[cy,cx]
        rectangles={}
        for line in (resource/name/(name+'ChaSpn.txt')).read_bytes().decode('gb18030',errors='replace').splitlines():
            a=line.split('\t')
            if len(a)<8 or not a[0].isdigit():continue
            lo=list(map(int,a[1].split(',')));hi=list(map(int,a[2].split(',')))
            if len(lo)!=2 or len(hi)!=2 or any(b<=v for v,b in zip(lo,hi)):continue
            for model in a[4].split(','):
                if model.isdigit():rectangles.setdefault(str(int(model)),[]).append((lo,hi))
        before=sum(len(v['points']) for v in region['farms'].values());changed=0;empty=[]
        for model,record in region['farms'].items():
            bounds=rectangles.get(model,[]);points=[]
            def allowed(p):
                x,y=nav.cell(p)
                return nav.free((x,y)) and nav.combat_allowed(p) and labels[y,x]==component and any(lo[0]<=p[0]<hi[0] and lo[1]<=p[1]<hi[1] for lo,hi in bounds)
            for old in record['points']:
                if allowed(old):p=old
                else:
                    changed+=1;p=None;x,y=nav.cell(old)
                    candidates=((x+dx,y+dy) for dx in range(-12,13) for dy in range(-12,13))
                    for cell in sorted(candidates,key=lambda c:(c[0]-x)**2+(c[1]-y)**2):
                        candidate=list(nav.position(cell))
                        if allowed(candidate):p=candidate;break
                if p and p not in points:points.append(p)
            if not points:
                # A species can retain a goal only inside a genuine reachable spawn area.
                for lo,hi in bounds:
                    for fx,fy in ((.5,.5),(.15,.15),(.85,.85),(.15,.85),(.85,.15)):
                        p=nav.nearest((int(lo[0]+(hi[0]-lo[0])*fx),int(lo[1]+(hi[1]-lo[1])*fy)),6)
                        if p and allowed(p):points.append(list(p));break
                    if points:break
            record['points']=points
            if not points:empty.append(int(model))
        audit[name]={'old_points':before,'rechecked_or_removed_points':changed,
                     'ground_reachable_points':sum(len(v['points']) for v in region['farms'].values()),
                     'species_without_reachable_ground_spawn':empty}
        print(name,audit[name],flush=True)
    path.write_text(json.dumps(regions,ensure_ascii=False,separators=(',',':'))+'\n')
    return audit


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('resource',type=Path)
    args=p.parse_args();audit=recheck(args.resource)
    output=ROOT/'assets/world-navigation.json';data=json.loads(output.read_text());data['farm_recheck']=audit
    output.write_text(json.dumps(data,indent=2)+'\n')
