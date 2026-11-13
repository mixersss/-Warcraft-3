"""Regressions from live reports: fare starvation and lost quest notices."""
import sys,struct,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from city_travel import CityTravel,TELEPORTERS
from adventure import talk_request
from world import Entity
from test_adventure import role,page
import test_alpha26 as base

class RecoveryTests(unittest.TestCase):
 def test_poor_remote_novice_hunts_then_earned_fare_unblocks_trip(self):
  w,p,q=base.ProfessionSchedulingTests().policy(2);w.own.values.update({0:11,8:0})
  p.travel=CityTravel(w,p.send,1,role(2));p.tick(100)
  self.assertTrue(p.raising_travel_funds);self.assertEqual(p.attacks,1)
  self.assertEqual(w.own.values[8],0);self.assertEqual(q.requests,0)
  w.own.values[8]=500;w.entities[1000].values[1]=0
  w.own.x,w.own.y=TELEPORTERS['garner'];w.motion.clear()
  w.entities[99]=Entity(11,99,1099,2,0,*TELEPORTERS['garner'],40)
  p.tick(101);self.assertFalse(p.raising_travel_funds)
  p.send.assert_called_with(301,talk_request(99));self.assertEqual(w.own.values[8],500)
 def quest(self,button=6,journal=None):
  w,p,q=base.ProfessionSchedulingTests().policy(1)
  q.journal={} if journal is None else journal
  q.context=(99,'senna','select',q.role['promotion'])
  q.process_event(827,page(99,q.role['promotion'],button),10)
  return w,p,q
 def test_commit_requests_full_journal_once_before_timeout(self):
  w,p,q=self.quest();q.tick(12,p);q.tick(13,p)
  self.assertEqual(sum(c.args==(325,b'') for c in p.send.call_args_list),1)
 def test_snapshot_confirms_acceptance_without_add_notice(self):
  w,p,q=self.quest();q.observe(828,b'\x01'+struct.pack('>HB',58,0))
  self.assertEqual(q.accepted,1);self.assertIsNone(q.pending);self.assertIsNone(q.context)
  self.assertEqual(w.own.values[4],0)
 def test_snapshot_confirms_delivery_without_clear_notice(self):
  w,p,q=self.quest(7,{58:1});q.observe(828,b'\x00')
  self.assertEqual(q.delivered,1);self.assertIsNone(q.pending)
  self.assertEqual(q.choose_destination(),'peter')
 def test_unchanged_or_unrelated_snapshot_does_not_forge_success(self):
  for payload in (b'\x00',b'\x01'+struct.pack('>HB',1,0)):
   w,p,q=self.quest();q.observe(828,payload)
   self.assertEqual(q.accepted,0);self.assertIsNotNone(q.pending)

if __name__=='__main__':unittest.main()
