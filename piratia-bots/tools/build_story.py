"""Project initial main-history definitions and exact static NPC bindings; never execute Lua."""
import argparse,hashlib,json,re
from pathlib import Path
from build_npc_knowledge import uncomment
ROOT=Path(__file__).resolve().parents[1]
ENTRY_IDS=(200,206,208,209,211,213,215,216,218,219,220,222,224,225,226,227,228,229,230)

def build(resource):
    source=resource/'script/MisScript/MissionScript02.lua'
    text=uncomment(source.read_bytes().decode('gb18030',errors='replace'))
    definitions={}
    for block in re.split(r'(?=DefineMission\s*\()',text):
        match=re.match(r'DefineMission\(\s*(\d+),\s*"([^"]+)",\s*(\d+)([^\n]*)',block)
        if match:definitions[int(match[1])]={'title':match[2],'journal':int(match[3]),'complete':'COMPLETE_SHOW' in match[4],'body':block}
    npcs=json.loads((ROOT/'assets/world-npcs.json').read_text())['npcs']
    def npc_for(identity):
        rows=[n for n in npcs if identity in n['mission_source_ids']]
        if len(rows)!=1:raise ValueError(f'Ambiguous history NPC binding {identity}: {len(rows)}')
        return rows[0]
    def needs(body):
        result=[]
        for kind,identity,count in re.findall(r'MisNeed\s*\(\s*MIS_NEED_(ITEM|KILL)\s*,\s*(\d+)\s*,\s*(\d+)',body):
            result.append({'kind':1 if kind=='ITEM' else 0,'id':int(identity),'count':int(count)})
        return result
    quests=[]
    for identity in ENTRY_IDS:
        entry=definitions[identity];journal=entry['journal']
        completion=next((i for i,d in definitions.items() if d['journal']==journal
                         and re.search(r'MisResultAction\s*\(\s*ClearMission\s*,\s*'+str(journal)+r'\s*\)',d['body'])),None)
        if completion is None:raise ValueError(f'History completion missing {identity}')
        start,end=npc_for(identity),npc_for(completion)
        demands=needs(entry['body'])
        if not demands:
            demands=[{'kind':1,'id':int(i),'count':int(c)} for i,c in re.findall(
                r'MisResultCondition\s*\(\s*HasItem\s*,\s*(\d+)\s*,\s*(\d+)',definitions[completion]['body'])]
        rewards=re.findall(r'AddExpAndType\s*,\s*2\s*,\s*(\d+)',definitions[completion]['body'])
        q={'source_id':identity,'journal':journal,'title':entry['title'],'map':start['map'],
           'position':start['position'],'receiver_map':end['map'],'receiver':end['position'],
           'needs':demands,'talk':'MIS_NEED_DESP' in entry['body'],
           'life_xp_source_reward':int(rewards[0]) if rewards else None}
        quests.append(q)
    auxiliary=definitions[214];npc=npc_for(214)
    intermediate={'journal':207,'title':auxiliary['title'],'map':npc['map'],'position':npc['position'],
                  'receiver':npc['position'],'talk':True,'intermediate':True,
                  'needs':[{'kind':1,'id':3966,'count':1}],'next_journal':208}
    data={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'quests':quests,
          'intermediates':{'207':intermediate},'later_history_exhaustively_supported':False}
    (ROOT/'assets/story-quests.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
    print(len(quests),'history journals with exact native definitions and NPC bindings')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('resource',type=Path);build(p.parse_args().resource)
