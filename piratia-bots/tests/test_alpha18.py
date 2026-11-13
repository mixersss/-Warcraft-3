"""Productive farming, guarded NPC sale transactions and bounded network recovery."""
import sys,struct,json,random,threading,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from activity import Activity
from vendor import Vendor,sell_request
from inventory import BagItem
from equipment import ItemCatalog
from life import LifeItems
from classic_wire import ProtocolError
from auto_bots import run_bot
from test_development import scene
import test_coordination as base
from navigation import Navigation

class FarmingTests(unittest.TestCase):
 def policy(self):
  f=base.CohortCombatTests();f.nav=Navigation(ROOT/'assets/argent-navigation.json');return f.policy()
 def test_no_progress_selects_bounded_farm_window(self):
  a=Activity();a.update(0,1,0,0,0);a.update(121,1,0,0,0)
  self.assertTrue(a.hunting(122));self.assertFalse(a.hunting(302));self.assertEqual(a.fallbacks,1)
 def test_real_progress_and_intentional_rest_do_not_trigger_idle_recovery(self):
  a=Activity();a.update(0,1,0,0,0);a.update(110,1,5,1,0);a.update(220,1,5,1,0)
  self.assertEqual(a.fallbacks,0);a.update(1000,1,5,1,0,True);self.assertEqual(a.fallbacks,0)
 def test_npc_errand_never_interrupts_live_target(self):
  w,p=self.policy();p.target=1000;f=SimpleNamespace();callback=Mock(return_value=True)
  self.assertFalse(p.task('adventure',f,callback,100));callback.assert_not_called()
 def test_quest_unavailability_fallback_keeps_first_profession_mandatory(self):
  w,p=self.policy();p.activity.force_until=500;p.clock=100;w.own.values.update({0:9,4:0})
  self.assertTrue(p.mandatory_work());f=SimpleNamespace(context=None,pending=None);callback=Mock(return_value=False)
  p.task('adventure',f,callback,100);callback.assert_called_once()
 def test_optional_distant_npc_is_not_a_reason_to_stop_farming(self):
  w,p=self.policy();f=SimpleNamespace(choose_destination=lambda:'far',npcs={'far':(100000,100000)})
  callback=Mock();self.assertFalse(p.task('adventure',f,callback,100));callback.assert_not_called()
 def test_wounded_target_is_preferred_at_same_distance(self):
  w,p=self.policy();a=w.entities[1000];b=SimpleNamespace(identity=1001,values={0:1,1:10,31:100})
  w.entities[1001]=__import__('dataclasses').replace(a,identity=1001,values=b.values)
  self.assertLess(p.target_score(w.entities[1001],100),p.target_score(a,100))

class VendorTests(unittest.TestCase):
 def make(self):
  w=scene();w.bag_ready=True;w.bag_disabled=False;w.bag_capacity=48;w.own.values[8]=50
  v=Vendor(w,LifeItems(ROOT/'assets'),ItemCatalog(ROOT/'assets/items.json'),{},random.Random(1),w.own.position,ROOT/'assets')
  p=SimpleNamespace(market=None,career=None,story=None,adventure=None,send=Mock(),position=lambda now:w.own.position,nav=Mock(),move_to=Mock(return_value=True))
  return w,v,p
 def item(self,i,n):return BagItem(i,n,0,0,0,0,0,True)
 def test_native_npc_sale_has_exact_legacy_fields(self):
  self.assertEqual(sell_request(77,2,20),struct.pack('>IHBBB',77,309,0,2,20))
  with self.assertRaises(ValueError):sell_request(77,2,0)
 def test_plain_whitelisted_junk_is_sold_without_reserve(self):
  w,v,p=self.make();w.bag={0:self.item(1613,30),1:self.item(3457,50),2:self.item(885,50),3:self.item(3296,50)}
  self.assertEqual(v.choices(p),[(0,1613,30)])
  p.career=SimpleNamespace(needed_items=lambda:{1613});self.assertEqual(v.choices(p),[])
 def test_no_sale_without_both_real_count_and_gold_updates(self):
  w,v,p=self.make();w.bag={0:self.item(1613,30)};w.entities[77]=__import__('dataclasses').replace(w.own,identity=77,control=2)
  v.context=77,'ready',60;v.tick(1,p,True);p.send.assert_called_once_with(308,sell_request(77,0,30));self.assertEqual(v.confirmed_sales,0)
  w.bag.clear();v.tick(2,p,True);self.assertEqual(v.confirmed_sales,0)
  w.own.values[8]=75;v.tick(3,p,True);self.assertEqual(v.confirmed_sales,1)
 def test_missing_sale_confirmation_never_deletes_items(self):
  w,v,p=self.make();w.bag={0:self.item(1613,30)};v.context=77,'confirmation',10;v.pending=0,1613,30,50,10
  v.tick(11,p,True);self.assertEqual(w.bag[0].count,30);self.assertEqual(v.sale_timeouts,1);self.assertLessEqual(v.next_sale,11)
 def test_junk_whitelist_excludes_expensive_and_rare_names(self):
  w,v,p=self.make()
  for i in (1612,1619,1621,3457,885,1012,3400,3296):self.assertNotIn(i,v.junk)

class SupervisorTests(unittest.TestCase):
 def test_network_failure_reconnects_same_identity(self):
  stop=threading.Event();failed={'stage':'hunting','exit_reason':'network_error','entered_world':True,'error_type':'ConnectionError','session_elapsed_seconds':10}
  calls=[]
  def once(*args):calls.append(args);return (False,dict(failed)) if len(calls)==1 else (True,{'stage':'completed'})
  with tempfile.TemporaryDirectory() as d,patch('auto_bots._run_bot_once',side_effect=once),patch.object(stop,'wait',return_value=False):
   bot={'account':'saved'};self.assertTrue(run_bot(1,bot,1973,60,stop,Path(d)));self.assertEqual(len(calls),2)
   self.assertIs(calls[0][1],bot);self.assertIs(calls[1][1],bot);self.assertLessEqual(calls[1][3],calls[0][3]);self.assertEqual(len(calls[1][-2]),1)
 def test_protocol_error_is_not_retried(self):
  with tempfile.TemporaryDirectory() as d,patch('auto_bots._run_bot_once',return_value=(False,{'exit_reason':'protocol_or_state_error'})) as once:
   self.assertFalse(run_bot(1,{},1973,60,threading.Event(),Path(d)));self.assertEqual(once.call_count,1)
 def test_stop_during_reconnect_prevents_new_login(self):
  stop=threading.Event()
  with tempfile.TemporaryDirectory() as d,patch('auto_bots._run_bot_once',return_value=(False,{'exit_reason':'network_error'})) as once,patch.object(stop,'wait',return_value=True):
   self.assertFalse(run_bot(1,{},1973,60,stop,Path(d)));self.assertEqual(once.call_count,1)
 def test_repeated_network_failure_has_three_retries_not_endless_loop(self):
  stop=threading.Event()
  with tempfile.TemporaryDirectory() as d,patch('auto_bots._run_bot_once',return_value=(False,{'exit_reason':'network_error'})) as once,patch.object(stop,'wait',return_value=False):
   self.assertFalse(run_bot(1,{},1973,60,stop,Path(d)));self.assertEqual(once.call_count,4)
 def test_foreign_online_account_is_not_kicked_or_retried(self):
  with tempfile.TemporaryDirectory() as d,patch('auto_bots._run_bot_once',return_value=(False,{'exit_reason':'server_refusal','server_error_code':1104,'entered_world':False})) as once:
   self.assertFalse(run_bot(1,{},1973,60,threading.Event(),Path(d)));self.assertEqual(once.call_count,1)

if __name__=='__main__':unittest.main()
