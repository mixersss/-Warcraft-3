"""Broken hunter gear, paid repair acknowledgements and confirmed shoreline movement."""
import dataclasses,struct,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from test_pet_economy import item
from test_development import scene
from repairs import Repairs
from equipment import Equipment,ItemCatalog
from classic_wire import string
from navigation import Navigation
import test_alpha26 as scheduling

class Repair53Tests(unittest.TestCase):
 def make(self):
  w=scene();w.own.values.update({0:29,4:2,8:5000});w.bag_ready=True;w.bag_capacity=24
  w.own.equipment={6:9999,9:9};w.bag={19:item(33,endurance=49,max_endurance=10000,valid=False),6:item(27,endurance=10000,max_endurance=10000)}
  actor=dataclasses.replace(w.entities[2],identity=3,control=2,x=w.own.x+100,y=w.own.y,handle=303);w.entities[3]=actor
  npcs=SimpleNamespace(by_service={'repair':[{'key':'smith','position':actor.position,'map':'garner'}]})
  gear=ItemCatalog(ROOT/'assets/items.json');send=Mock();repair=Repairs(w,npcs,gear,send)
  p=SimpleNamespace(world=w,nav=Mock(),position=lambda now:w.position(now),move_to=Mock(return_value=True))
  return w,gear,repair,send,p
 def open_quote(self,r,send,p):
  self.assertTrue(r.tick(1,p));npc=r.context[0]
  menu=struct.pack('>IB',npc,1)+string('Smith')+b'\x02'+string('Trade')+string('Repair')
  self.assertTrue(r.observe(802,menu,2));self.assertEqual(send.call_args.args[0],301)
  self.assertTrue(r.observe(546,b'',3));r.tick(4,p)
  self.assertEqual(send.call_args.args,(23,struct.pack('>IIBB',3,303,2,19)))
 def test_level29_hunter_repairs_own_level25_bow_not_future_level30_bow(self):
  w,g,r,s,p=self.make();self.assertEqual(r.candidates(),[(2,19)]);self.assertFalse(w.bag[19].valid)
 def test_paid_repair_needs_both_native_durability_and_exact_gold_delta(self):
  w,g,r,s,p=self.make();self.open_quote(r,s,p)
  r.observe(544,string('Bow')+struct.pack('>I',600),5);self.assertEqual(s.call_args.args,(24,b'\x01'))
  self.assertFalse(w.bag[19].valid);self.assertEqual(w.own.values[8],5000)
  w.bag[19]=dataclasses.replace(w.bag[19],endurance=10000,valid=True)
  self.assertTrue(r.tick(6,p));self.assertEqual(r.confirmed,0)
  w.own.values[8]=4400;self.assertFalse(r.tick(7,p));self.assertEqual(r.confirmed,1)
 def test_repaired_bow_equips_over_novice_sword_using_real_action(self):
  w,g,r,s,p=self.make();w.bag[19]=dataclasses.replace(w.bag[19],valid=True,endurance=10000)
  e=Equipment(w,g,s);policy=SimpleNamespace(sequence=2,emit=Mock())
  self.assertTrue(e.tick(1,policy));self.assertEqual(e.pending[0],33)
  self.assertEqual(policy.emit.call_args.args[0][-4:],struct.pack('>hh',19,-1))
  self.assertEqual(w.own.equipment[9],9)
 def test_unaffordable_quote_is_declined_and_money_never_changed_locally(self):
  w,g,r,s,p=self.make();self.open_quote(r,s,p)
  r.observe(544,string('Bow')+struct.pack('>I',5000),5)
  self.assertEqual(s.call_args.args,(24,b'\x00'));self.assertFalse(r.busy);self.assertEqual(w.own.values[8],5000)
 def test_changed_item_quote_cannot_repair_unrelated_replacement(self):
  w,g,r,s,p=self.make();self.open_quote(r,s,p);w.bag[19]=item(8)
  r.observe(544,string('Bow')+struct.pack('>I',1),5)
  self.assertEqual(s.call_args.args,(24,b'\x00'));self.assertFalse(r.busy)
 def test_repair_timeout_preserves_damaged_item_and_yields(self):
  w,g,r,s,p=self.make();before=w.bag[19];self.open_quote(r,s,p)
  self.assertFalse(r.tick(20,p));self.assertEqual(w.bag[19],before);self.assertEqual(r.confirmed,0)
  self.assertEqual(s.call_args.args,(24,b'\x00'));self.assertFalse(r.tick(21,p))
 def test_unverified_service_without_real_repair_menu_does_not_send_item_request(self):
  w,g,r,s,p=self.make();r.tick(1,p)
  r.observe(802,struct.pack('>IB',3,1)+string('Smith')+b'\x01'+string('Trade'),2)
  self.assertFalse(r.busy);self.assertFalse(any(c.args[0]==23 for c in s.call_args_list))
 def test_coral_and_other_unrepairable_items_are_not_sent_to_repair(self):
  w,g,r,s,p=self.make();w.bag={0:item(867,endurance=49,max_endurance=10000,valid=False)}
  self.assertEqual(r.candidates(),[])
 def test_broken_worn_armour_does_not_beat_a_working_lower_level_replacement(self):
  w,g,r,s,p=self.make();w.own.equipment={2:313}
  w.own.equipment_details={2:{'identity':313,'valid':False,'endurance':49,'max_endurance':10000}}
  self.assertIsNotNone(g.upgrade(w.own,306,3,item(306)))
 def test_same_id_replacement_waits_for_real_validity_and_durability_update(self):
  w,g,r,s,p=self.make();w.own.equipment={2:306};w.bag={4:item(306,endurance=10000,max_endurance=10000)}
  w.own.equipment_details={2:{'identity':306,'valid':False,'endurance':49,'max_endurance':10000}}
  e=Equipment(w,g,s);policy=SimpleNamespace(sequence=2,emit=Mock());self.assertTrue(e.tick(1,policy));e.tick(2,policy)
  self.assertEqual(e.confirmed,0);w.own.equipment_details[2].update(valid=True,endurance=10000);e.tick(3,policy)
  self.assertEqual(e.confirmed,1)
 def test_broken_bag_item_is_explained_in_equipment_report(self):
  w,g,r,s,p=self.make();e=Equipment(w,g,s);e.tick(1,SimpleNamespace(sequence=1,emit=Mock()))
  self.assertTrue(any(b['id']==33 and 'ремонт' in b['reason'] for b in e.blockers))

class Recovery53Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.nav=Navigation(ROOT/'assets/garner-navigation.json')
 def test_report15_position_has_short_physical_exit_without_backtracking_to_cell_centre(self):
  point=(220335,278344);route=self.nav.recovery_path(point)
  self.assertTrue(self.nav.needs_recovery(point));self.assertGreaterEqual(len(route),2)
  self.assertNotEqual(route[1],(220325,278325));self.assertFalse(self.nav.needs_recovery(route[-1]))
  self.assertEqual(route[0],point)
 def test_server_confirmed_active_escape_is_not_cancelled_or_blacklisted(self):
  w,p,q=scheduling.ProfessionSchedulingTests().policy(2);w.own.x,w.own.y=220335,278344;p.nav=self.nav
  p.recover_to_ground(100);route=list(p.offmesh_route);self.assertTrue(route)
  w.move_state=0;w.move_packet_number=p.last_sent_sequence;w.motion[w.own_id]=(route,100,10)
  before=p.offmesh_requests;p.recover_to_ground(104)
  self.assertEqual(p.offmesh_requests,before);self.assertEqual(p.offmesh_blocked,{})
  self.assertIn('сервер подтвердил',p.offmesh_reason)
 def test_native_escape_wait_remains_bounded_when_no_arrival_is_received(self):
  w,p,q=scheduling.ProfessionSchedulingTests().policy(2);w.own.x,w.own.y=220335,278344;p.nav=self.nav
  p.recover_to_ground(100);route=list(p.offmesh_route);w.move_state=0;w.move_packet_number=p.last_sent_sequence
  w.motion[w.own_id]=(route,100,1);p.recover_to_ground(121)
  self.assertNotIn('сервер подтвердил',p.offmesh_reason)


class EscapePlan53Tests(unittest.TestCase):
 def policy(self):
  from escape_plan import EscapePlan,RescueDirectory
  w=scene();w.bag_ready=True;w.bag_capacity=24;w.own.values.update({1:100,31:100,2:100,32:100})
  from stuck_return import StuckReturn
  p=SimpleNamespace(world=w,offmesh_since=0,stuck_return=StuckReturn(),transaction_busy=lambda:False,
    pending_action=None,sitting=SimpleNamespace(tick=Mock(return_value=False)),emit=Mock(),sequence=1)
  return w,p,EscapePlan('private-name',RescueDirectory())
 def test_one_minute_without_exit_resyncs_once_not_an_endless_login_loop(self):
  w,p,e=self.policy();self.assertFalse(e.tick(59,p))
  with self.assertRaises(ConnectionError):e.tick(60,p)
  self.assertEqual(e.resyncs,1);self.assertFalse(e.tick(100,p));self.assertFalse(e.tick(599,p))
  self.assertEqual(w.own.position,(223200,278700));p.emit.assert_not_called()
 def test_native_owned_ticket_is_used_before_reconnecting(self):
  w,p,e=self.policy();w.bag={3:item(4602)};self.assertTrue(e.tick(60,p))
  self.assertEqual(e.resyncs,0);self.assertTrue(p.stuck_return.pending)
  self.assertEqual(p.emit.call_args.args[0][-4:],struct.pack('>hh',3,-1))
 def test_low_hp_recovery_is_bounded_then_resyncs_if_no_native_healing(self):
  w,p,e=self.policy();w.bag={3:item(4602)};w.own.values[1]=50
  self.assertTrue(e.tick(60,p));p.sitting.tick.assert_called();p.emit.assert_not_called()
  with self.assertRaises(ConnectionError):e.tick(120,p)
 def test_same_area_resync_budget_survives_new_gameplay_session(self):
  from escape_plan import EscapePlan
  w,p,e=self.policy()
  with self.assertRaises(ConnectionError):e.tick(60,p)
  second=EscapePlan(e.name,e.directory);self.assertFalse(second.tick(130,p));self.assertEqual(second.resyncs,0)
 def test_ticket_purchase_is_independent_of_missing_custom_shop_overlay(self):
  from town import Town
  from life import LifeItems
  import random
  w,p,e=self.policy();w.own.values.update({0:29,4:2,8:10000});w.bag={0:item(1847,7)}
  life=LifeItems(ROOT/'assets');t=Town(w,life,ItemCatalog(ROOT/'assets/items.json'),None,random.Random(1),(0,0))
  self.assertIsNone(t.petcare);self.assertIn(4602,t.critical_items());self.assertEqual(t.emergency_ticket,4602)

if __name__=='__main__':unittest.main()
