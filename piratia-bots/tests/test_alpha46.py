"""Fleet replay, dry island egress, owned-ticket recovery and XP priority."""
import sys,unittest,struct
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from navigation import Navigation
from stuck_return import StuckReturn
from inventory import BagItem
from test_development import scene
import test_alpha26 as scheduling

def policy():
 w=scene();w.own.values.update({1:100,31:100,2:80,32:80});w.bag_ready=True;w.bag_disabled=False
 w.bag={3:BagItem(4602,1,0,0,0,0,0,True,(0,0),())}
 return w,SimpleNamespace(world=w,pending_action=None,sequence=5,emit=Mock(),transaction_busy=lambda:False,
                         sitting=SimpleNamespace(tick=Mock(return_value=False)))

class StuckTicketTests(unittest.TestCase):
 def test_only_owned_native_request_no_local_move_or_consumption(self):
  w,p=policy();r=StuckReturn();before=w.own.position
  self.assertTrue(r.tick(100,p));body=p.emit.call_args.args[0]
  self.assertEqual(body[8],11);self.assertEqual(struct.unpack('>hh',body[9:]),(3,-1))
  self.assertEqual(w.bag[3].count,1);self.assertEqual(w.own.position,before)
  self.assertTrue(r.tick(101,p));self.assertEqual(p.emit.call_count,1)
 def test_consumption_alone_is_not_arrival(self):
  w,p=policy();r=StuckReturn();r.tick(100,p);w.bag={}
  self.assertTrue(r.poll(101,p));self.assertEqual(r.confirmed,0)
  r.on_map('magicsea');self.assertTrue(r.poll(102,p));self.assertEqual(r.confirmed,0)
  r.on_map('garner');self.assertFalse(r.poll(103,p));self.assertEqual(r.confirmed,1)
 def test_arrival_alone_does_not_confirm_ticket(self):
  w,p=policy();r=StuckReturn();r.tick(100,p);r.on_map('garner')
  self.assertTrue(r.poll(101,p));self.assertEqual(r.confirmed,0)
  self.assertFalse(r.poll(121,p));self.assertEqual(r.timeouts,1);self.assertFalse(r.tick(122,p))
  self.assertEqual(w.bag[3].count,1)
 def test_full_hp_sp_human_and_owned_ticket_required(self):
  for change in ('hp','sp','boat','no_ticket','unknown_sp'):
   w,p=policy();r=StuckReturn()
   if change=='hp':w.own.values[1]=99
   if change=='sp':w.own.values[2]=79
   if change=='boat':w.own.model=10
   if change=='no_ticket':w.bag={}
   if change=='unknown_sp':w.own.values.pop(2)
   self.assertFalse(r.tick(100,p),change);p.emit.assert_not_called()

class GroundReplayTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.navs={m:Navigation(ROOT/'assets'/(m+'-navigation.json')) for m in ('garner','magicsea','darkblue')}
 def test_isolated_free_cell_is_not_valid_origin(self):
  n=self.navs['garner'];p=(191325,281825)
  self.assertTrue(n.free(n.cell(p)));self.assertTrue(n.needs_recovery(p))
  route=n.recovery_path(p);self.assertGreater(len(route),1)
  for q in route:
   x,y=n.recovery_cell(q);i=y*n.width*2+x
   self.assertTrue(n.safe_recovery_bits[i//8]&(1<<(7-i%8)))
 def test_current_excluded_report_has_dry_exit(self):
  n=self.navs['garner'];p=(175727,260638)
  self.assertTrue(n.needs_recovery(p));self.assertGreater(len(n.recovery_path(p)),1)
  self.assertFalse(n.needs_recovery((223250,278750)))
 def test_no_safe_exit_does_not_invent_path(self):
  n=self.navs['magicsea'];p=(80225,347025)
  self.assertTrue(n.needs_recovery(p));self.assertEqual(n.recovery_path(p),[])
 def test_stop_echo_does_not_blacklist_all_steps(self):
  w,p,q=scheduling.ProfessionSchedulingTests().policy(4);p.nav=self.navs['garner']
  w.own.x,w.own.y=175727,260638;p.recover_to_ground(100)
  before=p.offmesh_requests;p.action_stopped=Mock(return_value=True)
  p.recover_to_ground(100.1);self.assertEqual(p.offmesh_requests,before);self.assertEqual(p.offmesh_blocked,{})
 def test_xp_watchdog_defers_sale_but_allows_full_bag(self):
  w,p,q=scheduling.ProfessionSchedulingTests().policy();p.activity.force_until=200;p.clock=100
  w.bag_ready=True;w.bag_capacity=24;w.bag={};p.raising_travel_funds=False
  vendor=SimpleNamespace(context=None,pending=None);callback=Mock(return_value=True)
  self.assertFalse(p.task('vendor',vendor,callback,100));callback.assert_not_called()
  w.bag_capacity=1
  self.assertTrue(p.task('vendor',vendor,callback,101));callback.assert_called_once()
 def test_queued_ticket_is_flushed_while_waiting_for_native_arrival(self):
  w,p,q=scheduling.ProfessionSchedulingTests().policy()
  w.bag_ready=True;w.bag_disabled=False;w.bag={3:BagItem(4602,1,0,0,0,0,0,True,(0,0),())}
  w.own.values.update({1:100,31:100,2:80,32:80})
  p.clock=100;p.action_open=True
  self.assertTrue(p.stuck_return.tick(100,p));self.assertIsNotNone(p.pending_action)
  p.tick(102)
  self.assertIsNone(p.pending_action);self.assertEqual(p.sent_action_counts.get('11'),1)
  self.assertTrue(p.stuck_return.pending);self.assertEqual(w.bag[3].count,1)
 def test_bank_trip_cannot_override_xp_watchdog(self):
  w,p,q=scheduling.ProfessionSchedulingTests().policy();w.own.values.update({0:20,4:1})
  p.activity.force_until=500;p.bank=SimpleNamespace(busy=False,tick=Mock(return_value=False))
  p.tick(100);p.bank.tick.assert_not_called()

if __name__=='__main__':unittest.main()
