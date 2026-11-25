"""Paid satiety, responsive loot and recovery based on actual gameplay progress."""
import dataclasses
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import test_alpha42 as magic
import test_alpha55 as pets
import test_alpha18 as vendor
from inventory import BagItem
from loot import QuestLoot
from farm_plan import HuntLearning

class RecoveryTests(unittest.TestCase):
 def make(self):
  w,p=magic.MagicTests().make();p.fast_progression=True;p.target=1000
  p.economy=SimpleNamespace(emergency_until=0);p.transaction_busy=lambda:False
  return w,p,p.progress_monitor
 def test_passive_hp_sp_and_target_changes_do_not_hide_idle_minute(self):
  w,p,m=self.make();m.tick(0,p)
  w.own.values[1]+=1;w.own.values[2]+=1;m.tick(30,p)
  p.target=None;w.own.values[2]+=1;m.tick(61,p)
  self.assertEqual(m.recoveries,1);self.assertEqual(p.economy.emergency_until,181)
  self.assertEqual(p.next_action,61);self.assertIsNone(p.target)
 def test_walking_without_any_result_eventually_rebuilds_hunt_plan(self):
  w,p,m=self.make();m.tick(0,p)
  for now in range(30,181,30):w.own.x+=200;m.tick(now,p)
  self.assertEqual(m.recoveries,1);self.assertGreater(p.economy.emergency_until,180)
 def test_watchdog_preserves_a_growing_farm_search_past_idle_minute(self):
  from route_search import RoutePending
  from test_alpha24 import IncrementalNavigationTests
  w,p,m=self.make()
  p.target=None
  p.nav=IncrementalNavigationTests().nav()
  w.own.x,w.own.y=1050,1050
  p.search_goal=(6050,1050)
  p.search_started=0
  p.search_deadline=180
  for now in range(0,91,10):
   p.nav.begin_turn(expansions=20)
   try:
    m.tick(now,p)
    with self.assertRaises(RoutePending):p.nav.path((1050,1050),p.search_goal)
   finally:p.nav.end_turn()
  self.assertEqual(m.recoveries,0)
  m.tick(100,p)
  self.assertEqual(m.recoveries,0)
  m.tick(115,p)
  self.assertEqual(m.recoveries,1)
  self.assertIsNone(p.search_goal)
  self.assertFalse(p.nav.local.searches)
 def test_real_damage_and_native_transactions_are_preserved(self):
  w,p,m=self.make();m.tick(0,p)
  w.entities[1000].values[1]-=20;m.tick(59,p);m.tick(100,p)
  self.assertEqual(m.recoveries,0)
  p.transaction_busy=lambda:True;m.tick(500,p)
  self.assertEqual(m.recoveries,0)

class Fairy57Tests(unittest.TestCase):
 def test_cost_based_rule_matches_server_and_never_fabricates_state(self):
  w,c,p=pets.Fairy55Tests().make();c.cost_based_possession=True
  w.bag[1]=dataclasses.replace(w.bag[1],endurance=3000,instance_attributes=((26,6),(27,0),(28,0),(29,0),(30,0)))
  self.assertTrue(c.possession_usable(1));self.assertEqual(c.possession_confirmed,0)
  w.bag[1]=dataclasses.replace(w.bag[1],endurance=599)
  self.assertFalse(c.possession_usable(1))

class Loot57Tests(unittest.TestCase):
 def test_earned_patchouli_can_fill_existing_stack_in_full_bag(self):
  w,p=magic.MagicTests().make();w.bag_ready=True;w.bag_capacity=1
  w.bag={0:vendor.VendorTests().item(1000,3)}
  w.own_hits={123:(9,True)};w.items={10:(1000,10,w.own.position,1,123,8)}
  loot=QuestLoot(w);loot.fast_mode=True;loot.ground_gems={1000}
  p.emit=Mock()
  self.assertTrue(loot.tick(10,p,{1000}))
  self.assertEqual(loot.confirmed,0)
  w.bag[0]=vendor.VendorTests().item(1000,4)
  w.items={}
  loot.tick(11,p,{1000})
  self.assertEqual(loot.confirmed,1)

 def test_funding_sells_patchouli_first_without_batch_delay(self):
  v=vendor.VendorTests()
  w,seller,p=v.make()
  w.bag={0:v.item(4315,1),1:v.item(1000,1)}
  w.own.values[8]=900
  seller.sell_patchouli=True;seller.batch_farming=True
  p.supply_funding_goal=1200
  self.assertEqual(seller.choices(p)[0],(1,1000,1))
  self.assertTrue(seller.tick(100,p,True))

 def test_waits_for_native_protection_then_picks_blueprint_with_bounded_ack_deadline(self):
  w,p=magic.MagicTests().make();w.bag_ready=True;w.bag_capacity=24;w.bag={}
  w.own_hits={123:(9,True)};w.items={10:(1000,10,w.own.position,1,123,9)}
  loot=QuestLoot(w);loot.fast_mode=True;loot.ground_gems={1000};p.emit=Mock()
  self.assertFalse(loot.tick(10,p,{1000}));self.assertTrue(loot.tick(10.3,p,{1000}))
  self.assertAlmostEqual(p.next_action,10.45);self.assertAlmostEqual(loot.pending[-1],22.3)
  w.items={};w.bag={0:BagItem(1000,1,0,0,0,0,0,True)};loot.tick(10.4,p,{1000})
  self.assertEqual(loot.confirmed,1)
 def test_small_stock_does_not_send_solvent_bot_back_from_farm(self):
  w,v,p=vendor.VendorTests().make();v.batch_farming=True;v.sell_patchouli=True
  w.own.x=199000;w.own.y=260000;w.own.values[8]=1000
  w.bag={0:BagItem(1000,1,0,0,0,0,0,True)}
  self.assertFalse(v.tick(100,p,True));self.assertIsNone(v.sale_target)

class Reward57Tests(unittest.TestCase):
 def test_next_target_starts_before_late_xp_and_reward_is_not_counted_twice(self):
  w,p=magic.MagicTests().make();learning=HuntLearning('test');learning.async_rewards=True
  w.own.values[15]=100;first=w.entities[1000];learning.begin(w,first,1)
  learning.active['death_seen']=2
  second=SimpleNamespace(identity=1001,handle=22,model=75)
  learning.begin(w,second,2.1)
  self.assertEqual(learning.active['id'],1001);self.assertFalse(learning.waiting_reward(2.1))
  w.own.values[15]=150;learning.observe(w,2.3)
  self.assertEqual(learning.rows[str(first.model)]['xp'],50)
  learning.active['death_seen']=2.4;learning.finish(w,4.5,'win')
  self.assertEqual(sum(row['xp'] for row in learning.rows.values()),50)

if __name__=='__main__':unittest.main()
