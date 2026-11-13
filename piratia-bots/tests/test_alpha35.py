"""Server-shortened/stopped routes, worker-local obstacles and truthful terrain audit."""
import concurrent.futures
import struct
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from navigation import Navigation
from classic_wire import sequence
import test_coordination as fixtures

class ObstacleNavigationTests(unittest.TestCase):
    def nav(self,incremental=False):
        n=Navigation.__new__(Navigation);n.origin=(0,0);n.width=n.height=12
        n.cells=bytes([1])*144;n.map='test';n.waypoints=[]
        if incremental:n.enable_incremental()
        return n

    def test_cached_route_replans_around_observed_step_and_recovers_after_expiry(self):
        n=self.nav();a,b=(150,550),(1050,550)
        self.assertEqual(n.segment(a,b),[a,b])
        n.avoid_cell((5,5),100)
        route=n.segment(a,b)
        self.assertGreater(len(route),2)
        self.assertTrue(all(n.line_clear(x,y) for x,y in zip(route,route[1:])))
        self.assertTrue(all(n.cell(p)!=(5,5) for p in n.path(a,b)))
        n.expire_obstacles(131);self.assertEqual(n.segment(a,b),[a,b])
        self.assertEqual(n.cells,bytes([1])*144)

    def test_incremental_shared_cache_cannot_reuse_path_through_obstacle(self):
        n=self.nav(True);a,b=(150,550),(1050,550)
        n.begin_turn();self.assertTrue(n.path(a,b));n.end_turn()
        n.avoid_cell((5,5),100)
        n.begin_turn();route=n.path(a,b);n.end_turn()
        self.assertNotIn((5,5),[n.cell(p) for p in route])
        self.assertGreater(len(route),0)

    def test_observed_obstacle_is_private_to_worker_thread(self):
        n=self.nav(True);n.avoid_cell((5,5),100)
        self.assertFalse(n.free((5,5)))
        def other():
            n.begin_turn();result=n.segment((150,550),(1050,550));n.end_turn()
            return result,n.free((5,5))
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            route,free=pool.submit(other).result()
        self.assertTrue(free);self.assertEqual(route,[(150,550),(1050,550)])
        self.assertFalse(n.free((5,5)))

    def test_many_collisions_are_bounded_and_do_not_modify_base_map(self):
        n=self.nav()
        for i in range(100):n.avoid_cell((i%12,i//12),100)
        self.assertLessEqual(len(n.local.blocked_cells),64)
        self.assertFalse(n.avoid_cell((-1,0),100))
        self.assertEqual(n.cells,bytes([1])*144)

class StoppedMovementTests(unittest.TestCase):
    def policy(self):
        f=fixtures.CohortCombatTests();f.nav=Navigation(ROOT/'assets/argent-navigation.json')
        return f.policy(monsters=0)

    def stop(self,w,p,point,state=1,packet=None,now=102):
        body=(struct.pack('>IIBHH',w.own_id,p.move_packet if packet is None else packet,1,state,0)
              +sequence(struct.pack('<ii',*point)))
        with patch('world.time.monotonic',return_value=now):w.observe(508,body)

    def test_unrequested_early_stop_avoids_forward_cell_not_current_cell(self):
        w,p=self.policy();origin=w.own.position;goal=(origin[0]+1000,origin[1])
        p.move_to(goal,100);point=(origin[0]+100,origin[1])
        self.stop(w,p,point);p.observe_movement(102)
        self.assertEqual(p.blocked_move_stops,1);self.assertEqual(p.stuck,5)
        self.assertIsNotNone(p.last_blocked_step)
        self.assertTrue(p.nav.free(p.nav.cell(point)))
        self.assertFalse(p.nav.free(p.nav.cell(p.last_blocked_step['position'])))
        self.assertEqual(w.position(102),point)
        p.observe_movement(103);self.assertEqual(p.blocked_move_stops,1)

    def test_full_hunt_tick_starts_checked_detour_after_collision(self):
        w,p=self.policy();origin=w.own.position
        p.move_to((origin[0]+1000,origin[1]),100)
        self.stop(w,p,origin,now=102);p.tick(102)
        self.assertEqual(p.blocked_move_stops,1);self.assertEqual(p.recoveries,1)
        self.assertIn('обход препятствия',p.mode)
        points=p.sent_move_points
        self.assertGreaterEqual(len(points),2)
        self.assertTrue(all(p.nav.line_clear(a,b) for a,b in zip(points,points[1:])))
        self.assertEqual(w.position(102),origin) # No invented teleport to the detour.

    def test_our_stop_before_combat_does_not_create_obstacle(self):
        w,p=self.policy();origin=w.own.position
        p.move_to((origin[0]+1000,origin[1]),100);p.stop_action()
        self.stop(w,p,origin);p.observe_movement(102)
        self.assertEqual(p.blocked_move_stops,0);self.assertIsNone(p.last_blocked_step)

    def test_normal_arrival_does_not_create_obstacle(self):
        w,p=self.policy();origin=w.own.position
        p.move_to((origin[0]+1000,origin[1]),100)
        self.stop(w,p,p.move_endpoint);p.observe_movement(102)
        self.assertEqual(p.blocked_move_stops,0)

    def test_stale_packet_stop_cannot_mark_current_route_blocked(self):
        w,p=self.policy();origin=w.own.position
        p.move_to((origin[0]+1000,origin[1]),100)
        self.stop(w,p,origin,packet=999);p.observe_movement(102)
        self.assertEqual(p.blocked_move_stops,0)

    def test_distant_server_correction_does_not_invent_colliding_tile(self):
        w,p=self.policy();origin=w.own.position
        p.move_to((origin[0]+1000,origin[1]),100)
        self.stop(w,p,(origin[0],origin[1]+1000));p.observe_movement(102)
        self.assertEqual(p.blocked_move_stops,1);self.assertIsNone(p.last_blocked_step)

    def test_short_server_accepted_route_does_not_wait_for_long_requested_route(self):
        w,p=self.policy();origin=w.own.position;goal=(origin[0]+5000,origin[1])
        p.move_to(goal,100);requested=p.move_until
        accepted=(origin,(origin[0]+100,origin[1]))
        body=struct.pack('>IIBH',w.own_id,p.move_packet,1,0)+sequence(b''.join(struct.pack('<ii',*pt) for pt in accepted))
        with patch('world.time.monotonic',return_value=100):w.observe(508,body)
        self.assertLess(p.acknowledged_move_deadline(),requested)
        p.move_to(goal,102)
        self.assertEqual(p.move_waits,0);self.assertGreater(p.moves,1)

    def test_wait_branch_no_progress_is_checked_before_early_return(self):
        w,p=self.policy();origin=w.own.position;goal=(origin[0]+5000,origin[1])
        p.move_to(goal,100)
        w.move_revision+=1;w.move_state=0;w.move_packet_number=p.move_packet
        # A zero-length acknowledged route must not mask ten seconds of no progress.
        w.motion[w.own_id]=([origin],100,480)
        p.move_to(goal,111)
        self.assertEqual(p.stuck,5)
        self.assertEqual(p.blocked_move_stops,0) # No forged explicit collision.


class TerrainAuditTests(unittest.TestCase):
    def test_uniform_raw_attribute_cannot_be_promoted_to_a_water_mask(self):
        import tempfile
        from terrain_audit import attr_crop
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'sample.atr'
            path.write_bytes(struct.pack('<II',4,4)+struct.pack('<HB',5,3)*16)
            result=attr_crop(path,(1,1,3,3))
            self.assertEqual(result['raw_attribute_region_counts'],[{'attribute_word':5,'region_byte':3,'tiles':4}])
            self.assertFalse(result['land_sea_semantics_inferred'])
            self.assertEqual(len(result['sha256']),64)

    def test_truncated_attribute_file_and_invalid_crop_are_rejected(self):
        import tempfile
        from terrain_audit import attr_crop
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'sample.atr';path.write_bytes(struct.pack('<II',4,4)+bytes(47))
            with self.assertRaises(ValueError):attr_crop(path,(0,0,4,4))
            path.write_bytes(struct.pack('<II',4,4)+bytes(48))
            with self.assertRaises(ValueError):attr_crop(path,(0,0,5,4))

class QuestFocusTests(unittest.TestCase):
    def policy(self,first=1):
        import test_alpha26 as questing
        import test_alpha18 as selling
        w,p,q=questing.ProfessionSchedulingTests().policy(first)
        w.own.values[0]=14;w.bag_ready=True;w.bag_capacity=24
        _,v,_=selling.VendorTests().make();v.world=w;p.vendor=v
        w.bag={0:selling.VendorTests().item(4315,1)}
        return w,p,q,v

    def test_visible_required_pig_beats_optional_sale_and_ordinary_loot(self):
        from loot import QuestLoot
        w,p,q,v=self.policy();q.journal={62:0}
        w.entities[1000].model=237;w.entities[1000].values[0]=10
        p.loot=QuestLoot(w,True);w.own_hits[88]=(99,True)
        w.items[500]=(4319,1500,w.own.position,0,88,99)
        p.tick(100)
        self.assertTrue(p.quest_combat_ready);self.assertEqual(p.attacks,1)
        self.assertEqual(p.target,1000);self.assertEqual(p.loot.requests,0)
        self.assertIsNone(v.sale_target)

    def test_in_flight_sale_finishes_without_interrupting_native_confirmation(self):
        w,p,q,v=self.policy();q.journal={62:0}
        w.entities[1000].model=237;w.entities[1000].values[0]=10
        v.context=77,'confirmation',200;v.pending=0,4315,1,0,200
        p.tick(100)
        self.assertFalse(p.quest_combat_ready);self.assertEqual(p.attacks,0)
        self.assertIsNotNone(v.pending)

    def test_actual_required_drop_still_picked_before_next_fight(self):
        from loot import QuestLoot
        w,p,q,v=self.policy(4);q.journal={160:0}
        p.loot=QuestLoot(w);w.own_hits[88]=(99,True)
        w.items[500]=(1595,1500,w.own.position,0,88,99)
        p.tick(100)
        self.assertFalse(p.quest_combat_ready);self.assertEqual(p.loot.requests,1)
        self.assertEqual(p.attacks,0)

class NamedDiagnosticsTests(unittest.TestCase):
    def test_public_nickname_finds_only_matching_report_without_private_account_data(self):
        import json,tempfile
        from show_diagnostics import collect,character_tag
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'data').mkdir()
            (root/'data'/'private.json').write_text('never read this')
            (root/'bot-report-07.json').write_text(json.dumps({'bot_index':7,'character_tag':character_tag('Bot38977e75'),'hunt':{'state':'нужный бот'}}))
            (root/'bot-report-08.json').write_text(json.dumps({'bot_index':8,'character_tag':character_tag('Bot00000008'),'hunt':{'state':'другой бот'}}))
            text=collect(root,'bot38977e75')
            self.assertIn('bot-report-07.json',text);self.assertIn('нужный бот',text)
            self.assertNotIn('другой бот',text);self.assertNotIn('never read this',text)

    def test_invalid_nickname_is_not_a_path_or_shell_expression(self):
        from show_diagnostics import character_tag
        for name in ('../data/private.json','Bot38977e75 & echo x','', 'player'):
            with self.assertRaises(ValueError):character_tag(name)
        self.assertEqual(character_tag('bot38977e75'),character_tag('Bot38977E75'))

    def test_old_reports_without_tags_do_not_guess_character_identity(self):
        import json,tempfile
        from show_diagnostics import collect
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'bot-report-01.json').write_text(json.dumps({'bot_index':1,'hunt':{'state':'unknown identity'}}))
            text=collect(root,'Bot38977e75')
            self.assertIn('Ник не найден',text);self.assertNotIn('unknown identity',text)

if __name__=='__main__':unittest.main()
