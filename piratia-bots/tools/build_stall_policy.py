"""Curate owner-requested stall goods against real items, quests and drop tables."""
import argparse,collections,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REQUESTED=['New Sheepskin Scroll','Old Sheepskin Scroll','Elven Fruit','Stramonium Flower','Fancy Petal','Greasy Lizard Skin','Medicated Grass','Dotted Lizard Skin','Thick Fur','Fake Documentation','Animal Skin','Sharp Claw','Feather','Cactus Hair','Snowball','Ice Cream','Teleportation Rune','Fairy Ration']
def build(resource):
 load=lambda p:json.loads((ROOT/p).read_text())
 db=json.loads((ROOT.parent/'piratia-city-shops/native/item-database.json').read_text());db={r['id']:r for r in db if r['in_server']}
 old=load('assets/useful-loot.json')['items'];mobs=load('assets/world-mobs.json')['monsters'];drops=collections.defaultdict(list)
 for k,m in mobs.items():
  for i in m['drops']:drops[i].append(int(k))
 textrows={}
 for line in (resource/'ItemInfo.txt').read_text(encoding='gb18030',errors='replace').splitlines():
  a=line.split('\t')
  if a[0].isdigit() and len(a)>=94:textrows[int(a[0])]=a
 requested={};aliases={'Cactus Hair':'Cactus Hairball'}
 for name in REQUESTED:
  match=next((r for r in db.values() if r['name_en'].casefold()==aliases.get(name,name).casefold()),None)
  requested[name]={'id':match['id'] if match else None,'resolved_name':match['name_en'] if match else None,'normal_drop_species':drops[match['id']] if match else [],'equivalence':'name alias' if name in aliases else 'exact' if match else 'not found; not invented'}
 needs=set()
 for p in (resource/'script/MisScript').glob('MissionScript*.lua'):
  text=p.read_text(encoding='gb18030',errors='replace');text=re.sub(r'--\[\[.*?\]\]','',text,flags=re.S);text='\n'.join(l.split('--',1)[0] for l in text.splitlines())
  needs.update(int(m) for m in re.findall(r'MisNeed\s*\(\s*MIS_NEED_ITEM\s*,\s*(\d+)',text))
 explicit={r['id'] for r in requested.values() if r['id']};rows={}
 from sys import path
 path.insert(0,str(ROOT/'src'))
 from adventure import PROFESSION_OBJECTIVES
 profession={v[1] for v in PROFESSION_OBJECTIVES.values() if v[0]=='item'}
 for q in load('assets/town-services.json')['quests'].values():profession.update(n['id'] for n in q['needs'] if n['kind']==1)
 forge={i['id'] for s in json.loads((ROOT.parent/'piratia-city-shops/native/catalog.json').read_text())['shops'] if s['key']=='forge' for i in s['items']}
 for identity,rec in db.items():
  a=textrows.get(identity)
  if not a or a[16]!='1' or identity==1000:continue
  base=old.get(str(identity),{});category=base.get('category')
  isgear=category in ('gear','sealed')
  if isgear:
   if rec['level']<20 or not drops[identity] or 'newbie' in rec['name_en'].lower():continue
   category='gear' if category=='gear' else 'sealed';reason='source-backed dropped gear, level20+'
  elif identity in explicit:category='scroll' if identity in (684,1092) else 'care_supply' if identity==227 else 'quest_material' if identity in needs else 'requested_material';reason='explicit owner request; real item'
  elif identity in profession and drops[identity]:category='quest_material';reason='first/second profession ingredient with source drops'
  elif identity in forge or category in ('rune','gem','refining','kal','blueprint') and drops[identity]:reason='audited improvement/exchange/recipe item'
  else:continue
  if not category:category='forge_material'
  meta=dict(base);meta.update(name=rec['name_en'],name_ru=rec['name_ru'],kind=rec['kind'],category=category,level=rec['level'],stack=int(a[20]),drop_species=sorted(drops[identity]),useful_for=reason,mission_ingredient=identity in needs)
  price=rec['server_price'];meta['reference_price']=base.get('reference_price',max(50,min(2000,price*3)))
  if category in ('quest_material','requested_material','care_supply'):meta['reference_price']=max(50,min(2000,price*3))
  rows[str(identity)]=meta
 sources={}
 for line in (resource/'CharacterInfo.txt').read_text(encoding='gb18030',errors='replace').splitlines():
  a=line.split('\t')
  if not a[0].isdigit() or len(a)<53 or a[0] not in mobs:continue
  goods=[]
  for ids,rates in ((a[46],a[47]),(a[51],a[52])):
   for identity,denom in zip(re.findall(r'\d+',ids),re.findall(r'\d+',rates)):
    identity,denom=int(identity),int(denom)
    if str(identity) in rows and denom>0:goods.append({'id':identity,'denominator':denom,'base_factor':min(1,100/denom)})
  if goods:sources[a[0]]={'name':mobs[a[0]]['name'],'level':mobs[a[0]]['level'],'items':goods}
 out={'version':1,'minimum_gear_level':20,'gear_requires_source_drop':True,'patchouli_destination':'NPC1500','no_implied_runtime_craft_automation':True,'requested_resolution':requested,'items':rows,'sources':sources,'category_counts':dict(collections.Counter(r['category'] for r in rows.values())),'drop_rule':'Check_Baoliao base_factor=min(1,100/denominator); live luck, level and server rates still apply; not a guaranteed income'}
 (ROOT/'assets/stall-goods.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'))+'\n')
 print('Curated',len(rows),'goods;',len(sources),'drop models;',out['category_counts'])
 for name,r in requested.items():
  if not r['id'] or not r['normal_drop_species']:print(name,r['id'],'no confirmed ordinary drops')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('resource',type=Path);build(p.parse_args().resource)
