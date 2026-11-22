"""Render native Trade stock and per-player selection for the classic3-tab shop UI."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SERVICES=[('Insert gems', 'OpenForge'),('Combine gems','OpenUnite'),('Create sockets','OpenMilling'),
 ('Extract gems','OpenGetStone'),('Fuse apparel','OpenFusion'),('Strengthen fusion','OpenUpgrade'),
 ('Upgrade equipment','OpenItemTiChun'),('Recharge coral','OpenItemEnergy'),('Repair','OpenRepair')]

def pages(shop,limit=60):
 if shop.get('sections'):
  result=[]
  for section in shop['sections']:
   ids=set(section['ids']);part=dict(shop,items=[i for i in shop['items'] if i['id'] in ids]);part.pop('sections',None)
   result.extend(pages(part,limit))
  return result
 buckets=[[],[],[]]
 for item in shop['items']:
  kind=item['kind'];bucket=0 if 1<=kind<=11 else 1 if kind in (19,20,21,22,23,24,27) else 2
  buckets[bucket].append(item['id'])
 count=max(1,max((len(b)+limit-1)//limit for b in buckets))
 return [[bucket[p*limit:(p+1)*limit] for bucket in buckets] for p in range(count)]

def render(catalog,compat=False):
 if catalog.get('catalog_revision')==56:return (ROOT/'render-alpha56.lua').read_bytes()
 if catalog.get('catalog_revision')==57:return (ROOT/'render-alpha57.lua').read_bytes()
 if catalog.get('catalog_revision')==58:return (ROOT/'render-alpha58.lua').read_bytes()
 if catalog.get('catalog_revision')==59:return (ROOT/'render-alpha59.lua').read_bytes()
 lines=['-- OWNER_CITY_SHOPS_V2_BEGIN','OwnerNativeShops = {}','OwnerNativeSelection = {}',
        'OwnerBasicGems={'+','.join('[%d]=true'%i['id'] for s in catalog['shops'] for i in s['items'] if i['kind'] in (49,50))+'}']
 if not compat:
  lines.append('OwnerFreshFairies={'+','.join('[%d]=%d'%(i['id'],1 if i['id'] in (*range(231,238),681) else 0) for s in catalog['shops'] for i in s['items'] if i['kind']==59)+'}')
 for shop in catalog['shops']:
  batches=pages(shop)
  lines.append('OwnerNativeShops[%s] = {pages={'%json.dumps(shop['key']))
  for page,panels in enumerate(batches,1):
   lines.append('[%d] = {tp=TRADE_NOMAL,berth=-1,owner_native_shop=%s,'%(page,json.dumps(shop['key'])))
   for index,panel in enumerate(panels,1):
    lines.append('[%d]={itemtype=%d,count=%d,item={%s},price={}},'%(index,index-1,len(panel),','.join(map(str,panel))))
   lines.append('[4]={itemtype=3,count=0,item={},price={}}},')
  lines.append('}}')
 lines.append((ROOT/('native_trade-alpha47.lua' if compat else 'native_trade-alpha55.lua' if catalog.get('catalog_revision',0)<=55 else 'native_trade.lua')).read_text())
 if catalog.get('catalog_revision',0)>=56:
  lines.append((ROOT/'owner_progression.lua').read_text())
  lines.append((ROOT/'ground_gems.lua').read_text())
 for shop in catalog['shops']:
  key=json.dumps(shop['key']);lines.extend(['function '+shop['function']+'()',
   ' Talk(1,%s)'%json.dumps(shop['name']+' - gold shop. Choose Trade to open items.'),
   ' for _,stock in pairs(OwnerNativeShops[%s].pages) do stock.tp=TRADE_NOMAL end'%key,
   ' Trade=OwnerNativeShops[%s].pages[1]'%key])
  for page in range(1,len(pages(shop))+1):
   label=shop['sections'][page-1]['label'] if shop.get('sections') else ('Trade' if page==1 else 'Trade - part '+str(page))
   lines.append(' Text(1,%s,OwnerOpenTrade,%s,%d)'%(json.dumps(label),key,page))
  if shop['key']=='forge':
   for label,function in SERVICES:lines.append(' Text(1,%s,%s)'%(json.dumps(label),function))
  if shop['key']=='jewellery':
   lines.append(' Text(1,"Get missing bag expansions",OwnerOpenTrade,"owner-bags",0)')
  if shop['key']=='progress':
   for job,label in ((1,'Swordsman'),(2,'Hunter'),(4,'Explorer'),(5,'Herbalist')):
    lines.append(' Text(1,"First profession: %s",OwnerOpenTrade,"owner-profession",%d)'%(label,job))
   lines.extend([' Text(1,"Second profession",JumpPage,2)',' Text(1,"Get level 3 stall",OwnerOpenTrade,"owner-stall",0)',' Text(1,"Restore basic combat spell",OwnerOpenTrade,"owner-combat",0)',' Text(1,"Gem loot counters",OwnerOpenTrade,"owner-gem-stats",0)',
    ' Talk(2,"Choose second profession at level 40.")'])
   for job,label in ((8,'Champion'),(9,'Crusader'),(12,'Sharpshooter'),(13,'Cleric'),(14,'Seal Master'),(16,'Sea Voyager')):
    lines.append(' Text(2,"Second profession: %s",OwnerOpenTrade,"owner-profession",%d)'%(label,job))
   lines.extend([' Text(2,"Back",JumpPage,1)',' Text(2,"Close",CloseTalk)'])
  lines.extend([' Text(1,"Close",CloseTalk)','end'])
 if catalog.get('catalog_revision',0)>=57:lines.append((ROOT/'possession.lua').read_text())
 if catalog.get('catalog_revision',0)>=60:
  lines.append((ROOT/'continuous_experience.lua').read_text())
  lines.append((ROOT/'experience_diagnostics.lua').read_text())
 lines.append('-- OWNER_CITY_SHOPS_V2_END')
 return ('\n'.join(lines)+'\n').encode('ascii')
