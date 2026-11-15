"""Project numeric history requirements/bindings; never publish or execute owner Lua."""
import argparse,hashlib,json,re
from pathlib import Path
from build_npc_knowledge import uncomment
ROOT=Path(__file__).resolve().parents[1]

def project(raw,npcs):
    text=uncomment(raw.decode('gb18030',errors='replace'))
    headers=list(re.finditer(r'DefineMission\s*\(\s*(\d+)\s*,\s*"([^"]+)"\s*,\s*(\d+)([^\n]*)',text))
    rows=[];seen=set()
    for i,m in enumerate(headers):
        identity,journal=int(m[1]),int(m[3]);body=text[m.end():headers[i+1].start() if i+1<len(headers) else len(text)]
        if identity in seen:raise ValueError('Duplicate mission definition')
        seen.add(identity)
        bindings=[{'key':n['key'],'name':n['name'],'map':n['map'],'position':n['position']} for n in npcs if identity in n['mission_source_ids']]
        needs=[{'kind':'item' if kind=='ITEM' else 'kill','id':int(k),'count':int(c)} for kind,k,c in re.findall(r'MisNeed\s*\(\s*MIS_NEED_(ITEM|KILL)\s*,\s*(\d+)\s*,\s*(\d+)',body)]
        turnin=[{'id':int(k),'count':int(c)} for k,c in re.findall(r'MisResultCondition\s*\(\s*HasItem\s*,\s*(\d+)\s*,\s*(\d+)',body)]
        level=[{'operator':op,'value':int(n)} for op,n in re.findall(r'MisBeginCondition\s*\(\s*LvCheck\s*,\s*"([<>=]+)"\s*,\s*(\d+)',body)]
        condition_names=sorted(set(re.findall(r'Mis(?:Begin|Result)Condition\s*\(\s*(\w+)',body)))
        custom=[n for n in condition_names if n not in {'LvCheck','NoRecord','NoMission','HasRecord','HasMission','HasItem','AlwaysFailure','AlwaysTrue'}]
        rows.append({'source_id':identity,'journal':journal,'title':m[2],
            'completion_entry':'COMPLETE_SHOW' in m[4],
            'starts_journals':[int(n) for n in re.findall(r'MisBeginAction\s*\(\s*AddMission\s*,\s*(\d+)',body)],
            'clears_journals':[int(n) for n in re.findall(r'MisResultAction\s*\(\s*ClearMission\s*,\s*(\d+)',body)],
            'needs_previous_records':[int(n) for n in re.findall(r'MisBeginCondition\s*\(\s*HasRecord\s*,\s*(\d+)',body)],
            'level_conditions':level,'needs':needs,'turnin_items':turnin,'static_npcs':bindings,
            'custom_condition_names':custom,'has_description_objective':bool(re.search(r'MisNeed\s*\(\s*MIS_NEED_DESP',body)),
            'life_xp_source':[int(n) for n in re.findall(r'AddExpAndType\s*,\s*2\s*,\s*(\d+)',body)],
            'instructions_exhaustively_parsed':False})
    return {'version':1,'source_file':'script/MisScript/MissionScript02.lua','source_sha256':hashlib.sha256(raw).hexdigest(),
        'definitions':rows,'scope':'Literal requirements and static bindings only; branches/custom conditions/quest conversations not exhaustively interpreted; not an automation expansion'}

def main():
    p=argparse.ArgumentParser();p.add_argument('resource',type=Path);args=p.parse_args()
    raw=(args.resource/'script/MisScript/MissionScript02.lua').read_bytes()
    npcs=json.loads((ROOT/'assets/world-npcs.json').read_text())['npcs'];result=project(raw,npcs)
    (ROOT/'assets/story-reference.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    print('History definitions:',len(result['definitions']),'with static bindings:',sum(bool(r['static_npcs']) for r in result['definitions']))
if __name__=='__main__':main()
