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
  regions=SimpleNamespace(hunting_travel_data=data,mob_knowledge=source.MOBS,map_catalog={'garner':{},'eastgoaf':{}})
  c=HuntTravel(w,regions,source.LIFE,SimpleNamespace(phase=lambda *a:'progression'),Mock(),'Bot58')
  p=SimpleNamespace(sequence=3,emit=Mock(),position=lambda now:w.own.position,nav=SimpleNamespace(nearest=lambda point,radius:point),move_to=Mock(return_value=True),learning=SimpleNamespace(last_progress_at=None))
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
 def test_event_requires_visible_matching_native_identity_and_exact_action(self):
  w,c,p=self.make();c.plan=dict(self.plan(w,'event'),event_id=6,model=193);c.target_started=100
  entity=dataclasses.replace(w.own,identity=88,model=193,handle=900,event_identity=88,event_id=6)
  w.entities[88]=entity;self.assertTrue(c.tick(100,p,True))
  self.assertEqual(p.emit.call_args.args[0][8:],struct.pack('>BIIH',18,88,900,6));self.assertEqual(c.confirmed,0)
 def test_closed_event_is_released_to_normal_hunting_without_fake_move(self):
  w,c,p=self.make();c.plan=dict(self.plan(w,'event'),event_id=6,model=193);c.target_started=100
  self.assertFalse(c.tick(100,p,True));self.assertIsNone(c.plan);p.emit.assert_not_called();self.assertTrue(c.blocked)
 def test_far_trip_needs_owned_return_ticket_even_for_portals(self):
  w,c,p=self.make();c.routes=lambda *a:[self.plan(w)];c.nearby=lambda *a:[(295,0)];c.rate=lambda *a:1
  w.bag={}
  c.plan=c.choose(100,p);self.assertIsNotNone(c.plan);c.target_started=100
  self.assertFalse(c.tick(100,p,True));p.emit.assert_not_called();c.send.assert_not_called()
  w.bag={0:source.item(4602)};self.assertIsNotNone(c.choose(100,p))
 def test_published_knowledge_covers_real_tickets_nodes_and_entries(self):
  data=json.loads((ROOT/'assets/hunting-travel58.json').read_text())
  self.assertEqual((len(data['birthplaces']),len(data['tickets']),len(data['island_nodes']),len(data['entrances'])),(71,43,8,119))
  self.assertEqual(sum(len(n['routes']) for n in data['island_nodes']),56)
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
