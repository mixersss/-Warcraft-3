"""Verified supplier recovery, stable Junior savings and curated real-loot stalls."""
import copy,dataclasses,json,random,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import test_pet_economy as pet_examples
from test_pet_economy import item,PetCare
import test_market as market_examples
from equipment import ItemCatalog
from town import Town
from economy import Economy
import test_alpha26 as scheduling

class Pet54Tests(unittest.TestCase):
 def make(self):
  w,c,p=pet_examples.FairyTests().make();c.life=copy.copy(c.life);c.life.owner_shops={'catalog_revision':50,'fresh_fairies':True};c.life.prices=dict(c.life.prices)
  c.life.prices.update({232:2000,681:20000,2312:1000});c.preferred=681;c.junior=True;w.bag={0:item(1847,7)}
  t=Town(w,c.life,ItemCatalog(ROOT/'assets/items.json'),None,random.Random(1),w.own.position);t.petcare=c
  return w,c,t
 def test_junior_choice_never_falls_back_to_cheaper_fairy(self):
  w,c,t=self.make();w.own.values[8]=5000
  self.assertEqual(c.purchase_identity(),681);self.assertIn(681,[i for i,n,r in c.purchase_goals()]);self.assertNotIn(232,[i for i,n,r in c.purchase_goals()])
  self.assertFalse(c.affordable_care());self.assertIn('копит',c.purchase_blocker())
 def test_junior_affordable_only_with_food_reserve(self):
  w,c,t=self.make();w.own.values[8]=22099;self.assertFalse(c.affordable_care())
  w.own.values[8]=22100;self.assertTrue(c.affordable_care());self.assertEqual(c.purchase_identity(),681)
 def test_savings_protected_from_stall_book_and_optional_ring(self):
  w,c,t=self.make();w.own.values.update({8:15000,13:1})
  self.assertEqual(c.savings(),22000);self.assertEqual(t.spend_limit(3296),0)
  self.assertGreater(t.spend_limit(1847),0);self.assertGreater(t.spend_limit(4602),0)
 def test_completed_fairy_goal_releases_savings(self):
  w,c,t=self.make();w.bag[1]=item(681,instance_attributes=((26,0),(30,0)))
  self.assertIsNotNone(c.fairy());self.assertEqual(c.savings(),0)
 def test_affordable_second_generation_not_starved_by_xp_watchdog(self):
  w,p,q=scheduling.ProfessionSchedulingTests().policy();w.own.values.update({0:20,4:1});p.target=None;p.adventure=None;p.activity=SimpleNamespace(hunting=lambda now:True);p.petcare=SimpleNamespace(needs_food_visit=lambda:False,affordable_care=lambda:True)
  feature=SimpleNamespace(context=None,pending=None,critical_items=lambda:[],combat_items=set(),life=SimpleNamespace(prices={}))
  self.assertTrue(p.task('town',feature,lambda:True,100))
 def test_missing_overlay_diagnosis_is_explicit(self):
  w,c,t=self.make();c.life.owner_shops=None
  self.assertEqual(c.purchase_goals(),[]);self.assertIn('RESTORE-BOT-SHOPS',c.summary()['purchase_blocker'])

class Trade54Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=json.loads((ROOT/'assets/stall-goods.json').read_text())
 def make(self):
  w,s,m,p=market_examples.MarketTests().make();m.catalog.enable_curated_catalog();m.broad_goods=m.focused_goods=True
  m.useful_gear=Mock(return_value=False);return w,s,m,p
 def test_requested_real_resources_present_and_unknown_names_not_invented(self):
  rows=self.data['items']
  for identity in (684,1092,3116,4352,3130,4474,3129,1747,1608,1616,1619,1691,4492,3126,227):self.assertIn(str(identity),rows)
  for name in ('Dotted Lizard Skin','Thick Fur','Teleportation Rune'):self.assertIsNone(self.data['requested_resolution'][name]['id'])
 def test_only_mob_drop_backed_gear20plus_is_stall_stock(self):
  for identity,meta in self.data['items'].items():
   if meta['category']=='gear':self.assertGreaterEqual(meta['level'],20);self.assertTrue(meta['drop_species']);self.assertNotIn('newbie',meta['name'].lower())
 def test_empty_socket_drop_equipment_sells_but_real_gems_stay_protected(self):
  w,s,m,p=self.make();w.bag={0:dataclasses.replace(item(313),parameters=(2000000000,0),instance_attributes=((36,13),(47,6),(30,3)))}
  self.assertTrue(m.offers(p));self.assertTrue(m.ordinary_gear(w.bag[0]))
  for params,forge in (((2001000000,0),0),((2000000000,1),0),((2000000000,0),1)):
   w.bag[0]=dataclasses.replace(w.bag[0],parameters=params,forge=forge);self.assertEqual(m.offers(p),[])
 def test_newbie_sword_and_level15_armour_never_enter_stall(self):
  w,s,m,p=self.make();w.bag={0:item(8),1:item(296),2:item(1000,20),3:item(4352,10)}
  offered={w.bag[slot].identity for g,price,n,slot in m.offers(p)}
  self.assertEqual(offered,{4352})
 def test_npc_vendor_sells_surplus_novice_gear_not_requested_resources(self):
  from vendor import Vendor
  w,s,m,p=self.make();w.own.values.update({0:30,4:1});w.own.equipment={9:3,6:9999}
  w.bag={0:item(8),1:item(4352,10),2:item(1747,7),3:item(1000,3)};p.market=m
  v=Vendor(w,m.life,m.gear,None,random.Random(1),w.own.position,ROOT/'assets');v.sell_patchouli=True
  selected={identity for slot,identity,n in v.choices(p)}
  self.assertIn(8,selected);self.assertIn(1000,selected);self.assertNotIn(4352,selected);self.assertNotIn(1747,selected)
  w.bag[4]=item(5001)
  self.assertNotIn(5001,{identity for slot,identity,n in v.choices(p)})
 def test_item_sources_are_actual_server_levels_not_unverified_guide_levels(self):
  self.assertEqual(self.data['sources']['295']['level'],23);self.assertEqual(self.data['sources']['85']['level'],26)
  self.assertFalse(self.data['requested_resolution']['Old Sheepskin Scroll']['normal_drop_species'])
 def test_income_phase_chooses_comfortable_actual_sources(self):
  w,s,m,p=self.make();w.own.values.update({0:29,4:2,31:2000});e=Economy('test-income',ROOT/'assets');e.trade_data=self.data;e.phase=lambda w,now:'income'
  region=json.loads((ROOT/'assets/regions.json').read_text())['garner'];learning=SimpleNamespace(blocked=lambda *a:False,dangerous=lambda *a:False)
  chosen=e.models(w,region,learning,100);self.assertTrue(chosen);minimum=29-(8 if e.cohort=='farmer' else 5)
  self.assertTrue(all(minimum<=region['farms'][str(i)]['level']<=29 for i in chosen));self.assertTrue(e.last_goods)
 def test_casters_primary_combat_supply_remains_before_fairy_goal(self):
  import test_alpha43 as suppliers
  w,t,p=suppliers.ShoppingTests().make();w.own.values[8]=40000
  _,c,_=Pet54Tests().make();c.world=w;c.preferred=232;t.petcare=c
  plan=t.plan_supplies(100,p);self.assertTrue(plan)
  self.assertEqual(t.gear.types[plan['item']],9)

class Bootstrap54Tests(unittest.TestCase):
 def test_missing_overlay_recovers_only_from_existing_verified_install_candidates(self):
  from restore_shop_knowledge import ensure_shop_knowledge
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);assets=root/'assets';assets.mkdir();server=root/'resource';server.mkdir();(server/'owner-city-shops-v2.json').write_text('{}')
   with patch('restore_shop_knowledge.restore',return_value={'restored':True,'catalog_revision':50}) as restore:
    result=ensure_shop_knowledge(assets,[server]);self.assertTrue(result['ready']);restore.assert_called_once_with(server,assets)
 def test_unknown_changed_install_not_advertised_as_ready(self):
  from restore_shop_knowledge import ensure_shop_knowledge
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);assets=root/'assets';assets.mkdir();(root/'owner-city-shops-v2.json').write_text('{}')
   with patch('restore_shop_knowledge.restore',side_effect=ValueError('unknown changed file')):
    result=ensure_shop_knowledge(assets,[root]);self.assertFalse(result['ready']);self.assertIn('unknown',result['problem'])

if __name__=='__main__':unittest.main()
