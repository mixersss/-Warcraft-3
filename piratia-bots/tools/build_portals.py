"""Project active GoToWhere city portal menus and arrivals, excluding commented routes."""
import argparse
import hashlib
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def build(resource):
    body=None
    for path in (resource/'script/MisScript').glob('NpcScript*.lua'):
        text=path.read_bytes().decode('gb18030',errors='replace')
        match=re.search(r'(?m)^function\s+GoToWhere\s*\(',text)
        if not match:continue
        end=re.search(r'(?m)^function\s+',text[match.end():])
        body=text[match.start():match.end()+end.start() if end else len(text)]
        break
    if body is None:raise ValueError('No verified GoToWhere definition')
    body='\n'.join(line.split('--')[0] for line in body.splitlines())
    variables={}
    for name,value in re.findall(r'local\s+(\w+)\s*=\s*("[^"]*"|\d+|\w+)',body):
        variables[name]=value[1:-1] if value.startswith('"') else int(value) if value.isdigit() else variables.get(value)
    destinations={}
    for section in re.split(r'\bInitTrigger\s*\(\s*\)',body):
        goto=re.search(r'TriggerAction\s*\(\s*1\s*,\s*GoTo\s*,\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*\)',section)
        button=re.search(r'Text\s*\(\s*(\d+)\s*,\s*"Teleport"',section)
        fee=re.search(r'TriggerAction\s*\(\s*2\s*,\s*TakeMoney\s*,\s*(\d+)',section)
        free=re.search(r'TriggerCondition\s*\(\s*1\s*,\s*LvCheck\s*,\s*"<"\s*,\s*(\d+)',section)
        if not all((goto,button,fee,free)):continue
        x,y,map_name=(variables.get(v) for v in goto.groups())
        if not isinstance(x,int) or not isinstance(y,int) or not isinstance(map_name,str):continue
        destinations[int(button[1])]={'map':map_name,'arrival_cm':[x*100,y*100],
                                     'fare':int(fee[1]),'free_through_level':int(free[1])-1}
    initial={(m,int(n)):int(page) for m,n,page in re.findall(
        r'TriggerCondition\s*\(\s*\d+\s*,\s*IsMapNpc\s*,\s*"([^"]+)"\s*,\s*(\d+)\s*\)\s*TriggerAction\s*\(\s*\d+\s*,\s*JumpPage\s*,\s*(\d+)',body)}
    menus={}
    for page,label,target in re.findall(r'Text\s*\(\s*(\d+)\s*,\s*"([^"]+)"\s*,\s*JumpPage\s*,\s*(\d+)',body):
        if int(target) in destinations:menus.setdefault(int(page),[]).append(dict(destinations[int(target)],label=label))
    nodes=[]
    for directory in sorted(resource.iterdir()):
        if not directory.is_dir():continue
        path=directory/(directory.name+'npc.txt')
        if not path.exists():continue
        for line in path.read_bytes().decode('gb18030',errors='replace').splitlines():
            a=line.split('\t')
            if len(a)<13 or not a[0].isdigit() or a[11]!='GoToWhere':continue
            key=(directory.name,int(a[0]));routes=menus.get(initial.get(key),[])
            if routes:nodes.append({'map':directory.name,'npc_source_id':int(a[0]),'name':a[1],
                                   'position':list(map(int,a[5].split(','))),'routes':routes})
    data={'nodes':nodes,'active_source_sha256':hashlib.sha256(body.encode()).hexdigest(),
          'commented_destinations_excluded':True,'conditional_other_portal_functions_supported':False}
    (ROOT/'assets/portals.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
    print(len(nodes),'verified portal NPCs;',sum(len(n['routes']) for n in nodes),'active routes')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('resource',type=Path);build(p.parse_args().resource)
