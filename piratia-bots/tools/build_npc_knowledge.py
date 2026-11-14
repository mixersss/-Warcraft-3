"""Project every static NPC placement from owner resources; never execute Lua."""
import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SERVICES={
 'trade':{'BuyPage'},'teleport':{'GoTo','GoToWhere','GoTosdBoss'},
 'bank':{'OpenBank'},'repair':{'OpenRepair'},'hair':{'OpenHair'},
 'spawn':{'SetSpawnPos'},'guild':{'CreateGuild','ListAllGuild','GuildBank'},
 'ship_build':{'CreateBoat'},'ship_repair':{'RepairBoat','RepairBerthList'},
 'ship_supply':{'SupplyBoat','SupplyBerthList'},'ship_launch':{'LuanchBerthList'},
 'ship_salvage':{'SalvageBerthList'},'ship_trade':{'TradeBerthList'},
 'ship_level':{'BoatLevelBerthList'},'forge':{'OpenForge','OpenUnite','OpenMilling','OpenFusion'},
 'exchange':{'SendExchangeData','SendExchangeXData','TransferDiamond'},
}

def uncomment(s):
    # Preserve quoted strings; -- inside a label is not the start of a comment.
    token=re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|--\[\[.*?\]\]|--[^\r\n]*',re.S)
    return token.sub(lambda m:m[0] if m[0][0] in '\"\'' else '\n'*m[0].count('\n'),s)

def functions(resource):
    result={};hashes={}
    for path in sorted((resource/'script/MisScript').glob('NpcScript*.lua')):
        raw=path.read_bytes();hashes[path.name]=hashlib.sha256(raw).hexdigest()
        source=uncomment(raw.decode('gb18030',errors='replace'))
        starts=list(re.finditer(r'(?m)^\s*function\s+(\w+)\s*\(',source))
        for i,m in enumerate(starts):
            body=source[m.start():starts[i+1].start() if i+1<len(starts) else len(source)]
            if m[1] in result and result[m[1]]!=body:raise ValueError('Ambiguous NPC function '+m[1])
            result[m[1]]=body
    return result,hashes

def build(resource,out):
    funcs,script_hashes=functions(resource);npcs=[];tables={};unknown=set();duplicate_copies=[]
    for path in sorted(resource.rglob('*.txt')):
        if not path.name.lower().endswith('npc.txt'):continue
        if 'script' in path.relative_to(resource).parts:
            duplicate_copies.append(path.relative_to(resource).as_posix());continue
        # Bind a table to its actual directory/map; do not import stale copied tables.
        mapname=path.parent.name
        if path.name.lower()!=mapname.lower()+'npc.txt':continue
        tables[mapname]=hashlib.sha256(path.read_bytes()).hexdigest()
        seen=set()
        for line in path.read_bytes().decode('gb18030',errors='replace').splitlines():
            a=line.split('\t')
            if not a[0].isdigit() or len(a)<13:continue
            identity=int(a[0]);position=list(map(int,a[5].split(',')))
            if identity in seen:raise ValueError('Duplicate NPC placement ID')
            seen.add(identity)
            if len(position)!=2 or any(not 0<=x<409600 for x in position):raise ValueError('Invalid NPC position')
            function=a[11];body=funcs.get(function,'')
            if not body:unknown.add(function)
            # Candidate services are statically visible, not a claim every branch is open.
            tokens=set(re.findall(r'\b[A-Za-z_]\w*\b',body))|{function}
            services=sorted(name for name,handlers in SERVICES.items() if handlers&tokens)
            missions=sorted(set(map(int,re.findall(r'AddNpcMission\s*\(\s*(\d+)\s*\)',body))))
            if missions:services.append('quest')
            menus=[{'page':int(page),'handler':handler} for page,handler in
                   re.findall(r'Text\s*\(\s*(\d+)\s*,\s*"(?:\\.|[^"\\])*"\s*,\s*(\w+)',body)]
            offers=sorted(set(map(int,re.findall(r'\b(?:Weapon|Defence|Other)\s*\(\s*(\d+)\s*\)',body))))
            shop=bool(offers and any(m['handler']=='BuyPage' for m in menus))
            npcs.append({'key':mapname+':'+str(identity),'source_id':identity,'map':mapname,
                         'name':a[1],'model':int(a[3]),'position':position,'region':a[8],
                         'script_function':function,'script_found':bool(body),
                         'services':services,'mission_source_ids':missions,
                         'menu_handlers':menus,'offers':offers,'verified_shop_binding':shop,
                         'conditions_not_evaluated':bool(re.search(r'\b(?:if|TriggerCondition)\b',body)),
                         'source_kind':'static_npc_table'})
    # These are NPC model definitions, not fabricated placements for unlocated actors.
    definitions={}
    for line in (resource/'CharacterInfo.txt').read_bytes().decode('gb18030',errors='replace').splitlines():
        a=line.split('\t')
        if a[0].isdigit() and len(a)>4 and a[4] in ('2','3'):
            definitions[int(a[0])]={'name':a[1],'control':int(a[4])}
    placed={n['model'] for n in npcs}
    data={'version':1,'npcs':npcs,'model_definitions':definitions,
          'models_without_static_placement':sorted(set(definitions)-placed),
          'tables_sha256':tables,'npc_scripts_sha256':script_hashes,
          'excluded_stale_script_table_copies':duplicate_copies,'unresolved_functions':sorted(unknown),
          'static_tables_exhaustively_imported':True,'dynamic_lua_spawns_exhaustively_parsed':False,
          'availability_requires_live_server':True}
    out.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
    print('Static NPCs',len(npcs),'tables',len(tables),'maps with NPCs',len({n['map'] for n in npcs}),
          'shops',sum(n['verified_shop_binding'] for n in npcs),'unresolved functions',len(unknown),
          'unlocated NPC model definitions',len(data['models_without_static_placement']))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('resource',type=Path);p.add_argument('--out',type=Path,default=ROOT/'assets/world-npcs.json')
    a=p.parse_args();build(a.resource,a.out)
