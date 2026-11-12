"""Real stall state machine, economy, inventory and native captured codecs."""
import json,struct,sys,unittest
from pathlib import Path
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from market import Market,MarketCatalog,MarketDirectory,read_offers,start_request,buy_request
from inventory import BagItem
from equipment import ItemCatalog
from life import LifeItems
from classic_wire import ProtocolError,string
from test_development import scene
from coordination import tactic_for
from collections import Counter

class MarketTests(unittest.TestCase):
 def make(self):
  w=scene();w.own.values.update({0:35,4:1,13:2,8:1000000});w.bag_ready=True;w.bag_capacity=48;w.bag_disabled=False
  gear=ItemCatalog(ROOT/'assets/items.json');life=LifeItems(ROOT/'assets');catalog=MarketCatalog(ROOT/'assets')
  send=Mock();d=MarketDirectory();m=Market(w,send,w.own.name,1,catalog,gear,life,d)
  policy=SimpleNamespace(career=None,story=None,chests=None,adventure=None,sequence=1,emit=Mock(),nav=Mock(),home=w.own.position,position=lambda now:w.own.position,move_to=Mock(return_value=True))
  return w,send,m,policy
 def item(self,identity=885,count=5):return BagItem(identity,count,100,100,0,0,0,True)
 def packet(self,owner=2,identity=885,price=25000,grid=0,count=3):
  return struct.pack('>IB',owner,1)+string('Shop')+struct.pack('>BHB I H 4H BB 2I B',grid,identity,count,price,50,100,100,0,0,0,1,0,0,0)
 def test_native_plain_and_five_instance_attributes(self):
  f=json.loads((ROOT/'tests/fixtures/native_stall.json').read_text())
  for kind,payload in f['fixtures'].items():
   owner,offers=read_offers(bytes.fromhex(payload));self.assertEqual(owner,456)
   grid,price,item=offers[0];self.assertEqual((grid,price,item.identity,item.count),(0,25000,885,2))
   self.assertEqual(len(item.instance_attributes),5 if kind=='instance' else 0)
 def test_malformed_or_modern_stall_format_is_not_accepted(self):
  p=self.packet()
  for bad in (p[:-1],p+b'\0',p[:4]+b'\xff'+p[5:]):
   with self.assertRaises(ProtocolError):read_offers(bad)
 def test_native_purchase_has_no_destination_grid(self):
  self.assertEqual(buy_request(456,2,3),struct.pack('>IBB',456,2,3))
  self.assertEqual(start_request('Shop',[(0,25000,2,7)]),string('Shop')+b'\x01'+struct.pack('>BIBB',0,25000,2,7))
  with self.assertRaises(ValueError):start_request('Shop',[(0,1,1,7),(0,1,1,8)])
 def test_surplus_only_protects_needed_rare_stock_and_enhancements(self):
  w,s,m,p=self.make();w.bag={0:self.item(885,5),1:replace(self.item(885,4),forge=1),2:replace(self.item(885,4),parameters=(0,123)),3:self.item(3296),4:self.item(1847)}
  offers=m.offers(p);self.assertEqual(offers,[(0,25000,3,0)])
  p.career=SimpleNamespace(needed_items=lambda:{885});self.assertEqual(m.offers(p),[])
 def test_owned_better_gear_is_not_sold(self):
  w,s,m,p=self.make()
  i=next(i for i in m.gear.gear if m.useful_gear(i) and i in m.catalog.items)
  w.bag={0:self.item(i)};self.assertEqual(m.offers(p),[])
 def test_class_incompatible_gear_is_not_bought(self):
  w,s,m,p=self.make();i=next(i for i,g in m.gear.gear.items() if g['jobs']!=[-1] and 1 not in g['jobs'])
  self.assertFalse(m.useful_gear(i))
 def test_learning_waits_for_native_skill_and_consumption(self):
  w,s,m,p=self.make();w.bag={0:self.item(3296,1)}
  self.assertTrue(m.learn(1,p));p.emit.assert_called_once()
  w.skills[241]={'level':1};m.learn(2,p);self.assertEqual(m.confirmed_learns,0)
  w.bag={};m.learn(3,p);self.assertEqual(m.confirmed_learns,1)
 def test_no_free_skill_without_life_points(self):
  w,s,m,p=self.make();w.own.values[13]=0;w.bag={0:self.item(3296,1)}
  self.assertFalse(m.learn(0,p));p.emit.assert_not_called()
 def test_open_only_after_arrival_and_stock_and_server_ack(self):
  w,s,m,p=self.make();w.skills[241]={'level':1};w.bag={0:self.item()};m.next_shift=0
  p.nav.nearest.return_value=(w.own.x+1000,w.own.y)
  self.assertTrue(m.tick(1,p,True));self.assertEqual(m.state,'travelling');s.assert_not_called()
  m.tick(2,p,True);p.move_to.assert_called_once();s.assert_not_called()
  m.pitch=w.own.position;m.tick(3,p,True);self.assertEqual(s.call_args.args[0],330);self.assertEqual(m.confirmed_opens,0)
  m.observe(858,struct.pack('>I',2),4);self.assertEqual(m.confirmed_opens,0)
  m.observe(858,struct.pack('>I',1),5);self.assertEqual(m.confirmed_opens,1);self.assertEqual(m.trade_until,2405)
 def test_forty_minute_rotation_needs_server_closure(self):
  w,s,m,p=self.make();m.stock=[(0,25000,1,0)];m.opened(10)
  m.tick(2409,p,True);s.assert_not_called()
  m.tick(2410,p,True);s.assert_called_once_with(333,b'');self.assertEqual(m.state,'closing')
  m.tick(2411,p,True);self.assertEqual(m.state,'closing')
  m.observe(857,struct.pack('>I',1),2412);self.assertEqual(m.state,'idle');self.assertGreaterEqual(m.next_shift,3612)
 def test_open_timeout_requests_close_and_never_assumes_success(self):
  w,s,m,p=self.make();m.state='opening';m.deadline=10
  m.tick(11,p,True);self.assertEqual(m.state,'closing');self.assertEqual(m.confirmed_opens,0);s.assert_called_once_with(333,b'')
 def test_sold_out_and_danger_close_stall(self):
  for empty in (True,False):
   w,s,m,p=self.make();m.stock=[] if empty else [(0,25000,1,0)];m.opened(0)
   m.tick(1,p,empty);s.assert_called_once_with(333,b'')
 def test_only_asked_visible_nearby_stall_can_sell_to_bot(self):
  w,s,m,p=self.make();w.entities[2].stall='Shop';m.context=(2,10)
  m.observe(854,self.packet(owner=99),1);s.assert_not_called()
  m.observe(854,self.packet(),2);s.assert_called_once_with(332,buy_request(2,0))
  self.assertEqual(m.confirmed_buys,0);w.bag={0:self.item(885,1)}
  m.tick(3,p,True);self.assertEqual(m.confirmed_buys,0)
  w.own.values[8]-=25000;m.tick(4,p,True);self.assertEqual(m.confirmed_buys,1)
 def test_overpriced_and_unneeded_and_distant_stalls_do_not_spend(self):
  for case in ('price','cash','distance','not_requested','not_stall'):
   w,s,m,p=self.make();w.entities[2].stall='Shop';m.context=(2,10)
   if case=='cash':w.own.values[8]=1001
   if case=='distance':w.entities[2].x+=1000
   if case=='not_requested':m.context=None
   if case=='not_stall':w.entities[2].stall=''
   m.observe(854,self.packet(price=2000000000 if case=='price' else 25000),1);s.assert_not_called()
 def test_stall_sale_notices_only_change_own_confirmed_stock(self):
  w,s,m,p=self.make();m.stock=[(0,25000,3,0)];m.opened(0)
  m.observe(856,struct.pack('>IBB',2,0,2),1);self.assertEqual(m.sold_units,0)
  m.observe(856,struct.pack('>IBB',1,0,2),2);self.assertEqual(m.sold_units,2);self.assertEqual(m.stock[0][2],1)
 def test_rune_goals_follow_owner_gannon_tier_and_preserve_ten(self):
  w,s,m,p=self.make();self.assertEqual(m.rune_goal(),{3428:10,3429:10})
  w.bag={0:self.item(3428,12)};self.assertEqual(m.offers(p)[0][2],2)
  self.assertEqual(m.needed()[3429],10);w.own.values[0]=60;self.assertEqual(m.rune_goal(),{3455:10,3456:10})
 def test_class_gem_goals_reserve_one_and_change_with_actual_profession(self):
  w,s,m,p=self.make();self.assertEqual(m.gem_goals(),{863:1,862:1})
  w.own.values[4]=12;self.assertEqual(m.gem_goals(),{861:1,860:1})
  w.bag={0:self.item(861,3)};self.assertEqual(m.offers(p)[0][2],2)
  w.own.values[4]=13;self.assertEqual(m.gem_goals(),{1012:1,862:1})
 def test_two_hundred_workers_share_thirty_spaced_city_pitches_and_rotate(self):
  d=MarketDirectory();leases=[]
  for i in range(200):
   city=('garner','magicsea','darkblue')[i%3];slot=d.reserve(str(i),city,0)
   if slot is not None:leases.append((city,slot))
  self.assertEqual(len(leases),30);self.assertEqual(len(set(leases)),30)
  d.release('0');self.assertEqual(d.reserve('new','garner',1),0)
  self.assertEqual(Counter(tactic_for(i) for i in range(1,201)),{'farm':80,'hybrid':120})

class IntegrationTests(unittest.TestCase):
 def test_active_stall_blocks_combat_equipment_and_movement(self):
  from hunter import Hunter
  from navigation import Navigation
  from headless import Report
  w=scene();send=Mock();h=Hunter(w,Navigation(ROOT/'assets/argent-navigation.json'),send,Report(),Mock(),'stall-test')
  h.started=0;h.market=SimpleNamespace(busy=True,tick=Mock(),reason='selling')
  h.equipment=SimpleNamespace(tick=Mock());h.tick(100)
  h.market.tick.assert_called_once();h.equipment.tick.assert_not_called();send.assert_not_called()
  self.assertEqual(h.attacks,0)
 def test_npc_book_request_only_with_real_life_points_and_budget(self):
  from town import Town
  import random
  w=scene();w.own.values.update({0:10,4:1,13:1,8:20000});w.bag_ready=True;w.bag_disabled=False;w.bag_capacity=48
  w.bag={0:BagItem(1847,10,0,0,0,0,0,True)}
  life=LifeItems(ROOT/'assets');gear=ItemCatalog(ROOT/'assets/items.json')
  t=Town(w,life,gear,{'first_job':1,'target_job':9},random.Random(1),w.own.position)
  self.assertEqual(t.choose_want(),(3296,1))
  w.own.values[13]=0;self.assertNotEqual(t.choose_want(),(3296,1))
 def test_rejected_unconfirmed_open_does_not_permanently_freeze_worker(self):
  helper=MarketTests();w,send,m,p=helper.make();m.state='opening';m.deadline=10
  m.tick(11,p,True);self.assertEqual(m.state,'closing')
  m.tick(27,p,True);self.assertEqual(m.state,'idle');self.assertEqual(m.confirmed_opens,0)
 def test_confirmed_stall_without_closure_ack_remains_stationary(self):
  helper=MarketTests();w,send,m,p=helper.make();m.stock=[(0,1,1,0)];m.opened(0);m.request_close(10)
  m.tick(30,p,True);self.assertEqual(m.state,'closing');self.assertTrue(m.active_confirmed)
 def test_stall_book_and_recipe_wishes_never_grant_inventory(self):
  helper=MarketTests();w,send,m,p=helper.make();before=dict(w.bag)
  needed=m.needed();self.assertIn(3296,needed);self.assertIn(3428,needed)
  self.assertEqual(w.bag,before);send.assert_not_called()

if __name__=='__main__':unittest.main()
