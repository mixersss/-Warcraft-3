"""Earned non-quest loot, native damage ownership, Forest Spirit and stable transport."""
import dataclasses,json,socket,struct,sys,tempfile,threading,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from world import HP
from classic_wire import Wire
from loot import QuestLoot
from inventory import BagItem
from city_travel import CityTravel
from auto_bots import run_bot
from navigation import Navigation
from test_development import scene
import test_coordination as base

class LootTests(unittest.TestCase):
 def make(self):
  w=scene();w.bag_ready=True;w.bag_capacity=48;w.bag={}
  p=SimpleNamespace(position=lambda now:w.own.position,sequence=1,emit=Mock(),next_action=0,nav=Mock(),move_to=Mock(return_value=False))
  loot=QuestLoot(w,collect_all=True);loot.note_attack(88,0);w.own.values[15]+=1
  w.items[500]=(1620,1500,w.own.position,0,88,0)
  return w,p,loot
 def test_owned_nonquest_drop_is_collected_and_real_bag_confirms(self):
  w,p,l=self.make();self.assertTrue(l.tick(2,p,set()));self.assertEqual(l.confirmed,0)
  w.bag[0]=BagItem(1620,1,0,0,0,0,0,True);w.items.clear();l.tick(3,p,set())
  self.assertEqual(l.confirmed,1);self.assertEqual(l.requests,1)
 def test_waiting_pickup_does_not_block_hunting(self):
  w,p,l=self.make();l.tick(2,p,set());self.assertFalse(l.tick(3,p,set()))
  self.assertEqual(l.confirmed,0);self.assertEqual(l.requests,1)
 def test_disappearance_without_inventory_gain_is_not_success(self):
  w,p,l=self.make();l.tick(2,p,set());w.items.clear();l.tick(13,p,set())
  self.assertEqual(l.confirmed,0);self.assertEqual(l.timeouts,1)
 def test_own_damage_and_death_allow_party_zero_xp_loot(self):
  w,p,l=self.make();l.attacked.clear();w.own_hits[88]=(1,True)
  self.assertTrue(l.tick(2,p,set()))
 def test_other_player_or_thrown_or_uncredited_items_are_ignored(self):
  w,p,l=self.make();l.attacked.clear();w.own_hits[88]=(1,False)
  self.assertFalse(l.tick(2,p,set()));w.own_hits[88]=(1,True)
  w.items[500]=(1620,1500,w.own.position,1,88,0);self.assertFalse(l.tick(2,p,set()))
 def test_full_inventory_does_not_spam_pickups(self):
  w,p,l=self.make();w.bag_capacity=1;w.bag[0]=BagItem(289,1,0,0,0,0,0,True)
  self.assertFalse(l.tick(2,p,{1620}));p.emit.assert_not_called()
 def test_unknown_drop_keeps_four_free_cells_for_needed_items(self):
  w,p,l=self.make();w.bag_capacity=4
  self.assertFalse(l.tick(2,p,set()));self.assertTrue(l.tick(2,p,{1620}))
 def test_repeated_pickup_refusal_is_bounded(self):
  w,p,l=self.make()
  for t in (2,13,22,33,42):l.tick(t,p,set())
  self.assertEqual(l.requests,2);self.assertEqual(l.confirmed,0)
 def test_damage_packet_records_actual_source_and_death(self):
  native=json.loads((ROOT/'tests/fixtures/native_damage_prefix.json').read_text())
  for knock in (0,1):
   with self.subTest(knockback=knock):
    w,p,l=self.make();w.entities[88]=dataclasses.replace(w.own,identity=88,control=5,values={HP:20})
    body=bytes.fromhex(native['knockback_'+str(knock)])+struct.pack('>BHBI',3,1,HP,0)
    with patch('world.time.monotonic',return_value=2):w.observe(508,body)
    self.assertEqual(w.own_hits[88],(2,True))
 def test_party_final_blow_preserves_own_earlier_damage_credit(self):
  w,p,l=self.make();l.attacked.clear();w.own_hits[88]=(1,False)
  w.entities[88]=dataclasses.replace(w.own,identity=88,control=5,values={HP:20})
  prefix=struct.pack('>IIBBHBBB',88,1,4,1,256,0,0,0)
  body=prefix+struct.pack('>IIIIII',999,0,0,28,0,0)+bytes(2)+struct.pack('>BHBI',3,1,HP,0)
  w.observe(508,body);self.assertTrue(l.tick(2,p,set()))
 def test_death_attribute_update_preserves_own_earlier_damage_credit(self):
  w,p,l=self.make();l.attacked.clear();w.own_hits[88]=(1,False)
  w.entities[88]=dataclasses.replace(w.own,identity=88,control=5,values={HP:20})
  w.observe(509,struct.pack('>IBHBI',88,3,1,HP,0));self.assertTrue(l.tick(2,p,set()))
 def test_unrelated_item_gain_does_not_confirm_still_visible_drop(self):
  w,p,l=self.make();l.tick(2,p,set());w.bag[0]=BagItem(1620,1,0,0,0,0,0,True)
  l.tick(3,p,set());self.assertEqual(l.confirmed,0)
 def test_blocked_drop_approach_cannot_hold_bot_indefinitely(self):
  w,p,l=self.make();w.items[500]=(1620,1500,(w.own.x+800,w.own.y),0,88,0)
  p.move_to.return_value=True;p.nav.nearest.return_value=(w.own.x+800,w.own.y)
  self.assertTrue(l.tick(2,p,set()));self.assertFalse(l.tick(11,p,set()))
  self.assertEqual(l.unreachable,1);self.assertEqual(l.requests,0)

class StarterTests(unittest.TestCase):
 def test_level_one_selects_forest_spirit_instead_of_flowers(self):
  f=base.CohortCombatTests();f.nav=Navigation(ROOT/'assets/argent-navigation.json');w,p=f.policy()
  p.region=json.loads((ROOT/'assets/regions.json').read_text())['garner']
  w.own.values[0]=1
  flower=w.entities[1000]
  forest=dataclasses.replace(flower,identity=1001,model=103,handle=2001,values={0:3,1:69,31:69})
  w.entities[1001]=forest
  self.assertEqual(p.farm_models(),{103});self.assertTrue(p.eligible(forest,100));self.assertFalse(p.eligible(flower,100))
  p.tick(100);self.assertEqual(p.target,1001)
  w.own.values[0]=4;self.assertFalse(p.starter_models())
 def test_newbie_goes_to_argent_then_returns_to_preferred_city(self):
  w=scene();w.own.values[0]=1;w.map='darkblue';t=CityTravel(w,Mock(),8,{'first_job':2})
  self.assertTrue(t.starter_trip());self.assertEqual(t.destination(SimpleNamespace(career=None)),'garner')
  w.own.values[0]=4;self.assertEqual(t.destination(SimpleNamespace(career=None)),'darkblue')
  w.own.values[0]=9;self.assertEqual(t.destination(SimpleNamespace(career=None)),'darkblue')

class TransportTests(unittest.TestCase):
 def test_send_uses_transmit_timeout_instead_of_last_poll_deadline(self):
  sock=Mock();wire=Wire(sock);wire.header_size=6
  wire.send(17);self.assertEqual(sock.method_calls[0].args,(10,))
  self.assertEqual(sock.method_calls[1][0],'sendall')
  sock.reset_mock();wire.heartbeat();self.assertEqual(sock.method_calls[0].args,(10,))
 def test_partial_send_timeout_is_connection_failure_not_ignored_poll_timeout(self):
  sock=Mock();sock.sendall.side_effect=socket.timeout();wire=Wire(sock);wire.header_size=6
  with self.assertRaises(ConnectionError) as caught:wire.send(17)
  self.assertNotIsInstance(caught.exception,TimeoutError)
 def test_heartbeat_send_timeout_also_restarts_connection(self):
  sock=Mock();sock.sendall.side_effect=socket.timeout();wire=Wire(sock)
  with self.assertRaises(ConnectionError):wire.heartbeat()
 def test_continuous_network_recovery_does_not_stop_after_three_attempts(self):
  stop=threading.Event();waits=[]
  def wait(delay):
   waits.append(delay)
   if len(waits)==5:stop.set();return True
   return False
  failure={'exit_reason':'network_error','entered_world':True,'error_type':'ConnectionError','session_elapsed_seconds':1}
  with tempfile.TemporaryDirectory() as d,patch('auto_bots._run_bot_once',return_value=(False,dict(failure))) as once,patch.object(stop,'wait',side_effect=wait):
   self.assertFalse(run_bot(1,{},1973,0,stop,Path(d)))
   self.assertEqual(once.call_count,5);self.assertGreaterEqual(waits[3],120)
 def test_diagnostics_history_is_bounded_and_keeps_error_location(self):
  stop=threading.Event();histories=[]
  def once(*args):
   histories.append(list(args[-2]))
   if len(histories)==25:stop.set()
   return False,{'exit_reason':'network_error','error_locations':[{'file':'transport.py','line':1,'function':'receive'}]}
  with tempfile.TemporaryDirectory() as d,patch('auto_bots._run_bot_once',side_effect=once),patch.object(stop,'wait',return_value=False):
   run_bot(1,{},1973,0,stop,Path(d))
  self.assertEqual(len(histories[-1]),20);self.assertIn('error_locations',histories[-1][-1])

if __name__=='__main__':unittest.main()
