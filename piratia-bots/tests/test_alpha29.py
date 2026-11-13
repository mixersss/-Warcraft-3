"""Live full-bag report: safely sell junk before accepting class letters."""
import sys,struct,unittest,dataclasses
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from world import Entity
from adventure import NPCS,talk_request
from vendor import sell_request
from test_adventure import offers
import test_alpha18 as vendor_base
import test_alpha26 as policy_base

class FullBagTests(unittest.TestCase):
 def test_full_bag_sells_even_small_plain_stack_not_a_permanent_five_item_reserve(self):
  f=vendor_base.VendorTests();w,v,p=f.make();w.bag_capacity=1;w.bag={0:f.item(1613,3)}
  self.assertEqual(v.choices(p),[(0,1613,3)])
  w.bag_capacity=48;self.assertEqual(v.choices(p),[(0,1613,3)])
 def test_quest_items_and_modified_items_survive_space_pressure(self):
  f=vendor_base.VendorTests();w,v,p=f.make();w.bag_capacity=1;w.bag={0:f.item(1613,3)}
  p.career=__import__('types').SimpleNamespace(needed_items=lambda:{1613})
  self.assertEqual(v.choices(p),[])
  p.career=None;w.bag[0]=dataclasses.replace(w.bag[0],forge=1)
  self.assertEqual(v.choices(p),[])
 def test_full_native_sell_flow_precedes_senna_and_keeps_real_account_money(self):
  w,p,q=policy_base.ProfessionSchedulingTests().policy(1)
  f=vendor_base.VendorTests();_,v,_=f.make();v.world=w;p.vendor=v
  w.bag_ready=True;w.bag_disabled=False;w.bag_capacity=1;w.bag={0:f.item(1613,3)};w.own.values[8]=54
  p.tick(100);self.assertEqual(q.requests,0);self.assertIsNotNone(v.sale_target)
  point=v.sale_target['position'];w.own.x,w.own.y=point;w.motion.clear();p.pending_action=None;p.action_open=False;p.next_action=0
  w.entities[99]=Entity(11,99,199,2,0,*point,40)
  p.tick(101);p.send.assert_called_with(301,talk_request(99))
  self.assertEqual(q.requests,0)
  v.observe(802,offers(99,[]),102,p.send)
  v.observe(805,struct.pack('>IBIB',99,1,0,0),103,p.send)
  p.tick(104);p.send.assert_called_with(308,sell_request(99,0,3))
  self.assertEqual(w.bag[0].count,3);self.assertEqual(w.own.values[8],54)
  w.bag={};w.own.values[8]=60;p.tick(105)
  self.assertEqual(v.confirmed_sales,1)
  w.own.x,w.own.y=NPCS['senna'];w.motion.clear()
  w.entities[88]=Entity(11,88,188,2,0,*NPCS['senna'],40)
  p.tick(106);p.tick(107);p.send.assert_called_with(301,talk_request(88))
  self.assertEqual(q.requests,1)
 def test_no_safe_surplus_is_reported_without_discarding_items_or_spamming_accept(self):
  w,p,q=policy_base.ProfessionSchedulingTests().policy(1)
  f=vendor_base.VendorTests();_,v,_=f.make();v.world=w;p.vendor=v
  w.bag_ready=True;w.bag_capacity=1;w.bag={0:f.item(3296,1)}
  before=dict(w.bag)
  for now in (100,101,102):p.tick(now)
  self.assertEqual(w.bag,before);self.assertEqual(q.requests,0)
  self.assertIn('нет места',p.mode)

if __name__=='__main__':unittest.main()
