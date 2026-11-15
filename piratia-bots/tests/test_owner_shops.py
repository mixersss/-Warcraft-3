"""Native merchant overlay, stock sets, adjacent NPCs and actual price bounds."""
import json,shutil,struct,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from life import LifeItems
from mechanics import MechanicsKnowledge
from market import MarketCatalog
from owner_shops import npc_near
from town import Town,function_request
from classic_wire import string
from test_development import scene
from world import Entity

def overlay():
 specs=[('Apparel and Wings',[5001]),('Fairies and Food',[680,232]),('Forge Supplies',[885]),('Travel Tickets',[4602]),('Experience and Luck',[3844,3845])]
 prices={5001:50000,680:20000,232:2000,885:5000,4602:5000,3844:10000,3845:10000};rows=[]
 for index,(name,items) in enumerate(specs):
  rows.append({'key':'garner:owner-v2:'+str(155+index),'source_id':155+index,'map':'garner','name':name,'model':17,
   'position':[224750,(2777+index*2)*100+50],'region':'Argent City','script_function':'OwnerShop'+str(index),
   'script_found':True,'services':['trade']+(['forge'] if index==2 else []),'mission_source_ids':[],
   'menu_handlers':['OpenForge'] if index==2 else [],'offers':items,'verified_shop_binding':True,
   'conditions_not_evaluated':True,'source_kind':'owner-native-shops-v2','menu_pages':{str(i):2 if i==5001 else 1 for i in items}})
 return {'version':2,'npcs':rows,'prices':{str(i):p for i,p in prices.items()},'names':{str(i):'Небесная ягода' if i==3844 else 'предмет'+str(i) for i in prices}}

def assets(path):
 for name in ('life-items.json','town-services.json','items.json','world-npcs.json','market-items.json'):shutil.copy2(ROOT/'assets'/name,path/name)
 (path/'owner-city-shops.json').write_text(json.dumps(overlay(),ensure_ascii=False))

class OwnerShopTests(unittest.TestCase):
 def test_installed_supplier_prices_names_and_berry_alias(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);assets(p);life=LifeItems(p)
   self.assertEqual(len(life.npcs.rows),526);self.assertEqual(life.prices[3844],10000);self.assertEqual(life.names[3844],'Небесная ягода')
   self.assertTrue(any(n['name']=='Experience and Luck' for n in life.npcs.sellers(3844)))
   self.assertIn('Experience and Luck',life.npcs.answer(['где','купить','ня'],'garner',(224750,278450)))
 def test_corrupt_optional_cache_keeps_base_catalog(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);assets(p)
   for bad in ({'version':2,'npcs':[None]*5},dict(overlay(),prices={})):
    (p/'owner-city-shops.json').write_text(json.dumps(bad));life=LifeItems(p)
    self.assertIsNotNone(life.owner_shop_problem);self.assertEqual(len(life.npcs.rows),521)
 def test_adjacent_npcs_choose_nearest_not_first_entity(self):
  w=scene();w.entities[100]=Entity(17,100,1,2,0,224750,278350,40);w.entities[101]=Entity(17,101,1,2,0,224750,278450,40)
  self.assertEqual(npc_near(w,(224750,278450)).identity,101)
 def test_town_selects_native_stock_set_containing_desired_item(self):
  w=scene();town=Town(w,Mock(),Mock(),{},Mock(),w.own.position);town.wanted=(5001,1);town.target_shop={'menu_pages':{'5001':2}};town.context=(700,'talk',100)
  labels=['Trade','Trade - part 2','Close'];packet=struct.pack('>IB',700,1)+string('Shop')+bytes([3])+b''.join(string(v) for v in labels)+b'\0'
  send=Mock();self.assertTrue(town.observe(802,packet,10,send));send.assert_called_once_with(301,function_request(700,1,1))
 def test_mechanics_uses_new_forge_and_price_without_fake_success(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);assets(p);life=LifeItems(p);k=MechanicsKnowledge(ROOT/'assets/mechanics.json',life.npcs)
   self.assertEqual(k.items[3844]['price'],10000);self.assertTrue(any(n['name']=='Forge Supplies' for n in k.explain('forge')['candidate_npcs']))
   self.assertFalse(k.explain('forge')['native_action_success_verified'])
 def test_market_guide_cannot_undercut_new_npc_buyback(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);assets(p);m=MarketCatalog(p);m.prices=Mock();m.prices.guide.return_value=1000
   self.assertGreater(m.price(5001),25000);self.assertEqual(m.price(5001),37500)

if __name__=='__main__':unittest.main()
