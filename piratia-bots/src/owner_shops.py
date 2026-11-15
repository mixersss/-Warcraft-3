"""Load the optional source configuration written by the native server-shop installer."""
import json,math
from pathlib import Path

def read_overlay(assets):
 p=Path(assets)/'owner-city-shops.json'
 if not p.exists():return None
 data=json.loads(p.read_text(encoding='utf8'))
 if (not isinstance(data,dict) or data.get('version')!=2 or not isinstance(data.get('npcs'),list)
     or len(data['npcs'])!=5 or not isinstance(data.get('prices'),dict) or not isinstance(data.get('names'),dict)):
  raise ValueError('Invalid owner shop overlay')
 identities=set()
 for npc in data['npcs']:
  if (not isinstance(npc,dict) or not isinstance(npc.get('key'),str) or not npc['key'].startswith('garner:owner-v2:')
      or npc['key'] in identities or npc['map']!='garner' or len(npc['position'])!=2
      or any(type(v) is not int or not 0<=v<409600 for v in npc['position'])):raise ValueError('Invalid owner NPC')
  identities.add(npc['key'])
  if (any(not isinstance(npc.get(k),str) for k in ('name','region','script_function','source_kind'))
      or type(npc.get('model')) is not int or not isinstance(npc.get('mission_source_ids'),list)):
   raise ValueError('Invalid owner NPC metadata')
  if (not npc['verified_shop_binding'] or not isinstance(npc['offers'],list) or not isinstance(npc.get('menu_pages'),dict)
      or not isinstance(npc.get('services'),list) or not isinstance(npc.get('menu_handlers'),list)):
   raise ValueError('Invalid native shop')
  for identity in npc['offers']:
   if type(identity) is not int or str(identity) not in data['prices']:raise ValueError('Missing owner price')
   price=data['prices'][str(identity)]
   if type(price) is not int or price not in (500,1000,2000,5000,10000,20000,50000,300000):raise ValueError('Invalid owner price')
   if not isinstance(data['names'].get(str(identity)),str):raise ValueError('Missing owner item name')
   if str(identity) not in npc['menu_pages'] or not 1<=npc['menu_pages'][str(identity)]<=11:raise ValueError('Invalid native stock page')
 return data

def npc_near(world,point):
 candidates=[e for e in world.entities.values() if e.control in (2,3) and math.dist(e.position,point)<350]
 return min(candidates,key=lambda e:(math.dist(e.position,point),e.identity),default=None)
