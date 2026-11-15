"""Real bag actions, monostat fairy care, stable randomized activities and earned trade."""
import dataclasses,json,struct,sys,tempfile,unittest,random
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from test_development import scene
from inventory import BagItem
from life import LifeItems
from mechanics import MechanicsKnowledge
from pet_care import PetCare,FRUITS
from economy import Economy
LIFE=LifeItems(ROOT/'assets');MECHANICS=MechanicsKnowledge(ROOT/'assets/mechanics.json',LIFE.npcs)

def item(identity,count=1,**kw):
 d=dict(identity=identity,count=count,endurance=5000,max_endurance=5000,energy=240,max_energy=240,forge=0,valid=True)
 d.update(kw);return BagItem(**d)

def phase_time(e,w,name,start=0):
 return next(t for t in range(start,start+3600) if e.phase(w,t)==name)

class FairyTests(unittest.TestCase):
 def make(self):
  w=scene();w.own.values.update({0:20,4:1,8:40000});w.own.build_id='crusader_speed';w.bag_ready=True;w.bag_capacity=48
  care=PetCare(w,LIFE,MECHANICS,'test-care',{'target_job':9});p=SimpleNamespace(emit=Mock(),sequence=2,mandatory_work=lambda:False)
  return w,care,p
 def test_second_generation_or_junior_choice_is_stable_and_follows_build(self):
  w,c,p=self.make();self.assertEqual(c.stat,'STR');self.assertIn(c.preferred,(232,681))
  self.assertEqual(PetCare(w,LIFE,MECHANICS,'test-care',{'target_job':9}).preferred,c.preferred)
  w.own.build_id='voyager_tank';self.assertEqual(PetCare(w,LIFE,MECHANICS,'tank').stat,'CON')
 def test_all_owner_builds_feed_only_their_one_selected_stat(self):
  from pet_care import BUILD_STATS,FAIRIES
  for build,stat in BUILD_STATS.items():
   with self.subTest(build=build):
    w,_,p=self.make();w.own.build_id=build;c=PetCare(w,LIFE,MECHANICS,build)
    self.assertIn(c.stat,('STR','STA','CON','DEX'));self.assertEqual(c.stat,stat)
    wrong=next(i for s,i in FRUITS.items() if s!=stat)
    w.bag={1:item(FAIRIES[stat]),2:item(2312,3),4:item(FRUITS[stat]),5:item(wrong)}
    self.assertTrue(c.tick(1,p));self.assertEqual(p.emit.call_args.args[0][-4:],struct.pack('>hh',4,1))
 def test_reorder_uses_native_whole_stack_swap_and_waits_for_server(self):
  w,c,p=self.make();w.bag={5:item(232),1:item(1847,3)};before=dict(w.bag)
  self.assertTrue(c.tick(1,p));self.assertEqual(p.emit.call_args.args[0][8:],bytes([12])+struct.pack('>hhh',5,0,1));self.assertEqual(w.bag,before)
  c.tick(2,p);self.assertEqual(c.confirmed,0)
  w.bag={1:before[5],5:before[1]};c.tick(3,p);self.assertEqual(c.confirmed,1);self.assertEqual(w.bag[5].count,3)
 def test_food_requires_consumption_and_stamina_gain(self):
  w,c,p=self.make();w.bag={1:item(232,endurance=1000),2:item(2312,3)}
  self.assertTrue(c.tick(1,p));self.assertEqual(p.emit.call_args.args[0][8:],bytes([11])+struct.pack('>hh',2,1))
  w.bag[2]=dataclasses.replace(w.bag[2],count=2);c.tick(2,p);self.assertEqual(c.confirmed,0)
  w.bag[1]=dataclasses.replace(w.bag[1],endurance=3500);c.tick(3,p);self.assertEqual(c.confirmed,1)
 def test_only_chosen_stat_fruit_is_used_and_failed_growth_is_not_success(self):
  w,c,p=self.make();w.bag={1:item(232),2:item(2312,3),4:item(276,2),5:item(278,2)}
  self.assertTrue(c.tick(1,p));self.assertEqual(p.emit.call_args.args[0][-4:],struct.pack('>hh',4,1))
  w.bag[4]=dataclasses.replace(w.bag[4],count=1);w.bag[1]=dataclasses.replace(w.bag[1],energy=120)
  c.tick(2,p);self.assertEqual(c.growth_failures,1);self.assertEqual(c.growth_success,0);self.assertEqual(w.bag[5].count,2)
 def test_successful_growth_confirms_only_observed_single_stat_gain(self):
  w,c,p=self.make();w.bag={1:item(232),2:item(2312,3),4:item(276)};c.tick(1,p)
  del w.bag[4];w.bag[1]=dataclasses.replace(w.bag[1],energy=0,max_energy=480,instance_attributes=((MECHANICS.data['item_attribute_ids']['ITEMATTR_VAL_STR'],2),))
  c.tick(2,p);self.assertEqual(c.growth_success,1);self.assertTrue(c.fairy()[2]['monostat_matches_owner_policy'])
 def test_mixed_stat_fairy_is_preserved_not_fed_wrong_fruit(self):
  w,c,p=self.make();w.bag={1:item(232,instance_attributes=((26,2),(28,2))),2:item(2312,3),4:item(276)}
  before=dict(w.bag);self.assertFalse(c.tick(1,p));p.emit.assert_not_called();self.assertEqual(w.bag,before)
 def test_expert_book_requires_native_skill_level_three(self):
  w,c,p=self.make();w.bag={1:item(232,energy=0),2:item(2312,3),4:item(609)};c.tick(1,p)
  self.assertEqual(p.emit.call_args.args[0][-4:],struct.pack('>hh',4,-1));del w.bag[4]
  c.tick(2,p);self.assertEqual(c.confirmed,0);w.skills[280]={'level':3};c.tick(3,p);self.assertEqual(c.confirmed,1)
 def test_missing_ack_never_fakes_care_or_repeats_immediately(self):
  w,c,p=self.make();w.bag={1:item(232,endurance=1000),2:item(2312,3)};before=dict(w.bag)
  c.tick(1,p);c.tick(14,p);c.tick(15,p)
  self.assertEqual(c.timeouts,1);self.assertEqual(c.confirmed,0);self.assertEqual(p.emit.call_count,1);self.assertEqual(w.bag,before)
 def test_missing_bag_snapshot_or_book_reorder_is_not_consumption(self):
  w,c,p=self.make();w.bag={1:item(232,energy=0),2:item(2312,3),4:item(609)};c.tick(1,p)
  w.skills[280]={'level':3};w.bag[5]=w.bag.pop(4);c.tick(2,p);self.assertEqual(c.confirmed,0)
  del w.bag[5];w.bag_ready=False;c.tick(3,p);self.assertEqual(c.confirmed,0)
  w.bag_ready=True;c.tick(4,p);self.assertEqual(c.confirmed,1)
 def test_fairy_purchase_uses_installed_merchant_real_price_and_two_confirmations(self):
  from test_owner_shops import assets,overlay
  from equipment import ItemCatalog
  from town import Town,trade_page
  from classic_wire import string
  with tempfile.TemporaryDirectory() as d:
   path=Path(d);assets(path);data=overlay();fairies=data['npcs'][1]
   data['catalog_revision']=48;data['fresh_fairies']=True;fairies['menu_pages']['232']=1;data['prices']['232']=2000;data['names']['232']='Фея Силы'
   (path/'owner-city-shops.json').write_text(json.dumps(data))
   life=LifeItems(path);w,c,p=self.make();c.life=life;c.preferred=232;w.own.values[8]=2500;w.bag={0:item(1847,10),2:item(2312,2)}
   town=Town(w,life,ItemCatalog(ROOT/'assets/items.json'),{},random.Random(1),w.own.position);town.petcare=c
   self.assertEqual(town.choose_want(),(232,1))
   town.wanted=(232,1);town.target_shop={'menu_pages':{'232':1}};town.context=(700,'talk',20)
   send=Mock();packet=struct.pack('>IB',700,1)+string('Fairies')+bytes([1])+string('Trade')
   town.observe(802,packet,1,send);send.reset_mock()
   packet=struct.pack('>IBIBBBH',700,1,0,1,2,1,232)
   town.observe(805,packet,2,send);self.assertEqual(send.call_args.args[0],308)
   w.bag[3]=item(232);town.tick(3,p,False);self.assertEqual(town.confirmed,0)
   w.own.values[8]=500;town.tick(4,p,False);self.assertEqual(town.confirmed,1)

class EconomyTests(unittest.TestCase):
 def make(self,name='econ'):
  w=scene();w.own.values.update({0:20,4:1,31:1000});w.bag_ready=True;w.bag_capacity=48
  return w,Economy(name,ROOT/'assets')
 def test_each_actor_has_a_stable_random_order_with_all_activities(self):
  orders=set()
  for n in range(30):
   w,e=self.make(str(n));e.phase(w,100);order=tuple(e.stages);orders.add(tuple(name for name,_ in order))
   self.assertEqual(sum(t for _,t in order),1800);self.assertEqual(set(name for name,_ in order),{'business','history','income','professions','trade','progression'})
   for t in range(101,110):e.phase(w,t);self.assertEqual(tuple(e.stages),order)
  self.assertGreater(len(orders),20)
 def test_new_cycle_gets_new_order_and_fights_hold_current_activity(self):
  w,e=self.make();now=phase_time(e,w,'income');self.assertEqual(e.phase(w,now),'income');e.busy=True
  _,other=self.make();later=next(t for t in range(now+3600,now+5400) if other.phase(w,t)!='income')
  expected=other.phase(w,later);self.assertEqual(e.phase(w,later),'income')
  e.busy=False;self.assertEqual(e.phase(w,later),expected)
 def test_cash_farm_uses_actual_drop_sources_and_stops_for_full_stock(self):
  from farm_plan import HuntLearning
  w,e=self.make();region=json.loads((ROOT/'assets/regions.json').read_text())['garner'];learning=HuntLearning('econ');now=phase_time(e,w,'income')
  models=e.models(w,region,learning,now);self.assertTrue(models)
  for m in models:self.assertIn(str(m),e.data['sources']);self.assertLessEqual(region['farms'][str(m)]['level'],20)
  w.bag={0:item(1000,30)};self.assertEqual(e.models(w,region,learning,now),set())
 def test_profession_novice_has_no_economy_detours(self):
  w,e=self.make();w.own.values[4]=0
  self.assertEqual({e.phase(w,t) for t in range(0,4000,10)},{'progression'})
 def test_patchouli_stall_and_chat_price_ignore_old_learned_5000_price(self):
  from test_market import MarketTests
  w,s,m,p=MarketTests().make();m.catalog.prices=Mock();m.catalog.prices.guide.return_value=5000
  self.assertEqual(m.catalog.price(1000),500);self.assertEqual(m.ask_price(1000),500)
 def test_banking_keeps_stall_stock_but_can_store_excess(self):
  from test_alpha44 import BankTests
  w,s,m,p,b=BankTests().make();m.keep_stall_stock=True
  w.bag={n:item(1000,1) for n in range(8)}
  self.assertEqual([slot for slot,_,_ in b.candidates(p)],[6,7])

class ProfessionTests(unittest.TestCase):
 def test_actual_book_and_skill_point_deltas_required_after_stall_skill(self):
  from life_professions import LifeProfessions
  w=scene();w.own.values.update({0:20,4:1,13:2});w.bag_ready=True;w.bag_capacity=48
  e=Economy('prof',ROOT/'assets');life=LifeProfessions(w,LIFE,'prof',e);life.active=True
  self.assertIsNone(life.next_book());w.skills[241]={'level':1};book,skill=life.next_book();w.bag={4:item(book)}
  now=phase_time(e,w,'professions');p=SimpleNamespace(emit=Mock(),sequence=1)
  self.assertTrue(life.tick(now,p,True));self.assertEqual(p.emit.call_args.args[0][-4:],struct.pack('>hh',4,-1))
  del w.bag[4];w.skills[skill]={'level':1};life.tick(now+1,p,True);self.assertEqual(life.confirmed,0)
  w.own.values[13]=1;life.tick(now+2,p,True);self.assertEqual(life.confirmed,1)

class CityTicketTests(unittest.TestCase):
 def test_owned_destination_ticket_precedes_insufficient_portal_fare(self):
  from city_travel import CityTravel
  from stuck_return import StuckReturn
  w=scene();w.own.values.update({0:20,4:1,8:0,1:100,31:100,2:100,32:100});w.bag_ready=True;w.bag_capacity=48;w.bag={4:item(4603)}
  send=Mock();travel=CityTravel(w,send,7,{'first_job':1});returner=StuckReturn()
  p=SimpleNamespace(world=w,career=None,town=None,story=None,stuck_return=returner,transaction_busy=lambda:False,pending_action=None,
                    sitting=SimpleNamespace(tick=lambda *a:False),emit=Mock(),sequence=1)
  self.assertTrue(travel.tick(1,p,True));self.assertEqual(p.emit.call_args.args[0][-4:],struct.pack('>hh',4,-1));send.assert_not_called()
  self.assertEqual(returner.pending[1],'magicsea');self.assertEqual(w.own.values[8],0)

if __name__=='__main__':unittest.main()
