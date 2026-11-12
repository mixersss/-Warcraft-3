"""Owner-report regressions: combined move/attack phases and productive fight continuity."""
import struct,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from classic_wire import sequence
from hunter import movement
from navigation import Navigation
from coordination import Coordination
from fleet import Fleet
import test_coordination as base

class ActionPhaseTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.nav=Navigation(ROOT/'assets/argent-navigation.json')
 def policy(self,monsters=1):
  f=base.CohortCombatTests();f.nav=self.nav;return f.policy(monsters=monsters)
 def move_stop(self,w,p,state=8):
  w.observe(508,struct.pack('>IIBHH',w.own_id,p.last_sent_sequence,1,state,0)+sequence(struct.pack('<iiii',*w.own.position,*w.own.position)))
 def skill(self,w,p,state):
  body=struct.pack('>IIBBHH',w.own_id,p.last_sent_sequence,3,p.fight,0,state)
  if state:body+=struct.pack('>H',0)
  w.observe(508,body)
 def test_movement_inrange_does_not_end_combined_attack(self):
  w,p=self.policy();p.tick(100);self.move_stop(w,p)
  self.assertEqual(w.stop_packet_kind,1);self.assertFalse(p.action_stopped())
  p.tick(103);self.assertEqual(p.attacks,1);self.assertEqual(p.end_action_requests,0)
 def test_skill_stop_ends_combined_attack(self):
  w,p=self.policy();p.tick(100);self.skill(w,p,1)
  self.assertEqual(w.stop_packet_kind,3);self.assertTrue(p.action_stopped())
 def test_productive_normal_attack_is_not_cancelled_every_two_seconds(self):
  w,p=self.policy();p.tick(100);self.move_stop(w,p);self.skill(w,p,0)
  for now in range(103,130,3):
   w.entities[p.target].values[1]-=2;p.tick(now)
  self.assertEqual(p.attacks,1);self.assertEqual(p.end_action_requests,0)
  self.assertGreater(p.active_fight_waits,5);self.assertEqual(p.no_damage_retargets,0)
 def test_intermediate_move_stop_cannot_flush_replacement_fight(self):
  w,p=self.policy();p.tick(100);p.clock=101
  p.emit(movement(w.own_id,p.sequence,[w.own.position,(223500,278700)]))
  self.move_stop(w,p);p.flush_action(101.3)
  self.assertIsNotNone(p.pending_action);self.assertEqual(p.flushed_actions,0)
  self.skill(w,p,128);p.flush_action(101.4)
  self.assertIsNone(p.pending_action);self.assertEqual(p.flushed_actions,1)
 def test_server_immune_target_is_released_without_fourteen_second_retry_loop(self):
  w,p=self.policy(2);p.tick(100);first=p.target;self.skill(w,p,64);p.tick(103)
  self.assertNotEqual(p.target,first);self.assertGreater(p.blacklist[first],103)
  self.assertEqual(p.rejected_target_releases,1)
 def test_noobject_refusal_releases_only_current_target(self):
  w,p=self.policy(2);p.tick(100);first=p.target
  w.observe(520,struct.pack('>IBB',w.own_id,2,5));p.tick(103)
  self.assertNotEqual(p.target,first);self.assertEqual(p.rejected_target_releases,1)
 def test_busy_refusal_does_not_blacklist_legitimate_target(self):
  w,p=self.policy();p.tick(100)
  w.observe(520,struct.pack('>IBB',w.own_id,2,1));p.tick(103)
  self.assertEqual(p.target,1000);self.assertNotIn(1000,p.blacklist)
 def test_fast_movement_requests_do_not_count_as_ten_seconds_stuck(self):
  w,p=self.policy(0)
  for now in range(100,106):
   p.action_open=False;p.pending_action=None;p.move_to((223800,278700),now)
  self.assertLess(p.stuck,5)
  p.action_open=False;p.pending_action=None;p.move_to((223800,278700),111)
  self.assertEqual(p.stuck,5)
 def test_nearest_free_cell_fast_path_preserves_center(self):
  point=self.nav.waypoints[0]
  with patch.object(self.nav,'free',wraps=self.nav.free) as free:
   self.assertEqual(self.nav.nearest(point),self.nav.position(self.nav.cell(point)))
   self.assertEqual(free.call_count,1)
 def test_two_hundred_server_acknowledged_fights_keep_swinging_without_cancel(self):
  c=Coordination();f=base.CohortCombatTests();f.nav=self.nav
  policies=[f.policy(i,c,200)[1] for i in range(200)]
  for p in policies:
   p.tick(100);self.move_stop(p.world,p);self.skill(p.world,p,0)
  for now in (103,106,109):
   for p in policies:
    p.world.entities[p.target].values[1]-=5;p.tick(now)
  self.assertEqual(len({p.target for p in policies}),200)
  self.assertTrue(all(p.attacks==1 and p.end_action_requests==0 for p in policies))

class StatusTests(unittest.TestCase):
 def test_population_accepts_real_experience_without_inventing_progress(self):
  with tempfile.TemporaryDirectory() as d:
   f=Fleet(200,Path(d)/'population-status.json')
   f.update(1,connected=True,experience=14,start_experience=6)
   row=f.snapshot()['bots']['1'];self.assertEqual(row['experience'],14);self.assertEqual(row['start_experience'],6)

if __name__=='__main__':unittest.main()
