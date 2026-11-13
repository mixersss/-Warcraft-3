"""Slow approach, pre-navigation revival, safe seated regen and bounded route jobs."""
import json,struct,sys,unittest
from pathlib import Path
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from navigation import Navigation
from route_search import RoutePending
from sitting import Sitting,pose_request
from test_development import scene
import test_coordination as base

class SittingTests(unittest.TestCase):
 def make(self):
  world=scene();world.own.values[1]=30
  from types import SimpleNamespace
  policy=SimpleNamespace(target=None,pending_action=None,sequence=9,
     position=lambda now:world.own.position,emit=Mock())
  return world,policy,Sitting(world)
 def echo(self,w,sequence,seated):
  w.observe(508,pose_request(w.own_id,sequence,seated))
 def test_real_server_echo_is_required_for_confirmed_sitting(self):
  w,p,s=self.make();self.assertTrue(s.tick(100,p,True))
  p.emit.assert_called_once_with(struct.pack('>IIBHH',1,9,21,0,16))
  self.assertFalse(w.seated);self.assertEqual(s.confirmed,0)
  self.echo(w,9,True);s.tick(101,p,True)
  self.assertTrue(w.seated);self.assertEqual(s.confirmed,1)
  w.own.values[1]=50;s.tick(102,p,True);self.assertEqual(s.hp_observed,20)
 def test_stand_before_returning_to_work_and_do_not_fabricate_health(self):
  w,p,s=self.make();self.echo(w,8,True);hp=w.own.values[1]
  self.assertTrue(s.tick(100,p,False));self.assertTrue(w.seated)
  p.emit.assert_called_with(pose_request(1,9,False));self.assertEqual(w.own.values[1],hp)
  self.echo(w,9,False);self.assertFalse(s.tick(101,p,False));self.assertFalse(w.seated)
 def test_stale_or_other_character_pose_cannot_confirm_own_request(self):
  w,p,s=self.make();s.tick(100,p,True)
  w.observe(508,pose_request(2,9,True));s.tick(101,p,True)
  self.assertFalse(w.seated);self.assertEqual(s.confirmed,0)
 def test_pose_rejection_does_not_create_a_permanent_wait(self):
  w,p,s=self.make();s.tick(100,p,True)
  self.assertFalse(s.tick(106,p,True));self.assertEqual(s.timeouts,1)
  self.assertFalse(s.tick(110,p,True));self.assertEqual(p.emit.call_count,1)
 def test_nearby_enemy_or_recent_damage_prevents_sitting(self):
  from world import Entity
  w,p,s=self.make();w.entities[3]=Entity(103,3,7,5,1,w.own.x+400,w.own.y,40,{1:100})
  self.assertFalse(s.tick(100,p,True));p.emit.assert_not_called()
  w.entities.pop(3);s.last_hp=50
  self.assertFalse(s.tick(101,p,True));self.assertTrue(s.tick(107,p,True))
 def test_no_hp_progress_eventually_yields_to_other_recovery(self):
  w,p,s=self.make();self.echo(w,8,True);s.tick(100,p,True)
  s.tick(131,p,True);p.emit.assert_called_with(pose_request(1,9,False))
  self.echo(w,9,False);self.assertFalse(s.tick(132,p,True))
 def test_map_entry_clears_stale_pose(self):
  from test_hunt import enter_packet
  w,p,s=self.make();self.echo(w,9,True);w.enter(enter_packet());self.assertFalse(w.seated);self.assertIsNone(w.pose_packet_number)

class ProgressAndDeathTests(unittest.TestCase):
 def policy(self,monsters=0):
  f=base.CohortCombatTests();f.nav=Navigation(ROOT/'assets/argent-navigation.json');return f.policy(monsters=monsters)
 def test_monster_in_range_interrupts_long_search_route_without_premature_attack(self):
  w,p=self.policy(1);p.move_to((224500,278700),99)
  p.move_until=200;w.move_revision+=1;w.move_state=0
  p.tick(100);p.send.assert_called_with(7,b'');self.assertEqual(p.attacks,0)
  w.stop_revision+=1;w.stop_packet_number=p.last_sent_sequence;w.stop_packet_kind=1
  p.tick(100.3);self.assertEqual(p.attacks,1)
 def test_dead_character_revives_even_on_unwalkable_or_unknown_map(self):
  for bad_map in (False,True):
   w,p=self.policy();w.own.values[1]=0
   if bad_map:w.map='unknown'
   else:w.own.x=w.own.y=0
   p.tick(100);p.tick(104);p.send.assert_called_with(10,b'\x01')
   self.assertEqual(p.revive_requests,1);self.assertEqual(w.own.values[1],0)
 def test_revival_continues_after_missed_reply_and_records_delay(self):
  w,p=self.policy();w.own.values[1]=0;w.map='unknown'
  for t in (100,104,119,134,210):p.tick(t)
  self.assertEqual(p.revive_requests,4);self.assertEqual(p.summary()['revival']['attempts_in_batch'],1)
 def test_crowded_forest_does_not_hold_a_level_one_bot_forever(self):
  w,p=self.policy();w.own.values[0]=1;p.region=json.loads((ROOT/'assets/regions.json').read_text())['garner']
  p.clock=100;self.assertEqual(p.starter_models(),{103})
  p.clock=191;self.assertFalse(p.starter_models());self.assertTrue(p.planned_models())

class IncrementalNavigationTests(unittest.TestCase):
 def nav(self):
  n=Navigation.__new__(Navigation);n.origin=(0,0);n.width=80;n.height=80
  cells=bytearray([1])*6400
  for y in range(60):cells[y*80+40]=0
  n.cells=bytes(cells);n.enable_incremental();return n
 def test_search_resumes_without_claiming_an_unfinished_route_is_unreachable(self):
  n=self.nav();start=(1050,1050);goal=(6050,1050);yields=0
  for _ in range(1000):
   n.begin_turn(expansions=20)
   try:path=n.path(start,goal);break
   except RoutePending:yields+=1
   finally:n.end_turn()
  else:self.fail('Incremental search never finishes')
  self.assertGreater(yields,0);self.assertTrue(path);self.assertEqual(path[-1],goal)
  self.assertTrue(all(n.free(n.cell(p)) for p in path));self.assertFalse(n.local.searches)
 def test_one_turn_cannot_expand_more_than_budget(self):
  n=self.nav();n.begin_turn(expansions=12)
  with self.assertRaises(RoutePending):n.path((1050,1050),(6050,1050))
  self.assertLessEqual(n.planning_stats()['expanded_nodes'],12);n.end_turn()
 def test_direct_route_never_cuts_diagonal_corner(self):
  n=self.nav();cells=bytearray(n.cells);cells[1]=0;n.cells=bytes(cells)
  self.assertFalse(n.direct((0,0),(1,1)))
 def test_changed_request_finishes_previous_job_instead_of_leaking_searches(self):
  n=self.nav()
  for i in range(12):
   n.begin_turn(expansions=1)
   with self.assertRaises(RoutePending):n.path((1050,1050),(6050,1050+i*100))
   n.end_turn()
  self.assertEqual(len(n.local.searches),1)
 def test_clear_straight_route_avoids_astar_expansion(self):
  n=self.nav();n.begin_turn(expansions=0)
  self.assertTrue(n.path((50,50),(2050,2050)));self.assertEqual(n.planning_stats()['expanded_nodes'],0);n.end_turn()

class FastTransitionsTests(unittest.TestCase):
 def test_clear_shallow_angle_is_one_segment_instead_of_staircase(self):
  n=IncrementalNavigationTests().nav()
  points=n.segment((1050,1050),(3050,1650));self.assertEqual(len(points),2);self.assertTrue(n.line_clear(*points))
 def test_supercover_rejects_wall_and_corner_grazing(self):
  n=IncrementalNavigationTests().nav();self.assertFalse(n.line_clear((1050,1050),(6050,1050)))
  cells=bytearray(n.cells);cells[1]=0;n.cells=bytes(cells)
  self.assertFalse(n.line_clear((50,50),(150,150)))
 def test_fast_decisions_do_not_restart_a_productive_server_fight(self):
  w,p=ProgressAndDeathTests().policy(1)
  p.tick(100)
  for now in (100.5,101,101.5,102):
   w.entities[1000].values[1]-=5;p.tick(now)
  self.assertEqual(p.attacks,1);self.assertEqual(p.end_action_requests,0)
