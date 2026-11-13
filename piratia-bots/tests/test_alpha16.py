"""Regression for approach/strike, native dispatch, city preference and task-based leisure."""
import json,sys,struct,unittest,random
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from collections import Counter
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from classic_wire import string
from headless import Client,Report
from city_travel import CityTravel,home_city_for,TELEPORTERS
from activity_slots import ActivitySlots
from task_budget import TaskBudget
from public_chat import PublicChat,PublicBudget
from social import Social,ChatBudget,PHRASES
from help_player import HelpPlayer
from regions import Regions
from test_development import scene
import test_coordination as base

class CombatTests(unittest.TestCase):
 def policy(self):
  fixture=base.CohortCombatTests();fixture.nav=Regions(ROOT/'assets').nav('garner')
  return fixture.policy()
 def test_unarmed_does_not_strike_from_incorrect_attribute_range(self):
  w,p=self.policy();w.default_skill=25;w.own.values[43]=250;w.entities[1000].x=w.own.x+220
  self.assertEqual(p.attack_reach(w.entities[1000]),160)
  p.tick(100);self.assertEqual(p.attacks,0);self.assertGreater(p.moves,0)
 def test_bow_uses_native_range_instead_of_melee_cap(self):
  w,p=self.policy();w.default_skill=30;w.entities[1000].x=w.own.x+700
  p.tick(100);self.assertEqual(p.attacks,1);self.assertEqual(p.moves,0)
 def test_in_range_stops_route_then_waits_for_ack_before_strike(self):
  w,p=self.policy();p.move_to((223300,278700),99);p.move_until=101;w.move_revision=1;w.move_state=0
  p.tick(100);self.assertEqual(p.attacks,0);p.send.assert_called_with(7,b'')
  p.tick(100.1);self.assertEqual(p.attacks,0)
  w.stop_revision+=1;w.stop_packet_number=p.last_sent_sequence;w.stop_packet_kind=1
  p.tick(100.3);self.assertEqual(p.attacks,1)
 def test_native_failed_action_reason_is_recorded(self):
  w,p=self.policy();w.observe(520,struct.pack('>IBB',w.own_id,2,1))
  self.assertEqual(w.summary()['last_failed_action'],{'actor':w.own_id,'action':2,'reason':1})
 def test_stall_responses_reach_handler_in_actual_client_dispatch(self):
  client=Client(Mock(),Report());client.world_handler=Mock()
  for cmd in (854,856,857,858,859):client.service(cmd,b'payload')
  self.assertEqual(client.world_handler.call_count,5)

class PopulationTests(unittest.TestCase):
 def test_200_home_preferences_and_market_rest_quotas(self):
  self.assertEqual(Counter(home_city_for(i) for i in range(1,201)),{'garner':150,'magicsea':25,'darkblue':25})
  r=Regions(ROOT/'assets',200)
  self.assertEqual(r.market_directory.city_limits,{'garner':15,'magicsea':3,'darkblue':2})
  self.assertEqual(r.rest_directory.limit,20)
  for i in range(200):r.directory.update(str(i),i,'garner',(0,0),1,0)
  got=[r.rest_directory.acquire(str(i),0) for i in range(200)];self.assertEqual(sum(got),20)
  r.rest_directory.release('0');self.assertTrue(r.rest_directory.acquire('other',1))
 def test_optional_npc_detour_yields_to_farm_after_no_progress(self):
  b=TaskBudget();f=SimpleNamespace(context=None,pending=None)
  self.assertTrue(b.track('npc',f,True,(100,100),0))
  self.assertFalse(b.track('npc',f,True,(100,100),36));self.assertFalse(b.allow('npc',100))
  self.assertTrue(b.allow('npc',217))
 def test_no_completed_tasks_means_no_scheduled_rest(self):
  from town import Town
  from life import LifeItems
  from equipment import ItemCatalog
  w=scene();w.bag_ready=False;t=Town(w,LifeItems(ROOT/'assets'),ItemCatalog(ROOT/'assets/items.json'),{},random.Random(1),w.own.position)
  p=Mock();p.position.return_value=w.own.position;t.note_progress(0,0)
  from navigation import Navigation
  p.nav=Navigation(ROOT/'assets/argent-navigation.json')
  for now in (1,1000,10000):t.tick(now,p,True)
  self.assertEqual(t.breaks,0);self.assertEqual(t.rest_until,0)
  t.note_progress(12,0);t.tick(10001,p,True);t.tick(10002,p,True);self.assertEqual(t.breaks,1)
 def test_trainer_trip_overrides_home_without_changing_class(self):
  w=scene();role={'first_job':2};t=CityTravel(w,Mock(),1,role);p=SimpleNamespace(career=None)
  self.assertEqual(t.destination(p),'garner');w.own.values[0]=9
  self.assertEqual(t.destination(p),'darkblue');w.own.values[4]=2;self.assertEqual(t.destination(p),'garner')
 def test_teleport_only_from_live_menu_and_actual_map_confirms(self):
  w=scene();w.map='magicsea';w.own.values[0]=10;send=Mock();t=CityTravel(w,send,1,{'first_job':1})
  t.target='garner';t.context=(77,'menu',10)
  def menu(labels,page):return struct.pack('>IB',77,page)+string('Teleporter')+bytes([len(labels)])+b''.join(string(x) for x in labels)
  t.observe(802,menu(['Go to Argent City!','Go to Icicle City!'],18),1)
  self.assertEqual(t.context[1],'confirm');self.assertEqual(t.arrivals,0)
  t.observe(802,menu(['Teleport','Cancel'],4),2);self.assertEqual(t.context[1],'map');self.assertEqual(t.arrivals,0)
  w.map='garner';t.on_map(3);self.assertEqual(t.arrivals,1)

class ChatHelpTests(unittest.TestCase):
 def test_589_unique_phrases_and_50_real_echo_dialogue_scripts(self):
  rows=[x for v in PHRASES.values() for x in v];self.assertEqual(len(rows),589);self.assertEqual(len(set(rows)),589)
  self.assertEqual(len(json.loads((ROOT/'assets/bot-dialogues.json').read_text())),50)
 def test_shared_local_chat_at_most_one_message_per_two_seconds(self):
  b=ChatBudget(2);self.assertTrue(b.claim(0));self.assertFalse(b.claim(1));self.assertTrue(b.claim(2))
 def test_public_chat_requires_real_money_and_trade_requires_open_stock(self):
  w=scene();send=Mock();c=PublicChat(w,send,PublicBudget(),'test');c.next_world=c.next_trade=0
  c.tick(10,True);send.assert_not_called();w.own.values[8]=25000
  c.tick(11,True);self.assertEqual(send.call_args.args[0],6402)
  c.tick(12,True,SimpleNamespace(state='selling',stock=[1]));self.assertEqual(send.call_args.args[0],6401)
 def test_public_success_requires_server_echo_of_own_request(self):
  w=scene();w.own.values[8]=25000;c=PublicChat(w,Mock(),PublicBudget(),'echo');c.next_world=c.next_trade=0
  c.tick(1,True);text=c.pending[5402][0]
  c.observe(5402,string('Other')+string(text),2);self.assertEqual(c.confirmed_world,0)
  c.observe(5402,string(w.own.name)+string(text),3);self.assertEqual(c.confirmed_world,1)
 def test_public_budget_bounded_across_two_hundred_workers(self):
  b=PublicBudget();self.assertEqual(sum(b.claim('world',0) for _ in range(200)),1)
  self.assertFalse(b.claim('world',119));self.assertTrue(b.claim('world',120))
 def test_help_is_explicit_nearby_and_refuses_busy_bot(self):
  w=scene();w.entities[2].values={1:100,31:100};h=HelpPlayer(w)
  p=SimpleNamespace(target=None,resting=False,market=None,travel=None,adventure=None,story=None,career=None,town=None,position=lambda now:w.own.position)
  self.assertIn('Иду',h.request(2,0,p));self.assertTrue(h.active(1))
  p.target=99;self.assertIn('занят',h.request(2,2,p))
 def test_help_request_routes_to_real_handler_after_single_responder_claim(self):
  w=scene();send=Mock();s=Social(w,send,w.own.name,ChatBudget(2),'help');s.help_handler=Mock(return_value='Иду к тебе.')
  s.hear(2,w.own.name+' помоги',0);s.help_handler.assert_called_once_with(2,0)
  s.tick(6,False,True);self.assertEqual(send.call_args.args[0],1)

if __name__=='__main__':unittest.main()
