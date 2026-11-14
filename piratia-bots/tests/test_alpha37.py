"""All-novice fleet: review server objectives and keep working during optional planning."""
import dataclasses
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from adventure import Adventure,NPCS,talk_request
from progression import Progression
from fleet import Fleet
from show_levels import render
from show_diagnostics import render_report
from route_search import RoutePending
from test_adventure import role,page
from test_development import scene
import test_alpha26 as policies
import test_alpha18 as inventory

class ObjectiveReviewTests(unittest.TestCase):
    def quest(self,mission=62):
        w=scene();w.own.values.update({0:15,4:0});q=Adventure(w,Mock(),role=role(1),tactic='farm')
        q.journal_ready=True;q.journal={mission:0};q.accepted_here.add(mission)
        return w,q

    def test_saved_zero_flag_quest_checked_after_reconnect(self):
        w,q=self.quest();q.accepted_here.clear();q.observe(828,b'\x01'+struct.pack('>HB',62,0))
        q.review_objective(100)
        self.assertIsNone(q.farm());self.assertEqual(q.verification_task,62)
        self.assertEqual(q.journal[62],0);self.assertEqual(w.own.values[4],0)

    def test_reconnect_check_finishes_current_fight(self):
        w,q=self.quest();q.accepted_here.clear();q.journal_snapshot_received=True
        q.review_objective(100,busy=True);self.assertEqual(q.farm(),(237,None))
        q.review_objective(101,busy=False);self.assertIsNone(q.farm())

    def test_twelve_observed_pig_deaths_prompt_verification_not_fake_completion(self):
        w,q=self.quest();q.review_objective(100)
        for i in range(12):
            w.entities[100+i]=dataclasses.replace(w.own,identity=100+i,model=237,control=5)
            w.own_hits[100+i]=(101+i,True);q.review_objective(102+i,busy=True)
        self.assertEqual(q.farm(),(237,None));q.review_objective(120)
        self.assertEqual(q.review_deaths,12);self.assertIsNone(q.farm())
        self.assertEqual(q.journal,{62:0});self.assertEqual(w.own.values[4],0);self.assertEqual(q.delivered,0)

    def test_incomplete_npc_page_returns_to_farming_between_checks(self):
        w,q=self.quest();q.journal_snapshot_received=True;q.accepted_here.clear();q.review_objective(100)
        q.context=99,'peter','select',role(1)['promotion']
        q.process_event(827,page(99,role(1)['promotion'],8),101)
        self.assertEqual(q.farm(),(237,None));self.assertIsNone(q.context)
        q.review_objective(102);self.assertEqual(q.farm(),(237,None))
        q.review_objective(282);self.assertIsNone(q.farm())
        self.assertEqual(q.delivered,0);q.send.assert_not_called()

    def test_real_required_quantity_prompts_native_hand_in(self):
        w,q=self.quest(64);q.review_objective(100)
        w.bag={0:inventory.VendorTests().item(1678,2)};q.review_objective(101)
        self.assertEqual(q.farm(),(125,1678))
        w.bag[0]=inventory.VendorTests().item(1678,3);q.review_objective(102)
        self.assertIsNone(q.farm());self.assertEqual(q.journal[64],0);self.assertEqual(w.bag[0].count,3)

    def test_missing_kill_evidence_periodically_checks_npc(self):
        w,q=self.quest();q.review_objective(100);q.review_objective(279)
        self.assertEqual(q.farm(),(237,None));q.review_objective(280)
        self.assertIsNone(q.farm());self.assertEqual(q.review_deaths,0);self.assertEqual(q.journal[62],0)

    def test_hunter_routes_saved_quest_to_real_peter(self):
        w,p,q=policies.ProfessionSchedulingTests().policy(1);w.own.values[0]=15
        q.observe(828,b'\x01'+struct.pack('>HB',62,0));w.own.x,w.own.y=NPCS['peter'];w.motion.clear()
        w.entities[99]=dataclasses.replace(w.own,identity=99,control=2)
        p.tick(100);p.send.assert_called_once_with(301,talk_request(99))
        self.assertEqual(q.context[1],'peter');self.assertEqual(q.journal[62],0);self.assertEqual(w.own.values[4],0)

    def test_real_profession_change_clears_pending_conversation(self):
        w,q=self.quest();q.context=99,'peter','commit',role(1)['promotion'];q.pending=7,62,200
        w.own.values[4]=1;self.assertFalse(q.tick(100,Mock()))
        self.assertIsNone(q.context);self.assertIsNone(q.pending)
        self.assertEqual(q.delivered,0);self.assertTrue(q.summary()['profession_confirmed'])

class BackgroundPlanningTests(unittest.TestCase):
    def test_vendor_route_wait_does_not_prevent_visible_combat(self):
        w,p,q=policies.ProfessionSchedulingTests().policy(1);w.own.values[0]=14
        q.journal={62:0};w.entities[1000].model=237;w.entities[1000].values[0]=10
        w.bag_ready=True;w.bag_capacity=1;w.bag={0:inventory.VendorTests().item(4315,1)}
        _,v,_=inventory.VendorTests().make();v.world=w;p.vendor=v
        p.move_to=Mock(side_effect=RoutePending())
        p.tick(100)
        self.assertEqual(p.attacks,1);self.assertEqual(p.target,1000)
        self.assertEqual(p.background_task,'vendor');self.assertEqual(len(w.bag),1)

    def test_optional_path_search_is_retained_without_becoming_whole_tick_wait(self):
        w,p,q=policies.ProfessionSchedulingTests().policy(1);p.adventure=None
        feature=Mock(context=None,pending=None)
        callback=Mock(side_effect=RoutePending())
        self.assertFalse(p.task('town',feature,callback,100))
        self.assertEqual(p.background_task,'town');callback.assert_called_once()

    def test_mandatory_quest_path_is_not_silently_dropped(self):
        w,p,q=policies.ProfessionSchedulingTests().policy(1)
        with self.assertRaises(RoutePending):p.task('adventure',q,Mock(side_effect=RoutePending()),100)

    def test_bot117_with_room_does_not_abandon_required_farm_for_small_sale(self):
        w,p,q=policies.ProfessionSchedulingTests().policy(1)
        w.own.values.update({0:17,1:387,31:387,8:264});q.journal={1:0,62:0}
        w.entities.pop(1000);w.bag_ready=True;w.bag_capacity=24
        w.bag={i:inventory.VendorTests().item(4315,1) for i in range(15)}
        _,v,_=inventory.VendorTests().make();v.world=w;p.vendor=v
        p.move_to=Mock(return_value=True);p.tick(100)
        self.assertIsNone(v.sale_target);self.assertEqual(v.sales,0)
        p.move_to.assert_called();self.assertEqual(q.farm(),(237,None))

    def test_bot43_short_of_fare_can_fight_while_sale_route_pending(self):
        from city_travel import CityTravel
        w,p,q=policies.ProfessionSchedulingTests().policy(2)
        w.own.values.update({0:14,1:315,31:315,8:101});q.journal={1:0,98:0}
        w.bag_ready=True;w.bag_capacity=24;w.bag={0:inventory.VendorTests().item(1679,3)}
        p.travel=CityTravel(w,p.send,43,role(2))
        w.entities[1000].model=next(iter(p.planned_models()))
        _,v,_=inventory.VendorTests().make();v.world=w;p.vendor=v
        p.move_to=Mock(side_effect=RoutePending());p.tick(100)
        self.assertTrue(p.raising_travel_funds);self.assertEqual(p.background_task,'vendor')
        self.assertEqual(p.attacks,1);self.assertEqual(w.own.values[8],101)
        self.assertEqual(q.requests,0)

    def test_foreground_detour_has_budget_while_distant_vendor_job_still_pending(self):
        from test_alpha24 import IncrementalNavigationTests
        n=IncrementalNavigationTests().nav();cells=bytearray(n.cells)
        for y in range(8,13):cells[y*n.width+12]=0
        n.cells=bytes(cells);n.begin_turn()
        with self.assertRaises(RoutePending):
            with n.background_work(reserve_foreground=True):n.path((1050,1050),(6050,1050))
        self.assertGreaterEqual(n.local.remaining,384)
        route=n.path((1050,1050),(1450,1050));self.assertTrue(route)
        self.assertTrue(all(n.line_clear(a,b) for a,b in zip(route,route[1:])))
        self.assertEqual(len(n.local.searches),1)
        self.assertEqual(next(iter(n.local.searches))[4],'background');n.end_turn()

class ActualProfessionTests(unittest.TestCase):
    def test_display_distinguishes_planned_champion_and_actual_novice(self):
        text=render_report({'class_path':{'label':'чемпион'},'adventure':{'profession':0}})
        self.assertIn('цель развития чемпион',text);self.assertIn('0 — новичок',text)
        self.assertNotIn(': класс чемпион',text)
        self.assertIn('1 — мечник',render({'bots':{'78':{'job':1,'level':15}},'connected':1,'requested':200}))

    def test_fleet_counts_real_jobs(self):
        with tempfile.TemporaryDirectory() as directory:
            f=Fleet(200,Path(directory)/'population-status.json')
            f.update(1,connected=True,job=0,target_job=8);f.update(2,connected=True,job=1,target_job=9)
            s=f.snapshot();self.assertEqual(s['with_profession'],1);self.assertEqual(s['actual_professions'],{0:1,1:1})

class AttributeRetryTests(unittest.TestCase):
    def test_timeout_does_not_permanently_halt_spending_earned_points(self):
        w=scene();send=Mock();p=Progression(w,send)
        p.tick(0,True);p.tick(11,True);self.assertTrue(p.disabled)
        p.tick(100,True);self.assertEqual(send.call_count,1)
        p.tick(312,True);self.assertEqual(send.call_count,2);self.assertFalse(p.disabled)

    def test_coalesced_stat_gain_still_requires_point_deduction(self):
        w=scene();p=Progression(w,Mock());p.tick(0,True)
        w.own.values[25]+=2;p.tick(1,True);self.assertEqual(p.confirmed,0)
        w.own.values[6]-=1;p.tick(2,True);self.assertEqual(p.confirmed,1)

class FieldMerchantTests(unittest.TestCase):
    def test_real_catalog_contains_mine_and_field_merchants(self):
        _,v,_=inventory.VendorTests().make();shops=v.life.services['shops']['garner']
        self.assertEqual(len(shops),19)
        self.assertTrue(any(s['name']=='Greg' and s['position']==[188351,280526] for s in shops))
        self.assertTrue(any(s['name']=='Accessory - Pucan' and s['position']==[188975,280475] for s in shops))
        self.assertTrue(any(s['name']=='Coral Vendor - Lamon' and s['position']==[206177,254366] for s in shops))

    def test_near_mine_sells_to_greg_without_trip_to_argent(self):
        f=inventory.VendorTests();w,v,p=f.make();w.own.x,w.own.y=188351,280600
        w.bag={0:f.item(4315,1)};self.assertTrue(v.tick(100,p,True))
        self.assertEqual(v.sale_target['name'],'Greg')
        self.assertEqual(v.sale_target['region'],'Abandon Mine Haven')

    def test_pond_report_position_selects_field_vendor_instead_of_city(self):
        f=inventory.VendorTests();w,v,p=f.make();w.own.x,w.own.y=202877,259077
        w.bag={0:f.item(4315,1)};self.assertTrue(v.tick(100,p,True))
        self.assertEqual(v.sale_target['name'],'Coral Vendor - Lamon')
        self.assertEqual(v.sale_target['region'],'Belmont Plains')

    def test_actual_npc_without_trade_function_does_not_pin_all_future_visits(self):
        from classic_wire import string
        f=inventory.VendorTests();w,v,p=f.make();w.bag={0:f.item(4315,1)}
        v.tick(100,p,True);first=tuple(v.sale_target['position']);v.context=77,'talk',200
        payload=struct.pack('>IB',77,1)+string('hello')+b'\x01'+string('Nothing...')+b'\x00'
        v.observe(802,payload,101,p.send)
        self.assertIn(first,v.failed_shops);v.tick(102,p,True)
        self.assertNotEqual(tuple(v.sale_target['position']),first)

if __name__=='__main__':unittest.main()
