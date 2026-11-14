"""Bot78 screenshot replay, fast shared corridors and accessible merchant approaches."""
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from navigation import Navigation
from route_search import RoutePending
from show_diagnostics import render_report,collect,character_tag
import test_alpha18 as selling
import test_alpha26 as questing


def drain(nav,start,goal,turns=800):
    for turn in range(turns):
        nav.begin_turn()
        try:return nav.path(start,goal),turn+1
        except RoutePending:pass
        finally:nav.end_turn()
    raise AssertionError('Route did not finish within bounded turns')

class FastRoutesTests(unittest.TestCase):
    def test_bot78_full_bag_starts_actual_merchant_movement_from_reported_position(self):
        w,p,q=questing.ProfessionSchedulingTests().policy(1)
        w.own.x,w.own.y=198751,259451
        w.own.values.update({0:14,1:393,31:393,8:29});q.journal={701:0,62:0}
        w.bag_ready=True;w.bag_capacity=24
        w.bag={i:selling.VendorTests().item(4315,1) for i in range(24)}
        _,v,_=selling.VendorTests().make();v.world=w;p.vendor=v
        p.nav=Navigation(ROOT/'assets/garner-navigation.json');p.nav.enable_incremental()
        for turn in range(800):
            p.tick(100+turn*.25)
            if p.moves:break
        self.assertGreater(p.moves,0);self.assertEqual(p.last_sent_kind,1)
        self.assertEqual(w.own.position,(198751,259451)) # Native request, not fake movement.
        self.assertEqual(v.sales,0);self.assertEqual(q.requests,0)
        self.assertLess(p.nav.planning_stats()['expanded_nodes'],25000)

    def test_two_hundred_nearby_origins_reuse_checked_merchant_corridor(self):
        n=Navigation(ROOT/'assets/garner-navigation.json');n.enable_incremental()
        origin=(198750,259450);goal=n.nearest((219312,270612),6)
        route,_=drain(n,origin,goal);self.assertTrue(route)
        before=n.planning_stats()['expanded_nodes'];hits=n.planning_stats()['shared_route_hits']
        starts=[]
        for dy in range(-8,9):
            for dx in range(-8,9):
                cell=n.cell((origin[0]+dx*100,origin[1]+dy*100))
                if n.free(cell):starts.append(n.position(cell))
        self.assertGreaterEqual(len(starts),200)
        for start in starts[:200]:
            path,_=drain(n,start,goal);self.assertTrue(path)
            self.assertEqual(n.cell(path[-1]),n.cell(goal))
            self.assertEqual(len(path),len(set(path)))
            self.assertTrue(all(n.line_clear(a,b) for a,b in zip(path,path[1:])))
        stats=n.planning_stats()
        self.assertGreaterEqual(stats['shared_route_hits']-hits,150)
        self.assertLess(stats['expanded_nodes']-before,25000)
        self.assertLessEqual(len(n.corridors),128)
        self.assertTrue(all(len(rows)<=4 for rows in n.corridors.values()))

    def test_shared_corridor_join_never_cuts_across_wall(self):
        from test_alpha24 import IncrementalNavigationTests
        n=IncrementalNavigationTests().nav()
        goal=(6050,1050);first,_=drain(n,(1050,1050),goal);self.assertTrue(first)
        second,_=drain(n,(1250,1250),goal);self.assertTrue(second)
        self.assertTrue(all(n.line_clear(a,b) for a,b in zip(second,second[1:])))
        self.assertTrue(all(n.free(n.cell(p)) for p in second))

class MerchantRoutesTests(unittest.TestCase):
    def test_unreachable_merchant_yields_and_selects_another_without_cooldown(self):
        f=selling.VendorTests();w,v,p=f.make();w.bag={0:f.item(4315,1)}
        v.life.services={'shops':{'garner':[
            {'name':'first','position':[w.own.x+1000,w.own.y],'offers':[]},
            {'name':'second','position':[w.own.x+2000,w.own.y],'offers':[]}]}}
        p.move_to.return_value=False
        self.assertFalse(v.tick(100,p,True));self.assertIsNone(v.sale_target)
        self.assertIn((w.own.x+1000,w.own.y),v.failed_shops)
        p.move_to.return_value=True
        self.assertTrue(v.tick(100.1,p,True))
        self.assertEqual(v.sale_target['name'],'second');self.assertLessEqual(v.next_sale,100.1)

    def test_merchant_route_ends_at_nearby_interaction_point(self):
        f=selling.VendorTests();w,v,p=f.make();w.bag={0:f.item(4315,1)}
        self.assertTrue(v.tick(100,p,True))
        point=v.sale_target['position'];goal=v.sale_goals[0]
        self.assertLessEqual(math.dist(point,goal),220)
        self.assertNotEqual(tuple(point),tuple(goal))
        self.assertEqual(v.summary()['route_goal'],list(goal))

    def test_selected_diagnostics_show_search_progress_without_unrelated_parse_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'bot-report-143.json').write_text('{')
            (root/'bot-report-78.json').write_text(json.dumps({'bot_index':78,'character_tag':character_tag('Bot38977e75'),
                'route_planning':{'pending_jobs':[{'known_cells':600,'goal':[219350,270650]}],'shared_route_hits':10},
                'vendor':{'destination':[219312,270612],'route_goal':[219150,270650]}}))
            text=collect(root,'bot38977e75')
            self.assertIn('known_cells',text);self.assertIn('219150',text)
            self.assertNotIn('143',text);self.assertNotIn('пока недоступен',text)

if __name__=='__main__':unittest.main()
