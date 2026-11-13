"""Crowded patches, NPC admission and uninterrupted routes, without a game server."""
import json,random,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from coordination import Coordination
from navigation import Navigation
from runtime_guard import inspect_data
from test_development import scene

class DistributionTests(unittest.TestCase):
 def test_nearby_points_are_one_crowded_patch(self):
  c=Coordination();goals=[(10000,10000),(10100,10000),(10200,10000),(16000,10000)]
  c.choose_zone('a','garner',[goals[0]],0)
  self.assertEqual(c.choose_zone('b','garner',goals,1),goals[-1])
 def test_two_hundred_workers_fill_separated_patches_not_first_adjacent_tiles(self):
  c=Coordination();goals=[(10000+i*5000+j*100,10000) for i in range(20) for j in range(3)]
  chosen=[c.choose_zone(str(i),'garner',goals,0) for i in range(200)]
  counts=[sum((p[0]-10000)//5000==i for p in chosen) for i in range(20)]
  self.assertEqual(counts,[10]*20)
  for i in range(200):self.assertEqual(c.choose_zone(str(i),'garner',goals,5),chosen[i])
 def test_optional_npc_visits_yield_without_occupying_waiting_slots(self):
  c=Coordination(30)
  self.assertTrue(c.visit('a','garner',(100,100),0))
  self.assertTrue(c.visit('b','garner',(200,100),0))
  self.assertFalse(c.visit('c','garner',(300,100),0))
  self.assertNotIn('c',c.visits)
  self.assertTrue(c.visit('c','garner',(2000,100),0))
  self.assertFalse(c.visit('d','garner',(4000,100),0))
  self.assertTrue(c.visit('d','garner',(4000,100),0,mandatory=True))
  self.assertTrue(c.visit('e','garner',(300,100),16))
 def test_healthy_newbie_farms_before_optional_shopping_but_wounded_can_buy(self):
  from town import Town
  from life import LifeItems
  from equipment import ItemCatalog
  world=scene();world.bag_ready=True;world.bag_capacity=24;world.own.values[8]=1000
  town=Town(world,LifeItems(ROOT/'assets'),ItemCatalog(ROOT/'assets/items.json'),{},random.Random(1),world.own.position)
  nav=Navigation(ROOT/'assets/argent-navigation.json')
  policy=SimpleNamespace(nav=nav,position=lambda now:world.own.position,move_to=Mock(return_value=True),allow_visit=Mock(return_value=True),send=Mock())
  self.assertFalse(town.tick(1,policy,True));policy.move_to.assert_not_called()
  world.own.values[1]=30
  self.assertTrue(town.tick(2,policy,True,medical=True));self.assertEqual(town.wanted[0],1847)
 def test_shop_does_not_require_artificial_visitor_admission(self):
  from town import Town
  from life import LifeItems
  from equipment import ItemCatalog
  world=scene();world.own.values.update({0:4,8:1000});world.bag_ready=True;world.bag_capacity=24
  town=Town(world,LifeItems(ROOT/'assets'),ItemCatalog(ROOT/'assets/items.json'),{},random.Random(1),world.own.position)
  policy=SimpleNamespace(position=lambda now:world.own.position,allow_visit=Mock(return_value=False),nav=Mock(),move_to=Mock(return_value=True))
  self.assertTrue(town.tick(1,policy,True));policy.allow_visit.assert_not_called();self.assertIsNotNone(town.target_shop)

class RouteTests(unittest.TestCase):
 def nav(self):
  n=Navigation.__new__(Navigation);n.origin=(0,0);n.width=150;n.height=150;n.cells=bytes([1])*22500
  return n
 def test_long_straight_route_reaches_goal_in_one_action(self):
  nav=self.nav();self.assertEqual(nav.segment((50,50),(12050,50)),[(50,50),(12050,50)])
 def test_obstacle_detour_retains_checked_geometry(self):
  nav=self.nav();cells=bytearray(nav.cells)
  for y in range(90):cells[y*nav.width+60]=0
  nav.cells=bytes(cells);path=nav.path((1050,1050),(11050,1050));turns=nav.segment(path[0],path[-1])
  self.assertEqual(turns[-1],path[-1]);self.assertLessEqual(len(turns),32)
  # Each compressed edge is exactly a run in the original A* path, without
  # inventing diagonals or cutting across the obstacle.
  indexes=[path.index(point) for point in turns]
  for a,b in zip(indexes,indexes[1:]):
   deltas={(path[i+1][0]-path[i][0],path[i+1][1]-path[i][1]) for i in range(a,b)}
   self.assertEqual(len(deltas),1)
 def test_sub_cell_start_is_preserved_on_checked_direct_line(self):
  nav=self.nav();start=(11,29);path=nav.path(start,(5050,5050));turns=nav.segment(start,path[-1])
  self.assertEqual(turns,[start,path[-1]]);self.assertTrue(nav.line_clear(*turns))

class DataTests(unittest.TestCase):
 def test_fresh_state_and_existing_state_only_report_counts(self):
  with tempfile.TemporaryDirectory() as d:
   self.assertFalse(inspect_data(d)['saved_state'])
   Path(d,'bot-local.json').write_text(json.dumps({'version':1,'bots':[{'secret':'private'}]}))
   self.assertEqual(inspect_data(d),{'saved_state':True,'saved_bots':1})
 def test_nested_or_partial_copy_is_not_silently_replaced(self):
  with tempfile.TemporaryDirectory() as d:
   Path(d,'data').mkdir();Path(d,'data','bot-local.json').write_text('{}')
   with self.assertRaisesRegex(RuntimeError,'вложена'):inspect_data(d)
  with tempfile.TemporaryDirectory() as d:
   Path(d,'hunt-learning-001.json').write_text('{}')
   with self.assertRaisesRegex(RuntimeError,'часть'):inspect_data(d)

class ReceiveSchedulingTests(unittest.TestCase):
 def test_packet_storm_is_serviced_without_one_decision_per_packet(self):
  from collections import deque
  from unittest.mock import patch
  from test_hunt import enter_packet
  from headless import Report
  from hunter import hunt
  clock=[100.0]
  def receive(deadline):clock[0]+=.001;return 999,b''
  client=SimpleNamespace(enter_payload=enter_packet(),pending_world=deque(),
     service=Mock(),wire=SimpleNamespace(receive=receive,send=Mock(),last_send=100,heartbeat=Mock()))
  stop=SimpleNamespace(is_set=lambda:False)
  report=Report();nav=Navigation(ROOT/'assets/argent-navigation.json')
  with patch('hunter.time.monotonic',side_effect=lambda:clock[0]),patch('hunter.Hunter.tick') as think,patch.object(Report,'write'):
   hunt(client,1,stop,report,nav,tell=Mock(),bot_name='Bot00000000')
  self.assertGreaterEqual(client.service.call_count,999)
  self.assertGreaterEqual(think.call_count,3);self.assertLessEqual(think.call_count,5)
