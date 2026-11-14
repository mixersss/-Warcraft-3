"""Project only audited item/skill and town-service metadata from owner resources."""
import argparse,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def text(p):return p.read_bytes().decode('gb18030',errors='replace')
def functions(source):
 starts=list(re.finditer(r'(?m)^function\s+(\w+)\s*\(',source))
 return {m[1]:source[m.start():starts[i+1].start() if i+1<len(starts) else len(source)] for i,m in enumerate(starts)}

def main():
 p=argparse.ArgumentParser();p.add_argument('resource',type=Path);r=p.parse_args().resource
 effect=functions(text(r/'script/calculate/ItemEffect.lua'))
 constants={k:int(v) for k,v in re.findall(r'(?m)^\s*(SK_\w+)\s*=\s*(\d+)',text(r/'script/calculate/variable.lua'))}
 skillrows={int(a[0]):a for line in text(r/'skillinfo.txt').splitlines() if (a:=line.split('\t'))[0].isdigit()}
 books,chests,names,prices={},{},{},{}
 for line in text(r/'ItemInfo.txt').splitlines():
  a=line.split('\t')
  if not a[0].isdigit() or len(a)<90:continue
  i=int(a[0]);names[i]=a[1];prices[i]=max(0,int(a[22]));body=effect.get(a[86],'')
  found=re.search(r'local\s+sk_add\s*=\s*(SK_\w+)',body)
  if found and 'AddChaSkill' in body:
   identity=constants.get(found[1]);sk=skillrows.get(identity)
   if sk and sk[2]=='1':
    jobs={int(pair.split(',')[0]):int(pair.split(',')[1]) for pair in sk[3].split(';')}
    prerequisites=[] if sk[12]=='-1' else [list(map(int,p.split(','))) for p in sk[12].split(';')]
    books[i]={'skill':identity,'level':max(10,int(sk[11])),'jobs':jobs,'prerequisites':prerequisites,
               'cost':max(1,int(sk[13])),'name':a[1],'active':sk[9]=='1'}
  if a[86] in ('ItemUse_XRBOX','ItemUse_SANWUBOX','ItemUse_SIWUBOX','ItemUse_WUWUBOX','ItemUse_LIUWUBOX'):
   lv=re.search(r'if lv < (\d+)',body)
   chests[i]={'level':int(lv[1]) if lv else 999,'free_slots':4,'job_required':a[86]!='ItemUse_XRBOX'}
 (ROOT/'assets/life-items.json').write_text(json.dumps({'books':books,'chests':chests,'names':names,'prices':prices},ensure_ascii=False,separators=(',',':'))+'\n')
 npc=functions('\n'.join(text(f) for f in (r/'script/MisScript').glob('NpcScript*.lua')))
 meta={};advanced={}
 for mapname in ('garner','magicsea','darkblue'):
  meta[mapname]=[]
  for line in text(r/mapname/(mapname+'npc.txt')).splitlines():
   a=line.split('\t')
   if not a[0].isdigit() or len(a)<13:continue
   body=npc.get(a[11],'')
   body='\n'.join(line.split('--')[0] for line in body.splitlines())
   for questid in (749,750,751,755,757,758):
    if re.search(r'AddNpcMission\s*\(\s*'+str(questid)+r'\s*\)',body):advanced[questid]={'map':mapname,'position':list(map(int,a[5].split(','))),'name':a[1]}
   funcs=re.findall(r'Text\s*\(\s*1\s*,\s*"([^"]+)"\s*,\s*(\w+)',body)
   idx=next((i for i,(_,fn) in enumerate(funcs) if fn=='BuyPage'),None)
   offered=[int(v) for v in re.findall(r'(?:Weapon|Defence|Other)\s*\(\s*(\d+)\s*\)',body)]
   if idx is not None and offered:
    meta[mapname].append({'position':list(map(int,a[5].split(','))),'menu':idx,'name':a[1],'offers':offered,'region':a[8]})
 script=text(r/'script/MisScript/MissionScript01.lua');quests={}
 for target,sid in ((9,749),(8,750),(12,757),(13,751),(14,755),(16,758)):
  m=re.search(r'DefineMission\(\s*'+str(sid)+r'\s*,\s*"([^"]+)"\s*,\s*(\d+)',script)
  end=script.find('DefineMission',m.end());body=script[m.end():end if end>=0 else len(script)]
  needs=[{'kind':0 if kind=='KILL' else 1,'id':int(i),'count':int(n)}
         for kind,i,n in re.findall(r'MisNeed\(\s*MIS_NEED_(KILL|ITEM)\s*,\s*(\d+)\s*,\s*(\d+)',body)]
  quests[target]=dict(advanced[sid],title=m[1],journal=int(m[2]),needs=needs)
 (ROOT/'assets/town-services.json').write_text(json.dumps({'shops':meta,'advanced':advanced,'quests':quests},ensure_ascii=False,separators=(',',':'))+'\n')
 print('Books',len(books),'chests',len(chests),'shops',sum(map(len,meta.values())),'advanced',len(advanced))
if __name__=='__main__':main()
