"""Adaptive real-progress learning, actual contacts and consensual in-world assistance."""
import dataclasses,json,struct,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from farm_plan import HuntLearning,PROFILES
from personality import Personality
from contacts import Contacts,private_request
from classic_wire import string,Reader
from headless import Client,Report
from party import Party,BotDirectory
from social import Social,ChatBudget
from coordination import Coordination
from cooperation import Cooperation,HelpDirectory
from help_player import HelpPlayer
from show_levels import render
from test_development import scene
import test_coordination as base
from navigation import Navigation
from city_travel import CityTravel
from test_adventure import role

class LearningTests(unittest.TestCase):
 def make(self):
  w=scene();w.own.values.update({0:10,1:100,31:100,15:10,8:20});l=HuntLearning('test');l.profile=PROFILES[1]
  t=dataclasses.replace(w.own,identity=88,control=5,model=103,values={0:3,1:69,31:69});w.entities[88]=t
  return w,l,t
 def test_choice_is_not_pinned_to_own_monster_level(self):
  w,l,t=self.make();r={'farms':{str(i):{'level':lv,'hp':hp,'points':[[100,100]],'drops':[]} for i,lv,hp in ((1,8,25),(2,10,120),(3,12,40))}}
  self.assertEqual(l.choose(r,w.own,0),{1,2,3})
 def test_danger_changes_preference_without_modifying_real_stats(self):
  w,l,t=self.make();l.begin(w,t,0);w.own.values[1]=30;before=dict(w.own.values);l.observe(w,2)
  self.assertEqual(l.rows['103']['losses'],1);self.assertTrue(l.blocked(103,3));self.assertEqual(w.own.values,before)
 def test_death_is_a_dangerous_fight(self):
  w,l,t=self.make();l.begin(w,t,0);w.own.values[1]=0;l.observe(w,3)
  self.assertEqual(l.rows['103']['losses'],1)
 def test_only_observed_credited_death_counts_as_success(self):
  w,l,t=self.make();l.begin(w,t,0);t.values[1]=0;l.observe(w,2);self.assertFalse(l.rows)
  w.own_hits[88]=(2,True);w.own.values[15]=14;l.observe(w,3)
  self.assertEqual(l.rows['103']['wins'],1);self.assertEqual(l.rows['103']['xp'],4)
 def test_party_credited_win_without_xp_is_not_invented_xp(self):
  w,l,t=self.make();l.begin(w,t,0);t.values[1]=0;w.own_hits[88]=(2,True);l.observe(w,3)
  self.assertEqual(l.rows['103']['xp'],0);self.assertEqual(l.rows['103']['wins'],1)
 def test_stalled_battle_gets_a_bounded_cooldown(self):
  w,l,t=self.make();l.begin(w,t,0);l.finish(w,15,'stalled')
  self.assertTrue(l.blocked(103,20));self.assertFalse(l.blocked(103,106))
 def test_persistent_learning_has_no_character_name_or_credentials(self):
  w,l,t=self.make()
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'learning.json';l.load(p);l.begin(w,t,0);l.finish(w,10,'stalled');l.save(70)
   text=p.read_text();self.assertNotIn('password',text);self.assertNotIn('test',text)
   other=HuntLearning('test');other.load(p);self.assertEqual(other.rows['103']['stalls'],1)
 def test_broken_or_nonfinite_learning_does_not_kill_session(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'bad.json';p.write_text('{broken');l=HuntLearning(1);l.load(p);self.assertEqual(l.rows,{})
   p.write_text(json.dumps({'version':1,'models':{'103':{'wins':float('nan')}}}));l.load(p);self.assertEqual(l.rows,{})
 def test_new_gear_reopens_previously_dangerous_trials(self):
  w,l,t=self.make();r={'farms':{'103':{'level':3,'hp':69,'drops':[],'points':[[100,100]]}}}
  l.choose(r,w.own,0);l.avoid[103]=500;w.own.equipment[9]=9
  self.assertIn(103,l.choose(r,w.own,10))
 def test_distinct_stable_styles_exist_in_population(self):
  self.assertEqual(HuntLearning('same').profile,HuntLearning('same').profile)
  self.assertEqual(len({HuntLearning(i).profile[0] for i in range(200)}),6)

class PlanIntegrationTests(unittest.TestCase):
 def make(self):
  f=base.CohortCombatTests();f.nav=Navigation(ROOT/'assets/argent-navigation.json');w,p=f.policy(monsters=0)
  p.region=json.loads((ROOT/'assets/regions.json').read_text())['garner'];return w,p
 def test_level_gain_discards_old_route_lease(self):
  w,p=self.make();p.coordination=Coordination();p.refresh_farm_plan()
  old=(223250,267550);p.search_goal=old;p.coordination.choose_zone(p.owner,'garner',[old],100)
  w.own.values[0]=4;p.clock=101;p.refresh_farm_plan()
  self.assertIsNone(p.search_goal);self.assertNotIn(p.owner,p.coordination.zones);self.assertEqual(p.farm_plan_changes,1)
 def test_filter_and_routes_use_same_selected_models(self):
  w,p=self.make();w.own.values[0]=6;p.clock=100;models=p.planned_models()
  self.assertTrue(models)
  for model in models:
   rec=p.region['farms'][str(model)];e=dataclasses.replace(w.own,control=5,identity=model+1000,model=model,handle=99,values={0:rec['level'],1:rec['hp'],31:rec['hp']})
   self.assertTrue(p.eligible(e,100))
 def test_first_class_travel_wins_over_home_preference(self):
  w,p=self.make();w.own.values.update({0:9,4:0})
  for first,city in ((1,'garner'),(2,'darkblue'),(4,'garner'),(5,'magicsea')):
   travel=CityTravel(w,Mock(),1,role(first));self.assertEqual(travel.destination(p),city)
 def test_mandatory_class_objective_is_not_replaced_by_adaptive_probe(self):
  w,p=self.make();w.own.values.update({0:10,4:0});p.clock=100;p.activity.force_until=500
  p.adventure=SimpleNamespace(farm=lambda:(237,None),desired_models=lambda:{237})
  self.assertTrue(p.mandatory_work());self.assertEqual(p.planned_models(),{237})

class ContactTests(unittest.TestCase):
 def make(self):
  w=scene();send=Mock();s=Social(w,send,'Bot00000001',ChatBudget(2),'bot')
  person=Personality('bot');s.personality=person;directory=BotDirectory();directory.update(s.name,1,w.map,w.own.position,1,0)
  p=Party(w,send,s.name,1,directory);p.personality=person
  return w,send,s,p,Contacts(w,send,s,person,p)
 def test_real_private_reply_is_delayed_and_addressed_to_sender(self):
  w,send,s,p,c=self.make();c.hear(5403,string('Human')+string(s.name)+string('какой уровень?')+bytes(4),0)
  send.assert_not_called();c.tick(6);command,payload=send.call_args.args
  self.assertEqual(command,6403);r=Reader(payload);self.assertEqual(r.string(),'Human');self.assertIn(str(w.own.values[0]),r.string());r.end()
 def test_private_bot_echo_cannot_create_reply_loop(self):
  w,send,s,p,c=self.make();c.hear(5403,string('Bot00000002')+string(s.name)+string('привет'),0);c.tick(6);send.assert_not_called()
 def test_friend_request_is_native_invitation_not_fake_confirmation(self):
  w,send,s,p,c=self.make();c.invite_friend('Human',0);send.assert_called_once_with(6011,string('Human'));self.assertEqual(c.friend_refreshes,0)
 def test_incoming_human_friend_invitation_is_accepted(self):
  w,send,s,p,c=self.make();c.hear(5011,string('Human')+struct.pack('>IH',77,0),0);send.assert_called_once_with(6012,struct.pack('>I',77))
 def test_malformed_private_message_is_isolated(self):
  w,send,s,p,c=self.make();c.hear(5403,b'\0',0);self.assertEqual(c.unsupported,1);send.assert_not_called()
 def test_human_party_request_waits_for_server_membership(self):
  w,send,s,p,c=self.make();p.request_name('Human',0);send.assert_called_once_with(6001,string('Human'));self.assertEqual(p.members,())
  packet=bytes([0,2])+struct.pack('>I',1)+string(s.name)+string('')+bytes(2)+struct.pack('>I',77)+string('Human')+string('')+bytes(2)
  p.observe(5002,packet,1);self.assertEqual(p.members,(s.name,'Human'));self.assertIsNone(p.session_until)
 def test_full_party_does_not_send_another_invitation(self):
  w,send,s,p,c=self.make();p.members=(s.name,'a','b','c','d');self.assertIn('полная',p.request_name('Human',0));send.assert_not_called()
 def test_actual_client_dispatch_routes_contact_events(self):
  handler=Mock();client=Client(Mock(),Report());client.world_handler=handler
  for command in (5011,5012,5403):client.service(command,b'')
  self.assertEqual(handler.call_count,3)
 def test_private_packet_format_is_two_native_strings(self):
  self.assertEqual(private_request('Human','Привет'),string('Human')+string('Привет'))

class CooperativeTests(unittest.TestCase):
 def make(self):
  f=base.CohortCombatTests();f.nav=Navigation(ROOT/'assets/argent-navigation.json');w,p=f.policy()
  p.owner='Bot00000002';p.helper=HelpPlayer(w);p.coordination=Coordination()
  source=dataclasses.replace(w.own,identity=77,name='Bot00000001');w.entities[77]=source
  social=Social(w,p.send,p.owner,ChatBudget(2),p.owner);person=Personality(p.owner);person.help_chance=1
  directory=HelpDirectory();directory.register(source.name,{'identity':77,'map':w.map,'position':source.position,'target':1000,'handle':2000,'until':200})
  p.coordination.claim(source.name,(w.map,1000,2000),100)
  return w,p,social,person,Cooperation(w,p,social,person,directory)
 def test_help_needs_real_received_request_before_any_action(self):
  w,p,s,person,c=self.make();self.assertIsNone(p.helper.source)
  self.assertTrue(c.hear(77,s.name+', помоги с мобом!',101));self.assertEqual(p.helper.source,77)
  self.assertTrue(p.coordination.claim(p.owner,(w.map,1000,2000),102))
  self.assertFalse(p.coordination.claim('uninvited',(w.map,1000,2000),102))
 def test_busy_bot_refuses_and_keeps_own_task(self):
  w,p,s,person,c=self.make();p.target=1000;c.hear(77,s.name+', помоги с мобом!',101)
  self.assertIsNone(p.helper.source);self.assertEqual(c.refusals,1);self.assertTrue(s.urgent)
 def test_unhelpful_personality_can_decline_when_free(self):
  w,p,s,person,c=self.make();person.help_chance=0;c.hear(77,s.name+', помоги с мобом!',101)
  self.assertIsNone(p.helper.source);self.assertEqual(c.refusals,1)
 def test_unregistered_source_cannot_redirect_bot(self):
  w,p,s,person,c=self.make();w.entities[77].name='Human'
  self.assertFalse(c.hear(77,s.name+', помоги с мобом!',101));self.assertIsNone(p.helper.source)
 def test_help_target_reaches_actual_attack_policy(self):
  w,p,s,person,c=self.make();c.hear(77,s.name+', помоги с мобом!',101);p.tick(102)
  self.assertEqual(p.target,1000);self.assertEqual(p.attacks,1)
 def test_repeated_echo_does_not_duplicate_help(self):
  w,p,s,person,c=self.make();line=s.name+', помоги с мобом!';c.hear(77,line,101);c.hear(77,line,102)
  self.assertEqual(c.accepts,1)
 def test_same_seed_keeps_personality_after_restart(self):
  self.assertEqual(Personality('same').kind,Personality('same').kind)
 def test_status_view_explains_levels_without_player_names(self):
  text=render({'connected':1,'requested':200,'bots':{'1':{'level':7,'experience':19,'attacks':4,'state':'охота'}}})
  self.assertIn('Уровень',text);self.assertIn('19',text);self.assertNotIn('password',text)

if __name__=='__main__':unittest.main()
