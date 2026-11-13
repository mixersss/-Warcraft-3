"""Report-independent reproductions of empty starter alternatives and stale wait status."""
import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from farm_plan import HuntLearning,PROFILES
from test_development import scene
from navigation import Navigation
import test_coordination as base

class StarterFallbackTests(unittest.TestCase):
 def test_every_profile_has_checked_alternative_after_failed_forest_trial(self):
  world=scene();world.own.values.update({0:1,1:100,31:100})
  region=json.loads((ROOT/'assets/regions.json').read_text())['garner']
  for profile in PROFILES:
   with self.subTest(profile=profile[0]):
    learning=HuntLearning('probe');learning.profile=profile;learning.avoid[103]=500
    choices=learning.choose(region,world.own,100)
    self.assertTrue(choices);self.assertNotIn(103,choices);self.assertNotIn(75,choices)
 def test_fallback_does_not_ignore_actual_danger_cooldowns(self):
  world=scene();world.own.values.update({0:1,1:100,31:100})
  region=json.loads((ROOT/'assets/regions.json').read_text())['garner']
  learning=HuntLearning('probe');learning.profile=PROFILES[0]
  learning.avoid={int(model):500 for model in region['farms']}
  self.assertEqual(learning.choose(region,world.own,100),set())

class StatusTests(unittest.TestCase):
 def test_flushed_movement_is_not_reported_as_still_waiting(self):
  f=base.CohortCombatTests();f.nav=Navigation(ROOT/'assets/argent-navigation.json');world,policy=f.policy(monsters=0)
  policy.move_to((223800,278700),100);policy.move_to((224000,278700),101)
  self.assertIsNotNone(policy.pending_action)
  policy.tick(101.1);self.assertEqual(policy.mode,'ожидание завершения предыдущего действия')
  world.stop_revision+=1;world.stop_packet_number=policy.last_sent_sequence;world.stop_packet_kind=1
  policy.tick(101.4)
  self.assertIsNone(policy.pending_action);self.assertEqual(policy.mode,'маршрут отправлен')
  self.assertFalse(policy.summary()['action_wait']['pending'])


class PracticalTrialsTests(unittest.TestCase):
 def make(self):
  world=scene();world.own.values.update({0:1,1:100,31:100})
  region=json.loads((ROOT/'assets/regions.json').read_text())['garner']
  learning=HuntLearning('practice');learning.profile=PROFILES[0]
  from farm_plan import FIELDS
  learning.rows['103']={k:0 for k in FIELDS};learning.rows['103'].update(wins=1,seconds=20,xp=4)
  return world,region,learning
 def test_first_completed_fight_is_followed_by_an_unfamiliar_trial(self):
  world,region,learning=self.make();selected=learning.choose(region,world.own,100)
  self.assertEqual(len(selected),1);self.assertNotIn(103,selected);self.assertTrue(learning.probing)
 def test_trial_is_stable_then_unseen_route_is_not_repeated_immediately(self):
  world,region,learning=self.make();first=learning.choose(region,world.own,100)
  self.assertEqual(learning.choose(region,world.own,110),first)
  second=learning.choose(region,world.own,180)
  self.assertTrue(second);self.assertFalse(first.intersection(second))
 def test_forest_is_only_initial_preference_not_a_permanent_hunter_lock(self):
  f=base.CohortCombatTests();f.nav=Navigation(ROOT/'assets/argent-navigation.json');world,policy=f.policy(monsters=0)
  world.own.values[0]=1;policy.region=json.loads((ROOT/'assets/regions.json').read_text())['garner']
  self.assertEqual(policy.starter_models(),{103})
  _,_,learning=self.make();policy.learning=learning;policy.clock=100
  self.assertFalse(policy.starter_models());self.assertNotIn(103,policy.planned_models())

class RecoveryAndLeisureTests(unittest.TestCase):
 def test_revive_requests_continue_after_backoff_without_faking_health(self):
  f=base.CohortCombatTests();f.nav=Navigation(ROOT/'assets/argent-navigation.json');world,policy=f.policy(monsters=0)
  world.own.values[1]=0
  for now in (100,108,138,168,200):policy.tick(now)
  self.assertEqual(policy.revive_requests,3);policy.tick(300);self.assertEqual(policy.revive_requests,4)
  self.assertEqual(world.own.values[1],0)
  world.own.values[1]=100;world.own.state=1;policy.tick(301)
  self.assertIsNone(policy.dead_since);self.assertEqual(policy.death_attempts,0)
 def town(self,seed):
  from town import Town
  from life import LifeItems
  from equipment import ItemCatalog
  from types import SimpleNamespace
  from unittest.mock import Mock
  import random
  world=scene();nav=Navigation(ROOT/'assets/argent-navigation.json')
  town=Town(world,LifeItems(ROOT/'assets'),ItemCatalog(ROOT/'assets/items.json'),{},random.Random(seed),world.own.position)
  policy=SimpleNamespace(nav=nav,position=lambda now:world.own.position,move_to=Mock(return_value=True))
  town.rest_until=1000;return world,town,policy
 def test_leisure_uses_different_checked_destinations_instead_of_home_pile(self):
  goals=[]
  for seed in (1,2):
   world,town,policy=self.town(seed);self.assertTrue(town.tick(1,policy,True))
   self.assertNotEqual(town.rest_goal,town.home);self.assertTrue(policy.nav.path(world.own.position,town.rest_goal));goals.append(town.rest_goal)
  self.assertNotEqual(*goals)
 def test_leisure_walk_has_brief_stops_and_returns_to_work(self):
  world,town,policy=self.town(1);town.tick(1,policy,True);world.own.x,world.own.y=town.rest_goal
  town.tick(2,policy,True);self.assertEqual(town.walk_stops,1)
  town.next_shop=1000;self.assertFalse(town.tick(200,policy,True));self.assertEqual(town.rest_until,0)

class StallAndSpeechTests(unittest.TestCase):
 def test_stall_cannot_open_if_skill_is_missing_at_arrival(self):
  from test_market import MarketTests
  fixture=MarketTests();world,send,market,policy=fixture.make()
  market.state='travelling';market.deadline=100;market.pitch=world.own.position
  market.tick(1,policy,True)
  self.assertFalse(any(call.args[0]==330 for call in send.call_args_list))
 def test_eleventh_stall_pitch_does_not_reuse_first_pitch(self):
  from test_market import MarketTests
  points=[]
  for slot in (0,10):
   fixture=MarketTests();world,send,market,policy=fixture.make()
   world.skills[241]={'level':1};world.bag={0:fixture.item()};market.next_shift=0
   from unittest.mock import Mock
   market.directory.reserve=Mock(return_value=slot)
   policy.nav.nearest.return_value=(world.own.x+1000,world.own.y)
   market.tick(1,policy,True);points.append(policy.nav.nearest.call_args.args[0])
  self.assertNotEqual(*points)
 def test_runtime_context_mode_does_not_fill_chat_with_random_lines(self):
  from social import Social,ChatBudget
  from unittest.mock import Mock
  import dataclasses
  world=scene();world.entities[77]=dataclasses.replace(world.own,identity=77,name='Human')
  send=Mock();social=Social(world,send,'Bot00000001',ChatBudget(2),'seed');social.context_provider=lambda:None
  social.next_send=0;social.next_situation=0;social.tick(100,False,True);send.assert_not_called()
 def test_bot_congratulates_only_server_observed_peer_level(self):
  from test_alpha21 import CooperativeTests
  world,policy,social,person,coop=CooperativeTests().make()
  coop.directory.rows['Bot00000001']['level']=4
  self.assertFalse(coop.hear(77,social.name+', поднял 5 уровень.',101))
  self.assertTrue(coop.hear(77,social.name+', поднял 4 уровень.',102));self.assertTrue(social.urgent)

class RewardObservationTests(unittest.TestCase):
 def make(self):
  import dataclasses
  world=scene();target=dataclasses.replace(world.own,identity=88,control=5,model=103,values={0:3,1:69,31:69})
  world.entities[88]=target;world.own.values[15]=10
  learning=HuntLearning('reward');learning.begin(world,target,100)
  return world,target,learning
 def test_xp_following_death_packet_is_included_in_learning(self):
  world,target,learning=self.make();target.values[1]=0;world.own_hits[88]=(101,True)
  learning.observe(world,101);self.assertTrue(learning.waiting_reward(101));self.assertFalse(learning.rows)
  world.own.values[15]=14;learning.observe(world,101.5)
  self.assertEqual(learning.rows['103']['xp'],4);self.assertEqual(learning.rows['103']['dry_wins'],0)
 def test_old_death_credit_cannot_reward_new_alive_instance(self):
  world,target,learning=self.make();world.own_hits[88]=(80,True);learning.observe(world,102)
  self.assertFalse(learning.waiting_reward(102));self.assertFalse(learning.rows)


class PublicContextTests(unittest.TestCase):
 def test_no_context_means_no_random_world_or_trade_broadcast(self):
  from public_chat import PublicChat,PublicBudget
  from unittest.mock import Mock
  world=scene();world.own.values[8]=100000;send=Mock()
  chat=PublicChat(world,send,PublicBudget(),'test');chat.context_provider=lambda channel:None
  chat.next_world=chat.next_trade=0;chat.tick(100,True);send.assert_not_called()

if __name__=='__main__':unittest.main()
