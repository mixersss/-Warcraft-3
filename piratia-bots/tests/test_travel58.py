"""Travel must produce native movement/payment evidence, never simulated arrivals."""
import copy
import dataclasses
import json
import struct
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import test_mechanics as source
from hunt_travel import HuntTravel
from xp_boosters import XPBoosters
from economy import role_for
from classic_wire import string

class Travel58Tests(unittest.TestCase):
 def make(self):
  w=source.actor();w.own.values.update({0:35,1:1200,2:100,31:1200,32:100});w.map='garner';w.items={}
  w.bag={0:source.item(4602)}
  data={'birthplaces':{'Argent City':{'points':[[223100,278800]]}},'island_nodes':[],'tickets':[],'entrances':[]}
  regions=SimpleNamespace(hunting_travel_data=data,mob_knowledge=source.MOBS,map_catalog={'garner':{},'eastgoaf':{}},hunting_arrival_camps=lambda name,p:{295:((0,p),)},mine_exit_step=lambda *a:None,mine_exit_steps={})
  c=HuntTravel(w,regions,source.LIFE,SimpleNamespace(phase=lambda *a:'progression'),Mock(),'Bot58')
  p=SimpleNamespace(sequence=3,emit=Mock(),position=lambda now:w.own.position,nav=SimpleNamespace(nearest=lambda point,radius:point),move_to=Mock(return_value=True),learning=SimpleNamespace(last_progress_at=None),camp_route_active=lambda now:False,hunt_before_errands=lambda now:False)
  c.needs_town=lambda *a:False
  return w,c,p
 def plan(self,w,kind='portal'):
  return {'kind':kind,'map':'garner','position':list(w.own.position),'to_map':'garner','arrival_cm':[326000,328000],'fare':2000 if kind=='portal' else 0,'label':'Go to Zephyr Isle!','name':'Zephyr','model':None}
 def test_same_map_portal_requires_visible_npc_menu_payment_and_position(self):
  w,c,p=self.make();c.plan=self.plan(w);c.target_started=100
  w.entities[77]=dataclasses.replace(w.own,identity=77,control=2)
  self.assertTrue(c.tick(100,p,True));self.assertEqual(c.context['npc'],77)
  def menu(label):return struct.pack('>IB',77,1)+string('Transport')+b'\1'+string(label)
  c.observe(802,menu('Go to Zephyr Isle!'),100.1);c.observe(802,menu('Teleport'),100.2)
  c.tick(100.3,p,True);self.assertEqual(c.confirmed,0)
  w.own.x,w.own.y=326000,328000;c.tick(100.4,p,True);self.assertEqual(c.confirmed,0)
  w.own.values[8]-=2000;c.tick(100.5,p,True);self.assertEqual(c.confirmed,1)
 def test_ticket_requires_actual_consumption_and_native_arrival(self):
  w,c,p=self.make();c.plan=dict(self.plan(w,'ticket'),item_id=4602);c.target_started=100
  w.bag={4:source.item(4602)}
  self.assertTrue(c.tick(100,p,True));self.assertEqual(p.emit.call_args.args[0][8:],struct.pack('>Bhh',11,4,-1))
  w.own.x,w.own.y=326000,328000;c.tick(100.1,p,True);self.assertEqual(c.confirmed,0)
  w.bag={};c.tick(100.2,p,True);self.assertEqual(c.confirmed,1)
 def test_paid_arrival_defers_optional_city_return_until_progress_or_deadline(self):
  w,c,p=self.make()
  del c.needs_town
  w.bag_capacity=48
  w.bag[4]=source.item(3057)
  c.life=SimpleNamespace(services={'shops':{}},prices={})
  c.plan=dict(self.plan(w,'ticket'),item_id=3057,to_map='eastgoaf',model=295)
  c.target_started=100
  self.assertTrue(c.tick(100,p,True))
  w.map='eastgoaf'
  w.own.x,w.own.y=326000,328000
  w.bag.pop(4)
  c.tick(101,p,True)
  self.assertEqual(c.confirmed,1)
  p.crafting=SimpleNamespace(due=lambda now:True,goals=[1],op=None)
  self.assertFalse(c.needs_town(p,102))
  c.choose=Mock()
  self.assertFalse(c.tick(102,p,True))
  c.choose.assert_not_called()
  p.owner_services=SimpleNamespace(need=lambda:True)
  self.assertTrue(c.needs_town(p,102))
  p.owner_services=None
  self.assertTrue(c.needs_town(p,281))
  p.learning.last_progress_at=103
  self.assertTrue(c.needs_town(p,104))

 def test_trade_window_cannot_replace_an_active_walk_with_argent_return(self):
  from economy import Economy
  from test_coordination import CohortCombatTests
  CohortCombatTests.setUpClass()
  w,p=CohortCombatTests().policy(monsters=0)
  w.own.values.update({0:32,4:2})
  w.own.x,w.own.y=198751,266614
  w.bag_ready=True;w.bag_capacity=48;w.bag={0:source.item(4602)}
  p.search_goal=(155150,266150)
  p.search_deadline=250
  _,c,_=self.make()
  del c.needs_town
  c.world=w
  p.economy=c.economy=Economy('test',ROOT/'assets')
  p.economy.cycle=0;p.economy.offset=0;p.economy.stages=[('trade',1800)]
  p.market=SimpleNamespace(offers=lambda policy:[1])
  self.assertEqual(c.economy.phase(w,100),'trade')
  self.assertFalse(c.needs_town(p,100))
  self.assertFalse(c.tick(100,p,True))
  self.assertIsNone(c.plan)
  p.owner_services=SimpleNamespace(need=lambda:True)
  self.assertTrue(c.needs_town(p,100))
  p.owner_services=None
  self.assertTrue(c.needs_town(p,250))

 def test_expired_camp_route_does_not_send_an_xp_starved_bot_back_to_argent(self):
  from test_coordination import CohortCombatTests
  CohortCombatTests.setUpClass()
  w,p=CohortCombatTests().policy(monsters=0)
  w.own.values.update({0:32,4:2})
  w.own.x,w.own.y=198751,266614
  w.bag_ready=True;w.bag_capacity=48;w.bag={0:source.item(4602)}
  p.fast_progression=True
  p.region={'farms':{}}
  p.search_goal=(155150,266150)
  p.search_deadline=940
  p.learning.last_progress_at=10
  _,c,_=self.make()
  del c.needs_town
  c.world=w
  p.market=SimpleNamespace(offers=lambda policy:[1])
  c.economy.phase=lambda *a:'trade'
  c.plan=dict(self.plan(w,'ticket'),item_id=4602,returning=True)
  p.emit=Mock()
  self.assertFalse(p.camp_route_active(941))
  self.assertTrue(p.hunt_before_errands(941))
  self.assertFalse(c.tick(941,p,True))
  self.assertIsNone(c.plan)
  p.emit.assert_not_called()
  w.bag_capacity=1
  self.assertTrue(c.needs_town(p,941))
  w.bag_capacity=48
  p.learning.last_progress_at=942
  self.assertTrue(c.needs_town(p,943))
  p.learning.last_progress_at=10
  c.economy.phase=lambda *a:'progression'
  c.choose=Mock(return_value=None)
  self.assertFalse(c.tick(1010,p,True))
  c.choose.assert_called_once_with(1010,p,False)

 def test_event_requires_visible_matching_native_identity_and_exact_action(self):
  w,c,p=self.make();c.plan=dict(self.plan(w,'event'),event_id=6,event_model=193,model=295);c.target_started=100
  entity=dataclasses.replace(w.own,identity=88,model=193,handle=900,event_identity=88,event_id=6)
  w.entities[88]=entity;self.assertTrue(c.tick(100,p,True))
  self.assertEqual(p.emit.call_args.args[0][8:],struct.pack('>BIIH',18,88,900,6));self.assertEqual(c.confirmed,0)
 def test_closed_event_is_released_to_normal_hunting_without_fake_move(self):
  w,c,p=self.make();c.plan=dict(self.plan(w,'event'),event_id=6,event_model=193,model=295);c.target_started=100
  self.assertFalse(c.tick(100,p,True));self.assertIsNone(c.plan);p.emit.assert_not_called();self.assertTrue(c.blocked)
 def test_far_trip_needs_owned_return_ticket_even_for_portals(self):
  w,c,p=self.make();c.routes=lambda *a:[self.plan(w)];c.nearby=lambda *a:[(295,0)];c.rate=lambda *a:1
  w.bag={}
  c.plan=c.choose(100,p);self.assertIsNotNone(c.plan);c.target_started=100
  self.assertFalse(c.tick(100,p,True));p.emit.assert_not_called();c.send.assert_not_called()
  w.bag={0:source.item(4602)};self.assertIsNotNone(c.choose(100,p))
 def test_real_mine_ticket_landing_rejects_camps_across_disconnected_land(self):
  from regions import Regions
  w,c,p=self.make()
  regions=Regions(ROOT/'assets',400)
  regions.full_regions=True
  c.regions=regions
  bad=dict(self.plan(w,'ticket'),item_id=3847,arrival_cm=(164200,269800))
  good=dict(self.plan(w,'event'),to_map='eastgoaf',arrival_cm=(11623,3330))
  nav=regions.nav('garner')
  self.assertNotEqual(nav.land_component(bad['arrival_cm']),nav.land_component((223100,278800)))
  self.assertFalse(regions.hunting_arrival_sites('garner',bad['arrival_cm']))
  self.assertIn(99,regions.hunting_arrival_sites('eastgoaf',good['arrival_cm']))
  c.routes=lambda *a:[bad,good]
  c.nearby=lambda map_name,point:[(225,0)] if map_name=='garner' else [(99,10521)]
  c.rate=lambda model,*a:1 if model==99 else 0
  self.assertEqual(c.choose(100,p)['model'],99)
  c.routes=lambda *a:[dict(good,arrival_options=[good['arrival_cm'],(0,0)])]
  self.assertIsNone(c.choose(100,p))
 def test_detached_mine_exits_by_four_confirmed_native_events_without_ticket(self):
  from regions import Regions
  w,c,p=self.make()
  c.regions=Regions(ROOT/'assets',400)
  w.bag={}
  w.bag_ready=True
  w.own.x,w.own.y=164200,269800
  p.nav=c.regions.nav('garner')
  for i in range(4):
   now=100+10*i
   entry=c.regions.mine_exit_step(w.map,w.own.position,i>0)
   self.assertIsNotNone(entry)
   goal=p.nav.nearest(entry['position'],3)
   self.assertTrue(p.nav.path(w.own.position,goal))
   self.assertTrue(c.tick(now,p,True))
   p.move_to.assert_called_with(goal,now)
   self.assertEqual(c.purchase_goals(),[])
   w.own.x,w.own.y=entry['position']
   w.entities[88]=dataclasses.replace(w.own,identity=88,model=entry['model'],handle=900,
                                     event_identity=88,event_id=entry['event_id'])
   self.assertTrue(c.tick(now+1,p,True))
   self.assertEqual(p.emit.call_args.args[0][8:],struct.pack('>BIIH',18,88,900,entry['event_id']))
   self.assertTrue(c.tick(now+2,p,True))
   self.assertEqual(c.confirmed,i)
   w.entities.pop(88)
   w.map=entry['to_map']
   w.own.x,w.own.y=entry['arrival_cm']
   p.nav=c.regions.nav(w.map)
   self.assertFalse(c.tick(now+3,p,True))
   self.assertEqual(c.confirmed,i+1)
  self.assertEqual((w.map,p.nav.land_component(w.own.position)),('garner',23))
  self.assertIsNone(c.regions.mine_exit_step(w.map,w.own.position,True))
  self.assertFalse(w.bag)

 def test_owned_andes_ticket_shortens_long_walk_after_safe_landing_check(self):
  from regions import Regions
  from farm_scouting import scout_points
  w,c,p=self.make()
  c.regions=Regions(ROOT/'assets',400)
  w.own.values.update({0:35,4:1,33:180,34:200,35:100})
  c.knowledge=c.regions.mob_knowledge
  w.bag={0:source.item(4602),4:source.item(3051)}
  n=c.regions.nav('garner')
  for model,farm in c.regions.get('garner')['farms'].items():
   farm['points']=scout_points(n,c.regions.mob_knowledge.by_map['garner'].get(int(model),[]),farm['points'])
  self.assertFalse(n.land_component((101800,297500)))
  self.assertIn(253,c.regions.hunting_arrival_sites('garner',(101800,297500)))
  w.own.x,w.own.y=224700,277900
  options=[[100700,296600],[101800,297500]]
  route=dict(self.plan(w,'ticket'),item_id=3051,arrival_cm=options[0],arrival_options=options,name='Andes Forest Haven')
  c.routes=lambda *a:[route]
  p.camp_route_active=lambda now:True
  p.search_goal=(124250,265550)
  from farm_plan import HuntLearning
  p.learning=HuntLearning('level 35 swordsman')
  p.learning.last_progress_at=1
  self.assertTrue(c.tick(100,p,True))
  self.assertEqual(c.plan['name'],'Andes Forest Haven')
  self.assertTrue(c.plan['walking_alternative'])
  self.assertEqual(c.confirmed,0)
  self.assertEqual(p.emit.call_args.args[0][8:],struct.pack('>Bhh',11,4,-1))
  w.own.x,w.own.y=options[1];w.bag.pop(4)
  c.tick(101,p,True)
  self.assertEqual(c.confirmed,1)
  self.assertTrue(c.site_camp[2])
  site_points=c.regions.hunting_arrival_camps('garner',tuple(options[1]))[c.site_camp[1]]
  self.assertEqual(c.site_camp[2],tuple(point for _,point in site_points))

 def test_near_silver_mine_door_can_replace_long_walk_for_level40(self):
  from regions import Regions
  from farm_plan import HuntLearning
  w,c,p=self.make()
  c.regions=Regions(ROOT/'assets',400);c.regions.full_regions=True
  c.data=c.regions.hunting_travel_data;c.knowledge=c.regions.mob_knowledge
  w.own.values.update({0:40,4:9,33:206,34:231,35:48,31:1508,44:480})
  w.own.x,w.own.y=178614,264696
  p.nav=c.regions.nav('garner')
  p.learning=HuntLearning('silver mine')
  routes=c.routes(130,p)
  found=next(route for route in routes if route['name']=='Silver Mine 1 to Silver Mine 2')
  c.routes=lambda *a:[found]
  choice=c.choose(130,p,alternative_to=(113120,273504))
  self.assertEqual((choice['kind'],choice['to_map'],choice['model']),('event','eastgoaf',243))
  self.assertTrue(choice['walking_alternative'])

 def test_long_mine_approach_keeps_progress_and_releases_a_stuck_bot(self):
  w,c,p=self.make()
  w.own.x,w.own.y=135726,268849
  w.own.values[44]=480
  c.plan=dict(self.plan(w,'event'),name='Silver Mine 1 to Silver Mine 2',
              position=[178614,264696],arrival_cm=[22967,2878],to_map='eastgoaf')
  c.target_started=100
  for now in (100,130,160,190,220,250):
   self.assertTrue(c.tick(now,p,True))
   w.own.x+=5000
  w.own.x-=5000
  self.assertIsNotNone(c.plan)
  self.assertFalse(c.tick(285,p,True))
  self.assertIsNone(c.plan)

 def test_outbound_hunt_considers_verified_argent_portal_and_native_fare(self):
  from regions import Regions
  w,c,p=self.make()
  c.regions=Regions(ROOT/'assets',400)
  w.own.x,w.own.y=218700,277600
  p.nav=c.regions.nav('garner')
  w.own.values[8]=10000
  routes=c.routes(100,p)
  argent=[r for r in routes if r['kind']=='portal' and r['name']=='Argent Teleporter - Jovial']
  self.assertEqual({(r['to_map'],r['fare']) for r in argent},{('magicsea',500),('darkblue',500)})
  w.own.values[8]=0
  self.assertFalse(any(r['kind']=='portal' for r in c.routes(100,p)))

 def test_mine_scout_points_use_walkable_spawn_regions_and_conditionals_do_not_qualify_arrivals(self):
  from regions import Regions
  regions=Regions(ROOT/'assets',400)
  regions.full_regions=True
  nav=regions.nav('eastgoaf')
  farm=regions.get('eastgoaf')['farms']['243']
  self.assertTrue(farm['points'])
  self.assertTrue(all(nav.combat_allowed(p) and not nav.needs_recovery(p) for p in farm['points']))
  self.assertIn(243,regions.hunting_arrival_sites('eastgoaf',(23800,2700)))
  conditional=regions.get('abandonedcity')
  self.assertTrue(conditional['farms'])
  self.assertTrue(all(f['conditional_only'] for f in conditional['farms'].values()))
  self.assertFalse(regions.hunting_arrival_sites('abandonedcity',tuple(conditional['spawns'][0])))

 def test_waiting_for_tickets_releases_trip_after_bounded_attempt(self):
  w,c,p=self.make();c.plan=self.plan(w,'event');c.target_started=100
  c.life=SimpleNamespace(prices={4602:1000})
  w.bag={}
  w.own.values[8]=5000
  self.assertFalse(c.tick(100,p,True))
  self.assertEqual([item for item,_,_ in c.purchase_goals()],[4602])
  self.assertFalse(c.tick(219,p,True))
  self.assertEqual(c.target_started,100)
  self.assertFalse(c.tick(220,p,True))
  self.assertIsNone(c.plan)
  self.assertEqual(c.purchase_goals(),[])
  p.move_to.assert_not_called()

 def test_combined_ticket_cost_is_checked_before_starting_shopping(self):
  w,c,p=self.make();c.plan=dict(self.plan(w,'ticket'),item_id=3056);c.target_started=100
  c.life=SimpleNamespace(prices={4602:2500,3056:3500})
  w.bag={}
  w.own.values[8]=5000
  self.assertFalse(c.tick(100,p,True))
  self.assertIsNone(c.plan)
  self.assertEqual(c.purchase_goals(),[])
  p.emit.assert_not_called()

 def test_local_hunting_gets_a_head_start_before_optional_travel(self):
  w,c,p=self.make();p.started=100
  c.choose=Mock(return_value=None)
  self.assertFalse(c.tick(189,p,True))
  c.choose.assert_not_called()
  self.assertFalse(c.tick(190,p,True))
  c.choose.assert_called_once()

 def test_hunter_reconciles_ticket_purchase_before_optional_shopping_gate(self):
  import random
  from town import Town
  from test_coordination import CohortCombatTests
  CohortCombatTests.setUpClass()
  w,p=CohortCombatTests().policy()
  w.own.values[8]=6000
  w.bag={}
  town=Town(w,source.LIFE,None,None,random.Random(1),w.own.position)
  p.town=town
  p.task_budget.paused['town']=1000
  town.wanted=(3057,1)
  town.context=(77,'confirmation',112)
  town.pending=(3057,0,6000,112)
  p.tick(100)
  self.assertEqual(p.attacks,0)
  self.assertIsNotNone(town.pending)
  w.bag[0]=source.item(3057)
  w.own.values[8]=1000
  p.tick(101)
  self.assertEqual(town.confirmed,1)
  self.assertIsNone(town.context)
  self.assertIsNone(town.pending)

 def test_published_knowledge_covers_real_tickets_nodes_and_entries(self):
  data=json.loads((ROOT/'assets/hunting-travel58.json').read_text())
  self.assertEqual((len(data['birthplaces']),len(data['tickets']),len(data['island_nodes']),len(data['entrances'])),(71,43,8,119))
  self.assertEqual(sum(len(n['routes']) for n in data['island_nodes']),56)
  from regions import Regions
  regions=Regions(ROOT/'assets',400)
  landings={(route['map'],tuple(route['arrival_cm'])) for n in data['island_nodes'] for route in n['routes']}
  self.assertEqual(len(landings),8)
  for map_name,point in landings:
   with self.subTest(map_name=map_name,point=point):
    nav=regions.nav(map_name)
    self.assertTrue(nav.land_component(point))
    self.assertFalse(nav.needs_recovery(point))
  self.assertTrue(all(t['points'] and t['minimum_level']>=0 for t in data['tickets']))

class Booster58Tests(unittest.TestCase):
 def make(self):
  w=source.actor();w.own_states={};w.bag={0:source.item(3094)}
  c=XPBoosters(w,source.LIFE,SimpleNamespace(phase=lambda *a:'progression'))
  return w,c,SimpleNamespace(sequence=1,emit=Mock())
 def test_consumption_alone_does_not_confirm_experience_buff(self):
  w,c,p=self.make();self.assertTrue(c.tick(100,p,True));w.bag={}
  c.tick(101,p,True);self.assertEqual(c.confirmed,0)
  w.own_states={48:1};c.tick(102,p,True);self.assertEqual(c.confirmed,1)
  self.assertFalse(c.tick(103,p,True));self.assertEqual(p.emit.call_count,1)
 def test_existing_buff_and_low_gold_prevent_optional_purchase(self):
  w,c,p=self.make();w.bag={};w.own.values[8]=1999;self.assertEqual(c.purchase_goals(),[])
  w.own.values[8]=100000;w.own_states={48:1};self.assertEqual(c.purchase_goals(),[])
  self.assertFalse(c.tick(100,p,True));p.emit.assert_not_called()
 def test_sellers_are_exactly_thirty_percent_without_new_accounts(self):
  self.assertEqual(sum(role_for(i)=='gem_seller' for i in range(1,401)),120)

if __name__=='__main__':unittest.main()
