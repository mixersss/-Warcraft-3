"""Live Alpha32 report: full bag plus sale timer must not freeze quest combat."""
import dataclasses
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from show_diagnostics import render_report
import test_alpha18 as selling
import test_alpha26 as questing

class FullBagWorkTests(unittest.TestCase):
    def make(self,active=True):
        w,p,q=questing.ProfessionSchedulingTests().policy(1)
        w.own.values.update({0:14,1:100,31:100,4:0,8:85})
        if active:q.journal={1:0,62:0}
        f=selling.VendorTests();_,v,_=f.make();v.world=w;p.vendor=v
        w.bag_ready=True;w.bag_capacity=24
        w.bag={i:f.item(4315,1) for i in range(24)}
        if active:
            w.entities[1000].model=237;w.entities[1000].values[0]=10
        return w,p,q,v

    def test_full_bag_with_unavailable_vendor_does_not_freeze_kill_quest(self):
        w,p,q,v=self.make();v.life.services={'shops':{}}
        p.tick(100)
        self.assertEqual(p.target,1000);self.assertEqual(p.attacks,1)
        self.assertEqual(q.requests,0);self.assertTrue(p.inventory_blocked)
        self.assertIsNotNone(p.inventory_blocker)
        w.entities[1000].values[1]=50;p.tick(104)
        self.assertEqual(p.target,1000);self.assertNotIn('нет места',p.mode)

    def test_legacy_vendor_task_pause_does_not_prevent_sale(self):
        w,p,q,v=self.make();p.task_budget.paused['vendor']=250
        p.tick(100)
        self.assertIsNotNone(v.sale_target)
        self.assertEqual(q.requests,0);self.assertIn('продаёт',p.mode)

    def test_full_bag_does_not_accept_referral_when_vendor_unavailable(self):
        w,p,q,v=self.make(False);v.life.services={'shops':{}}
        p.tick(100)
        self.assertEqual(q.requests,0);self.assertEqual(len(w.bag),24)
        self.assertTrue(p.inventory_blocked);self.assertNotIn('нет места',p.mode)
        self.assertTrue(p.attacks or p.moves)

    def test_successful_sale_has_no_delay_before_new_junk_can_be_sold(self):
        f=selling.VendorTests();w,v,p=f.make()
        w.entities[77]=dataclasses.replace(w.own,identity=77,control=2)
        w.bag={0:f.item(4315,1)};v.context=77,'ready',200
        v.tick(100,p,True);w.bag.clear();w.own.values[8]+=1
        v.tick(101,p,True);v.tick(102,p,True)
        self.assertEqual(v.confirmed_sales,1);self.assertFalse(v.context)
        w.bag={0:f.item(4319,1)}
        self.assertTrue(v.tick(102.1,p,True));self.assertIsNotNone(v.sale_target)
        self.assertLessEqual(v.next_sale,102.1)

    def test_empty_sale_probe_does_not_delay_new_drop(self):
        f=selling.VendorTests();w,v,p=f.make()
        self.assertFalse(v.tick(100,p,True));w.bag={0:f.item(4319,1)}
        self.assertTrue(v.tick(100.1,p,True));self.assertIsNotNone(v.sale_target)

    def test_sale_timeout_keeps_items_and_allows_next_attempt_without_cooldown(self):
        f=selling.VendorTests();w,v,p=f.make();w.bag={0:f.item(4319,3)}
        v.context=77,'confirmation',100;v.pending=0,4319,3,50,100
        v.tick(101,p,True);self.assertEqual(v.sale_timeouts,1)
        self.assertTrue(v.tick(102,p,True));self.assertEqual(w.bag[0].count,3)
        self.assertLessEqual(v.next_sale,102)

    def test_legacy_sale_timer_does_not_delay_sale(self):
        f=selling.VendorTests();w,v,p=f.make();w.bag={0:f.item(4319,1)}
        v.next_sale=1000
        self.assertTrue(v.tick(100,p,True));self.assertIsNotNone(v.sale_target)

    def test_productive_vendor_route_has_no_absolute_time_limit_or_pause(self):
        w,p,q,v=self.make()
        for now in range(100,701,20):
            w.own.x+=100
            self.assertTrue(p.task('vendor',v,lambda:True,now))
        # A genuinely stuck route yields to other work, with no sale cooldown.
        self.assertFalse(p.task('vendor',v,lambda:True,736))
        self.assertNotIn('vendor',p.task_budget.paused)
        self.assertLessEqual(v.next_sale,736)

    def test_diagnostics_include_health_duration_position_and_pickup_evidence(self):
        text=render_report({'character_tag':'abc123','hunt':{'state_seconds':88,
            'inventory_blocker':'нет места','world':{'map':'garner','position':[123,456],'hp':50,'max_hp':100}},
            'loot':{'confirmation_timeouts':2}})
        for evidence in ('abc123','50/100','88','[123, 456]','нет места','confirmation_timeouts'):
            self.assertIn(evidence,text)

if __name__=='__main__':unittest.main()
