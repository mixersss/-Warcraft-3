"""Project all monster definitions and genuine spawn regions from owner resources.

Build-time numpy/scipy for checked farm samples only. No original scripts copied.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from navigation import Navigation


def numbers(value):
    return [int(x) for x in value.split(',') if x.strip().lstrip('-').isdigit()]


def build(resource):
    import numpy as np
    from scipy.ndimage import label
    definitions={}
    source=resource/'CharacterInfo.txt'
    for line in source.read_bytes().decode('gb18030',errors='replace').splitlines():
        a=line.split('\t')
        if not a[0].isdigit() or len(a)<79:continue
        identity=int(a[0])
        if identity in definitions:raise ValueError('Duplicate character definition')
        definitions[identity]={'name':a[1],'control':int(a[4]),'territory':int(a[26]),
            'level':int(a[60]),'hp':int(a[61]),'base_xp':int(a[59]),
            'attack_min':int(a[65]),'attack_max':int(a[66]),'defence':int(a[68]),
            'speed':int(a[78]),'drops':sorted(set(n for field in (46,51) for n in numbers(a[field]) if n>0)),
            'locations':[]}
    regions_path=ROOT/'assets/regions.json';regions=json.loads(regions_path.read_text())
    navs={};components={};bounds_by_map={};unknown=set();spawn_hashes={}
    for name,region in regions.items():
        n=Navigation(ROOT/'assets'/region['navigation']);navs[name]=n
        grid=np.frombuffer(n.cells,dtype=np.uint8).reshape(n.height,n.width)
        labels,_=label(grid);home=n.nearest(region['spawns'][0],12)
        x,y=n.cell(home);components[name]=(labels,int(labels[y,x]))
    for directory in sorted(resource.iterdir()):
        if not directory.is_dir():continue
        # A few copied spawn tables exist in unrelated folders. Bind by actual
        # matching map filename, not by every file found in a directory.
        path=directory/(directory.name+'ChaSpn.txt')
        if not path.exists():continue
        name=directory.name;spawn_hashes[name]=hashlib.sha256(path.read_bytes()).hexdigest()
        for line in path.read_bytes().decode('gb18030',errors='replace').splitlines():
            a=line.split('\t')
            if len(a)<8 or not a[0].isdigit():continue
            lo,hi=numbers(a[1]),numbers(a[2]);models=numbers(a[4]);counts=numbers(a[5]);respawn=numbers(a[7])
            if len(lo)!=2 or len(hi)!=2 or any(x<0 or x>409600 for x in lo+hi) or any(l>h for l,h in zip(lo,hi)):continue
            for i,model in enumerate(models):
                if model<=0:continue
                if model not in definitions:unknown.add(model);continue
                record={'map':name,'rectangle_cm':[lo,hi],
                        'count':counts[min(i,len(counts)-1)] if counts else None,
                        'respawn_seconds':respawn[min(i,len(respawn)-1)] if respawn else None}
                if record not in definitions[model]['locations']:definitions[model]['locations'].append(record)
                bounds_by_map.setdefault((name,model),[]).append((lo,hi))
    literal_calls=0
    for directory in sorted(resource.iterdir()):
        if not directory.is_dir() or directory.name=='script':continue
        for path in sorted(directory.glob('*.lua')):
            text=path.read_bytes().decode('gb18030',errors='replace')
            text=re.sub(r'--\[\[.*?\]\]','',text,flags=re.S)
            text='\n'.join(line.split('--')[0] for line in text.splitlines())
            for match in re.finditer(r'\bCreateCha\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*-?\d+\s*,\s*(\d+)\s*\)',text):
                model,x,y,respawn=map(int,match.groups())
                if model not in definitions:unknown.add(model);continue
                if not (0<=x<=409600 and 0<=y<=409600):continue
                location={'map':directory.name,'rectangle_cm':[[x,y],[x,y]],'count':1,
                          'respawn_seconds':respawn,'source_kind':'map_lua_literal',
                          'conditions_not_evaluated':True}
                if location not in definitions[model]['locations']:
                    definitions[model]['locations'].append(location);literal_calls+=1
    added=0
    for (name,model),bounds in bounds_by_map.items():
        monster=definitions[model]
        if name not in regions or monster['control']!=5 or monster['territory']==1 or monster['level']<=0 or monster['hp']<=0:continue
        region=regions[name];n=navs[name];labels,home_component=components[name]
        old=region['farms'].get(str(model));points=list(old['points']) if old else []
        if not points:
            for lo,hi in bounds:
                for fx,fy in ((.5,.5),(.15,.15),(.85,.85),(.15,.85),(.85,.15)):
                    p=n.nearest((int(lo[0]+(hi[0]-lo[0])*fx),int(lo[1]+(hi[1]-lo[1])*fy)),6)
                    if not p or not (lo[0]<=p[0]<=hi[0] and lo[1]<=p[1]<=hi[1]):continue
                    x,y=n.cell(p)
                    if labels[y,x]!=home_component:continue
                    if list(p) not in points:points.append(list(p))
                    break
                if len(points)>=4:break
        if not points and old is None:continue
        if old is None:added+=1
        region['farms'][str(model)]={'level':monster['level'],'hp':monster['hp'],'drops':monster['drops'],'points':points}
    monsters={str(k):v for k,v in definitions.items() if v['control']==5}
    other={str(k):v for k,v in definitions.items() if v['control']!=5 and v['locations']}
    data={'monsters_with_located_source_spawns':sum(bool(v['locations']) for v in monsters.values()),
          'definitions_without_located_spawn':[int(k) for k,v in monsters.items() if not v['locations']],
          'version':1,'source_character_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
          'spawn_source_sha256':spawn_hashes,'monsters':monsters,'other_spawn_actors':other,
          'unknown_spawn_models':sorted(unknown),'locations_are_spawn_regions_not_live_positions':True,
          'literal_map_lua_spawn_calls':literal_calls,
          'dynamic_lua_spawns_exhaustively_parsed':False,
          'ground_farm_species_by_map':{k:sum(bool(x['points']) for x in v['farms'].values()) for k,v in regions.items()}}
    (ROOT/'assets/world-mobs.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
    regions_path.write_text(json.dumps(regions,ensure_ascii=False,separators=(',',':'))+'\n')
    print('Definitions',len(monsters),'maps',len(spawn_hashes),'spawn regions',sum(len(m['locations']) for m in monsters.values()),'new ground species',added)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('resource',type=Path)
    build(p.parse_args().resource)
