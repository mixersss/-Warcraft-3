"""Reproduce Alpha24 planning starvation and unattended safe opportunities."""
import sys,unittest,json
from pathlib import Path
from unittest.mock import patch,Mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from route_search import RoutePending
import test_alpha24 as base24
from world import Entity
from farm_plan import HuntLearning,PROFILES

class PlanningStarvationTests(unittest.TestCase):
 def test_work_before_search_does_not_consume_search_slice(self):
  n=base24.IncrementalNavigationTests().nav()
  with patch('navigation.time.perf_counter',return_value=100) as wall:
   n.begin_turn(expansions=8)
   wall.return_value=200  # other bots/work have consumed wall time
   with self.assertRaises(RoutePending):n.path((1050,1050),(6050,1050))
  self.assertEqual(n.planning_stats()['expanded_nodes'],8);n.end_turn()
 def test_preemption_cannot_produce_an_endless_zero_node_yield(self):
  n=base24.IncrementalNavigationTests().nav()
  with patch('navigation.time.thread_time',side_effect=[0]+[100]*20):
   n.begin_turn(expansions=512)
   with self.assertRaises(RoutePending):n.path((1050,1050),(6050,1050))
  self.assertGreaterEqual(n.planning_stats()['expanded_nodes'],32);n.end_turn()
 def test_all_two_hundred_delayed_jobs_make_progress_and_finish(self):
  for _ in range(200):
   n=base24.IncrementalNavigationTests().nav();done=False
   for turn in range(200):
    with patch('navigation.time.perf_counter',return_value=turn) as wall:
     n.begin_turn(expansions=256);wall.return_value=turn+10
     before=n.planning_stats()['expanded_nodes']
     try:
      path=n.path((1050,1050),(6050,1050));done=True
     except RoutePending:
      self.assertGreater(n.planning_stats()['expanded_nodes'],before)
     finally:n.end_turn()
    if done:break
   self.assertTrue(done);self.assertTrue(path)

class OpportunityTests(unittest.TestCase):
 def policy(self):
  w,p=base24.ProgressAndDeathTests().policy();w.own.values.update({0:6,1:200,31:200})
  p.region={'farms':{str(m):{'level':lv,'hp':hp,'points':[[223300,278700]],'drops':[]} for m,lv,hp in ((184,6,105),(119,7,165),(104,9,105),(999,35,3000))}}
  p.learning.selected={184};p.learning.signature=(6,0,tuple(sorted(w.own.equipment.items())),False);p.learning.until=10000
  p.learning.profile=PROFILES[0];p.last_target_at=0
  return w,p
 def mob(self,w,model=119):
  w.entities[1000]=Entity(model,1000,1001,5,1,w.own.x+100,w.own.y,40,{0:7 if model==119 else 35,1:100,31:100})
 def test_level_six_bot_uses_safe_visible_alternative_and_keeps_attacking(self):
  w,p=self.policy();self.mob(w);p.tick(100)
  self.assertEqual(p.target,1000);self.assertEqual(p.attacks,1);self.assertEqual(p.opportunity_model,119)
  w.entities[1000].values[1]=80;p.tick(101)
  self.assertEqual(p.target,1000);self.assertEqual(p.attacks,1)
 def test_known_danger_and_high_level_are_not_used_to_escape_idle(self):
  w,p=self.policy();self.mob(w);p.learning.avoid[119]=1000
  p.move_to=Mock(return_value=True);p.tick(100);self.assertIsNone(p.target)
  w,p=self.policy();self.mob(w,999);p.move_to=Mock(return_value=True);p.tick(100);self.assertIsNone(p.target)
 def test_nearby_normal_objective_has_priority(self):
  w,p=self.policy();self.mob(w);w.entities[1002]=Entity(184,1002,1003,5,1,w.own.x+130,w.own.y,40,{0:6,1:100,31:100})
  p.tick(100);self.assertEqual(p.target,1002);self.assertEqual(p.opportunity_targets,0)

class RevivalEpisodeTests(unittest.TestCase):
 def test_new_death_is_not_delayed_by_previous_death_retry_clock(self):
  w,p=base24.ProgressAndDeathTests().policy();w.own.values[1]=0
  p.tick(100);p.tick(104);self.assertEqual(p.revive_requests,1)
  w.own.values[1]=100;w.own.state=0;p.tick(105)
  w.own.values[1]=0;p.tick(106);p.tick(110)
  self.assertEqual(p.revive_requests,2)
  self.assertEqual(p.summary()['revival']['episodes'],2)
  self.assertEqual(p.summary()['revival']['confirmed_returns'],1)

class IdleProbeTests(unittest.TestCase):
 def test_level_six_bot_changes_species_when_fights_have_stopped(self):
  w,p=OpportunityTests().policy();l=p.learning;l.signature=None;l.rows={}
  first=l.choose(p.region,w.own,0)
  # Force an unchanged cached shortlist: 90s of no XP must still break it.
  l.until=10000
  changed=l.choose(p.region,w.own,91)
  self.assertNotEqual(first,changed);self.assertEqual(len(changed),1);self.assertEqual(l.idle_probes,1)
  self.assertEqual(l.choose(p.region,w.own,100),changed)
 def test_real_xp_gain_resets_the_idle_probe_clock(self):
  w,p=OpportunityTests().policy();l=p.learning;l.signature=None
  l.choose(p.region,w.own,0);w.own.values[15]=10;l.choose(p.region,w.own,80)
  l.choose(p.region,w.own,100);self.assertEqual(l.idle_probes,0)
 def test_idle_probe_respects_danger_cooldowns(self):
  w,p=OpportunityTests().policy();l=p.learning;l.signature=None;l.choose(p.region,w.own,0)
  l.avoid.update({119:1000,104:1000})
  chosen=l.choose(p.region,w.own,91);self.assertFalse({119,104}.intersection(chosen))

class InterruptedRouteTests(unittest.TestCase):
 def test_confirmed_death_discards_unfinished_old_approach(self):
  w,p=base24.ProgressAndDeathTests().policy();n=base24.IncrementalNavigationTests().nav();p.nav=n
  n.begin_turn(expansions=1)
  with self.assertRaises(RoutePending):n.path((1050,1050),(6050,1050))
  n.end_turn();self.assertTrue(n.local.searches)
  w.own.values[1]=0;p.tick(100)
  self.assertFalse(n.local.searches)

class ConsoleLoadTests(unittest.TestCase):
 def test_repeated_transitions_do_not_flood_shared_windows_console(self):
  w,p=base24.ProgressAndDeathTests().policy();p.tell=Mock()
  def decision(now):
   p.clock=now;p.change('ищет');p.change('планирует' if int(now)%2 else 'идёт')
  p._tick=decision
  for now in range(100):p.tick(now)
  self.assertLessEqual(p.tell.call_count,4);self.assertEqual(p.mode,'планирует')
 def test_intermediate_changes_do_not_reset_final_state_duration(self):
  w,p=base24.ProgressAndDeathTests().policy()
  def decision(now):p.clock=now;p.change('ищет');p.change('планирует')
  p._tick=decision;p.tick(100);p.tick(150)
  self.assertEqual(p.summary()['state_seconds'],50)
