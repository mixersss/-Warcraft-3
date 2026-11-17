"""Project existing native island menus, consumable destinations and map entrances."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from lua_inventory import functions,literal_calls,tokens
ROOT=Path(__file__).resolve().parents[1]

def parse_portals(source,name):
    records,errors=functions(source)
    if errors:raise ValueError('Invalid source Lua inventory')
    record=next((f for f in records if f['name']==name),None)
    if not record:return {},{},None
    text=' '.join(json.dumps(t[1]) if t[0]=='string' else t[1] for t in record['_tokens'])
    variables={}
    for key,value in re.findall(r'local\s+(\w+)\s*=\s*("[^"]*"|\d+|\w+)',text):
        variables[key]=json.loads(value) if value.startswith('"') else int(value) if value.isdigit() else variables.get(value)
    destinations={}
    for section in re.split(r'\bInitTrigger\s*\(\s*\)',text):
        move=re.search(r'TriggerAction\s*\(\s*\d+\s*,\s*GoTo\s*,\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*\)',section)
        confirm=re.search(r'Text\s*\(\s*(\d+)\s*,\s*"Teleport"',section)
        fare=re.search(r'TriggerAction\s*\(\s*\d+\s*,\s*TakeMoney\s*,\s*(\d+)',section)
        if not all((move,confirm,fare)):continue
        x,y,map_name=(variables.get(v) for v in move.groups())
        if not isinstance(x,int) or not isinstance(y,int) or not isinstance(map_name,str):continue
        destinations[int(confirm[1])]={'map':map_name,'arrival_cm':[x*100,y*100],'fare':int(fare[1]),'confirm_label':'Teleport'}
    menus={}
    for page,label,destination in re.findall(r'Text\s*\(\s*(\d+)\s*,\s*"([^"]+)"\s*,\s*JumpPage\s*,\s*(\d+)',text):
        if int(destination) in destinations:menus.setdefault(int(page),[]).append(dict(destinations[int(destination)],label=label))
    initial={(m,int(n)):int(page) for m,n,page in re.findall(r'TriggerCondition\s*\(\s*\d+\s*,\s*IsMapNpc\s*,\s*"([^"]+)"\s*,\s*(\d+)\s*\)\s*TriggerAction\s*\(\s*\d+\s*,\s*JumpPage\s*,\s*(\d+)',text)}
    return menus,initial,record['sha256']

def build(resource):
    resource=Path(resource);birth=resource/'script/birth/birth_conf.lua'
    source=birth.read_bytes().decode('gb18030',errors='replace');births={}
    for row in literal_calls(tokens(source),'AddBirthPoint'):
        if len(row)==4 and all(isinstance(v,str) for v in row[:2]) and all(type(v) is int for v in row[2:]):
            name,map_name,x,y=row;births.setdefault(name,{'map':map_name,'points':[]})['points'].append([x*100,y*100])
    itemsource=(resource/'script/calculate/ItemEffect.lua').read_bytes().decode('gb18030',errors='replace')
    records,errors=functions(itemsource)
    if errors:raise ValueError('Invalid ItemEffect inventory')
    lookup={f['name']:f for f in records};tickets=[]
    database=json.loads((ROOT.parent/'piratia-city-shops/native/item-database.json').read_text())
    for row in database:
        if row['kind']!=36 or not row['in_server'] or not row['in_client']:continue
        for hook in re.findall(r'\bJz_Script_\w+',row['effect_hooks']):
            f=lookup.get(hook)
            if not f:continue
            places=[c[1] for c in literal_calls(f['_tokens'],'MoveCity') if len(c)==2 and isinstance(c[1],str)]
            if len(set(places))!=1 or places[0] not in births:continue
            if [ {'variable':'role'},row['id'],1] not in literal_calls(f['_tokens'],'DelBagItem'):continue
            tickets.append({'item_id':row['id'],'name':row['name_en'],'birthplace':places[0],**births[places[0]],'minimum_level':row['level'],'requires_full_hp_sp':True,'source_function':hook,'function_sha256':f['sha256']})
    island_source=(resource/'script/MisScript/NpcScript02.lua').read_bytes().decode('gb18030',errors='replace')
    menus,initial,island_sha=parse_portals(island_source,'island');nodes=[];entrances=[]
    for folder in sorted(resource.iterdir()):
        if not folder.is_dir():continue
        npcs=folder/(folder.name+'npc.txt')
        if npcs.exists():
            for line in npcs.read_bytes().decode('gb18030',errors='replace').splitlines():
                a=line.split('\t')
                if len(a)<12 or not a[0].isdigit() or a[11]!='island':continue
                routes=menus.get(initial.get((folder.name,int(a[0]))),[])
                if routes:nodes.append({'map':folder.name,'npc_source_id':int(a[0]),'name':a[1],'position':list(map(int,a[5].split(','))),'routes':routes})
        switches=folder/(folder.name+'swhmap.txt')
        if switches.exists():
            for line in switches.read_bytes().decode('gb18030',errors='replace').splitlines():
                a=line.split('\t')
                if len(a)<9 or not a[0].isdigit():continue
                try:
                    position=list(map(int,a[3].split(',')));arrival=list(map(int,a[6].split(',')))
                    if len(position)!=2 or len(arrival)!=2:continue
                    entrances.append({'map':folder.name,'event_id':int(a[0]),'model':int(a[1]),'event_type':int(a[2]),'position':position,'to_map':a[5],'arrival_cm':arrival,'activation_requirement':a[7],'name':a[8],'native_visible_event_required':True})
                except ValueError:continue
    result={'version':58,'birth_source_sha256':hashlib.sha256(birth.read_bytes()).hexdigest(),'island_function_sha256':island_sha,'birthplaces':births,'tickets':tickets,'island_nodes':nodes,'entrances':entrances,'mob_knowledge':'world-mobs.json','source_regions_are_not_live_mob_positions':True,'conditional_entries_remain_native':True}
    target=ROOT/'assets/hunting-travel58.json';target.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    print('Travel knowledge:',len(births),'birthplaces,',len(tickets),'tickets,',len(nodes),'island teleporters,',sum(len(n['routes']) for n in nodes),'island routes,',len(entrances),'map entrances')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('resource',type=Path);build(p.parse_args().resource)
