"""Lost closure acknowledgements must not freeze productive work indefinitely."""
import struct
import unittest
import sys
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from escape_plan import RescueDirectory,RecoveryResync
import test_market as markets

class Closure59Tests(unittest.TestCase):
 def make(self):
  w,s,m,p=markets.MarketTests().make();w.own_states={99:3};w.own_states_revision=1
  p.escape_plan=SimpleNamespace(directory=RescueDirectory())
  m.stock=[(0,60000,1,0)];m.opened(0);m.request_close(10)
  return w,s,m,p
 def test_native_own_state_removal_confirms_closure_without_857(self):
  w,s,m,p=self.make();w.observe(511,struct.pack('>IB',w.own_id,0))
  self.assertFalse(m.tick(11,p,True));self.assertEqual(m.state,'idle');self.assertEqual(m.state_confirmed_closes,1)
 def test_stale_and_other_player_states_cannot_confirm_closure(self):
  w,s,m,p=self.make();w.own_states={}
  self.assertTrue(m.tick(11,p,True));self.assertEqual(m.state,'closing')
  w.observe(511,struct.pack('>IB',w.own_id+99,0))
  self.assertTrue(m.tick(12,p,True));self.assertEqual(m.state,'closing')
  w.observe(511,struct.pack('>IBBB',w.own_id,1,99,3))
  self.assertTrue(m.tick(13,p,True));self.assertEqual(m.state,'closing')
 def test_no_proof_after_minute_requests_bounded_native_relogin(self):
  w,s,m,p=self.make()
  with self.assertRaises(RecoveryResync):m.tick(70,p,True)
  self.assertEqual(m.close_resyncs,1);self.assertTrue(m.active_confirmed)
  # Repeating here cannot force repeated reconnects or pretend the stall closed.
  self.assertTrue(m.tick(71,p,True));self.assertEqual(m.state,'closing');self.assertEqual(m.close_resyncs,1)

class Bolt59Tests(unittest.TestCase):
 def test_restored_bolt_resumes_real_cast_requests(self):
  import test_alpha42 as magic
  f=magic.MagicTests();w,p=f.make();w.own.values[0]=27;w.own.values[8]=183
  w.skills={97:magic.spell(level=10)};p.tick(100)
  self.assertIsNone(f.last_skill(p))
  w.skills[99]=magic.spell();p.tick(101)
  self.assertEqual(f.last_skill(p),99);self.assertEqual(p.combat_skills.requests,1)
  self.assertEqual(w.own.values[8],183)
 def test_bolt_ranks_use_only_earned_points_and_require_native_deduction(self):
  import test_alpha51 as guides
  from skills import Skills
  from unittest.mock import Mock
  fixture=guides.GuideSkillTests();fixture.setUpClass();w,plan=fixture.make('cleric_spirit',job=5)
  w.own.values.update({0:27,7:1,8:183});w.skills={99:{'level':1},97:{'level':10},79:{'level':8}}
  c=Skills(w,plan.role,fixture.life);p=Mock(sequence=1)
  self.assertTrue(c.tick(100,p,True));p.send.assert_called_once_with(11,struct.pack('>HB',99,1))
  w.skills[99]['level']=2;c.tick(101,p,True);self.assertEqual(c.confirmed,0)
  w.own.values[7]=0;c.tick(102,p,True);self.assertEqual(c.confirmed,1);self.assertEqual(w.own.values[8],183)

class Shopping59Tests(unittest.TestCase):
 def make(self):
  import random
  from town import Town
  from unittest.mock import Mock
  w,send,m,p=markets.MarketTests().make()
  t=Town(w,m.life,m.gear,None,random.Random(1),w.own.position)
  t.wanted=(1847,5);t.target_shop={'position':[w.own.x+10000,w.own.y],'name':'Test merchant'}
  t.next_break=float('inf');p.nav.nearest.side_effect=lambda point,radius:point;p.send=Mock()
  return w,t,p
 def test_repeated_unfinished_walk_yields_back_to_hunting(self):
  w,t,p=self.make();self.assertTrue(t.tick(100,p,True));self.assertTrue(t.tick(219,p,True))
  self.assertFalse(t.tick(220,p,True));self.assertIsNone(t.wanted);self.assertEqual(t.approach_timeouts,1)
  p.send.assert_not_called();self.assertEqual(t.confirmed,0)
 def test_native_purchase_confirmation_is_not_cancelled_by_walk_deadline(self):
  w,t,p=self.make();t.visit_started=0;t.pending=(1847,0,w.own.values[8],200)
  self.assertTrue(t.tick(150,p,True));self.assertIsNotNone(t.pending);self.assertEqual(t.approach_timeouts,0)
