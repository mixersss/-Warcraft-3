"""Alpha38 shore/quest regression, full knowledge, real class gear and portal routes."""
import dataclasses
import json
import math
import struct
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from navigation import Navigation
from coordination import Coordination
from equipment import Equipment,ItemCatalog
from mob_knowledge import MobKnowledge
from farm_plan import HuntLearning
from city_travel import CityTravel
from portal_shortcut import PortalShortcut
from classic_wire import sequence,string
from inventory import BagItem
from test_adventure import role,offers,page
from test_development import scene
import test_alpha26 as scheduling


def portal_page(npc,labels):
    return struct.pack('>IB',npc,1)+string('Teleporter')+bytes([len(labels)])+b''.join(string(x) for x in labels)+b'\0'


class ShoreRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.navs={name:Navigation(ROOT/'assets'/(name+'-navigation.json')) for name in ('garner','magicsea','darkblue')}

    def assert_physical(self,n,points):
        for a,b in zip(points,points[1:]):
            # Subcell samples of every native segment must stay outside hard blocks.
            steps=max(1,math.ceil(math.dist(a,b)/5))
            for i in range(steps+1):
                p=(a[0]+(b[0]-a[0])*i/steps,a[1]+(b[1]-a[1])*i/steps)
                x,y=n.recovery_cell(p);index=int(y*n.width*2+x)
                self.assertTrue(n.recovery_bits[index//8]&(1<<(7-index%8)),p)

    def test_bot93_sends_egress_beyond_old_three_metre_limit_without_fake_position(self):
        w,p,q=scheduling.ProfessionSchedulingTests().policy(4)
        w.own.x,w.own.y=219285,264950;w.own.values.update({0:16,1:523,31:523})
        q.journal={158:0};q.journal_snapshot_received=True
        p.nav=self.navs['garner'];p.tick(100)
        self.assertEqual(p.offmesh_requests,1);self.assertEqual(w.own.position,(219285,264950))
        command,body=p.send.call_args.args;self.assertEqual(command,6);self.assertEqual(body[8],1)
        points=list(struct.iter_unpack('<ii',body[11:]))
        self.assertEqual(points[0],w.own.position);self.assertTrue(p.nav.free(p.nav.cell(points[-1])))
        self.assertIsNone(p.nav.nearest(points[0],3));self.assertGreater(math.dist(points[0],points[-1]),300);self.assert_physical(p.nav,points)
        self.assertEqual(q.requests,0);self.assertEqual(w.own.values[4],0)

    def test_all_seventeen_excluded_snapshot_positions_have_checked_egress(self):
        cases={'garner':[(225854,270504),(218950,264950),(225909,270518),(219285,264950),
               (225875,270515),(225856,270515),(225828,270513),(217951,264357),
               (203350,259250),(218915,277124),(201950,259650),(225842,270514)],
               'magicsea':[(79950,346850),(79950,346950),(79950,346850),(79950,346850),(79934,346750)]}
        for name,positions in cases.items():
            n=self.navs[name]
            for position in positions:
                self.assertFalse(n.free(n.cell(position)))
                route=n.recovery_path(position);self.assertGreater(len(route),1,(name,position))
                self.assertLessEqual(len(route),32);self.assertTrue(n.free(n.cell(route[-1])))
                self.assert_physical(n,route)

    def test_normal_route_still_cannot_cross_reported_pond(self):
        n=self.navs['garner'];self.assertFalse(n.free(n.cell((202550,265950))))
        self.assertFalse(n.line_clear(n.nearest((201850,266350),12),n.nearest((203650,266350),12)))
        self.assertEqual(n.recovery_path((223250,278750)),[])

    def test_server_arrival_releases_offmesh_gate_and_resumes_teacher_route(self):
        w,p,q=scheduling.ProfessionSchedulingTests().policy(4)
        w.own.x,w.own.y=219285,264950;w.own.values.update({0:16,1:523,31:523})
        q.journal={158:0};q.journal_snapshot_received=True;p.nav=self.navs['garner'];p.tick(100)
        endpoint=p.offmesh_route[-1]
        packet=(struct.pack('>IIBHH',w.own_id,p.last_sent_sequence,1,1,0)+sequence(struct.pack('<ii',*endpoint)))
        w.observe(508,packet);p.tick(105)
        self.assertEqual(w.own.position,endpoint);self.assertGreater(p.moves,0)
        self.assertFalse(p.offmesh_route);self.assertNotEqual(p.mode,'ожидание достоверных данных карты')

    def test_rejected_egress_marks_step_and_tries_alternative_without_sixty_second_pause(self):
        w,p,q=scheduling.ProfessionSchedulingTests().policy(4)
        w.own.x,w.own.y=219285,264950;p.nav=self.navs['garner'];p.tick(100)
        first=p.offmesh_route;deadline=p.offmesh_next
        p.tick(deadline+.1)
        self.assertGreater(len(p.offmesh_blocked),0);self.assertNotEqual(p.offmesh_route,first)
        self.assertLessEqual(p.offmesh_next-(deadline+.1),10)
        self.assertEqual(w.own.position,(219285,264950))

    def test_recovery_never_opens_a_hard_blocked_start(self):
        n=Navigation.__new__(Navigation);n.width=n.height=5;n.origin=(0,0)
        n.cells=bytes([0]*24+[1]);n.recovery_cells=bytes([0]*25)
        self.assertEqual(n.recovery_path((50,50)),[])

    def test_recovery_cannot_cut_diagonally_between_hard_obstacles(self):
        n=Navigation.__new__(Navigation);n.width=n.height=3;n.origin=(0,0)
        n.cells=bytes([0]*8+[1]);n.recovery_cells=bytes([1,0,0,0,1,0,0,0,1])
        self.assertEqual(n.recovery_path((50,50)),[])


class ProfessionRegressionTests(unittest.TestCase):
    def test_real_teacher_retry_delay_allows_nearby_productive_hunt(self):
        w,p,q=scheduling.ProfessionSchedulingTests().policy()
        w.own.values.update({0:10,1:500,31:500})
        q.journal={65:0};q.priority_started=True;q.next_visit=500
        monster=w.entities[1000];monster.model=125;monster.values.update({0:8,1:40,31:40})
        p.region={'farms':{'125':{'level':8,'hp':100,'points':[list(monster.position)],'drops':[]}}}
        p.tick(100)
        self.assertEqual(p.attacks,1);self.assertEqual(p.target,1000)
        self.assertEqual(q.requests,0);self.assertEqual(w.own.values[4],0)

    def test_old_quest_combat_flag_cannot_block_native_teacher_talk(self):
        w,p,q=scheduling.ProfessionSchedulingTests().policy()
        w.own.x,w.own.y=q.npcs['peter'];q.journal={62:0};q.journal_snapshot_received=True
        w.entities[99]=dataclasses.replace(w.own,identity=99,control=2)
        p.quest_combat_ready=True;p.tick(100)
        self.assertFalse(p.quest_combat_ready);self.assertEqual(q.context[2],'talk')
        self.assertEqual(q.requests,1);self.assertEqual(w.own.values[4],0)

    def test_required_profession_npc_has_no_two_visitor_cap(self):
        c=Coordination(200)
        for i in range(200):self.assertTrue(c.visit(str(i),'garner',(219220,276700),100,mandatory=True))
        self.assertEqual(len(c.visits),200)
        self.assertFalse(c.visit('optional','garner',(219220,276700),100))

    def test_pending_promotion_page_is_read_without_accepting_or_faking_delivery(self):
        w,p,q=scheduling.ProfessionSchedulingTests().policy();q.journal={64:0}
        q.context=99,'william','talk',None
        q.process_event(802,offers(99,[('Swordsman Promotion',4)]),100)
        self.assertEqual(q.context[2],'select');self.assertEqual(q.requests,1)
        q.process_event(827,page(99,'Swordsman Promotion',8,[(0,1678,3,0)]),101)
        self.assertIsNone(q.context);self.assertEqual(q.last_needs,[(0,1678,3,0)])
        self.assertEqual(q.farm(),(125,1678));self.assertEqual(q.delivered,0)
        self.assertEqual(w.own.values[4],0)


class MonsterKnowledgeTests(unittest.TestCase):
    def test_full_definition_levels_spawn_bounds_and_unknown_dynamic_conditions(self):
        k=MobKnowledge(ROOT/'assets/world-mobs.json')
        self.assertEqual(len(k.monsters),608);self.assertEqual(max(r['level'] for r in k.monsters.values()),300)
        self.assertGreaterEqual(len(k.by_map),21)
        self.assertEqual(k.get(237)['level'],10);self.assertTrue(k.get(237)['locations'])
        nearest=k.nearest(237,'garner',(195000,256300))
        self.assertIsNotNone(nearest);self.assertEqual(nearest['map'],'garner')
        self.assertIsNone(k.nearest(237,'unprovided-map',(0,0)))
        data=json.loads((ROOT/'assets/world-mobs.json').read_text())
        self.assertEqual(len(data['spawn_source_sha256']),29)
        self.assertGreater(data['literal_map_lua_spawn_calls'],0)
        self.assertFalse(data['dynamic_lua_spawns_exhaustively_parsed'])

    def test_learning_retains_high_level_candidates_after_level45(self):
        w=scene();w.own.values.update({0:80,31:10000})
        region={'farms':{'999':{'level':80,'hp':1000,'points':[[100,100]],'drops':[]}}}
        learning=HuntLearning('high-level')
        self.assertEqual(learning.choose(region,w.own,100),{999})

    def test_equal_danger_and_reward_prefers_nearer_farm(self):
        w=scene();w.own.values.update({0:10,31:1000})
        region={'farms':{'100':{'level':10,'hp':100,'points':[[100,100]],'drops':[]},
                         '101':{'level':10,'hp':100,'points':[[120000,120000]],'drops':[]}}}
        learning=HuntLearning('distance');learning.choose(region,w.own,100,position=(100,100))
        self.assertGreater(learning.scores[100],learning.scores[101]*5)


class ClassGearTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.catalog=ItemCatalog(ROOT/'assets/items.json')

    def test_all_four_first_professions_request_compatible_weapon_then_wait_for_confirmation(self):
        for job,body,identity,link in ((1,1,1,9),(2,3,25,6),(4,1,73,9),(5,3,97,9)):
            w=scene();w.own.model=body;w.own.values.update({0:15,4:job})
            w.own.equipment={9:8};w.bag_ready=True;w.bag_capacity=24
            w.bag={0:BagItem(identity,1,20,20,0,0,0,True)}
            p=SimpleNamespace(emit=Mock(),sequence=1);e=Equipment(w,self.catalog,Mock())
            self.assertTrue(e.tick(100,p));self.assertEqual(e.pending[0],identity)
            self.assertEqual(e.confirmed,0);self.assertEqual(w.own.equipment,{9:8})
            self.assertEqual(p.emit.call_args.args[0][-4:],struct.pack('>hh',0,-1))
            w.own.equipment={link:identity};e.tick(101,p)
            self.assertEqual(e.confirmed,1)

    def test_novice_cannot_wear_future_class_gear_or_other_class_weapon(self):
        w=scene();w.own.values.update({0:15,4:0})
        for identity in (1,25,73,97):self.assertIsNone(self.catalog.upgrade(w.own,identity,20))
        w.own.values[4]=1;self.assertIsNone(self.catalog.upgrade(w.own,25,20))
        w.own.values[4]=2;w.own.model=2;self.assertIsNone(self.catalog.upgrade(w.own,25,20))

    def test_two_hand_upgrade_reserves_bag_space_and_does_not_replace_bow_with_newbie_knife(self):
        w=scene();w.own.model=3;w.own.values.update({0:15,4:2});w.own.equipment={9:8}
        self.assertIsNone(self.catalog.upgrade(w.own,25,0))
        self.assertIsNotNone(self.catalog.upgrade(w.own,25,1))
        w.own.equipment={6:25};self.assertIsNone(self.catalog.upgrade(w.own,8,20))
        self.assertEqual(w.own.equipment,{6:25})

    def test_shield_is_scored_for_defence_instead_of_zero_attack(self):
        w=scene();w.own.values.update({0:15,4:1})
        self.assertGreater(self.catalog.gear[121]['score'],0)
        self.assertIsNotNone(self.catalog.upgrade(w.own,121,20))


class PortalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=json.loads((ROOT/'assets/portals.json').read_text())

    def test_only_four_active_source_npcs_and_nine_verified_routes(self):
        self.assertEqual(len(self.data['nodes']),4)
        self.assertEqual(sum(len(n['routes']) for n in self.data['nodes']),9)
        self.assertTrue(self.data['commented_destinations_excluded'])
        self.assertFalse(any('Thundoria Castle!' in e['label'] for n in self.data['nodes'] for e in n['routes']))

    def test_remote_profession_uses_nearer_thundoria_teleporter(self):
        w=scene();w.own.x,w.own.y=74364,158606;w.own.values.update({0:15,8:1000})
        w.entities[99]=dataclasses.replace(w.own,identity=99,control=2)
        travel=CityTravel(w,Mock(),1,role(2),self.data)
        p=SimpleNamespace(position=lambda now:w.own.position,career=None)
        self.assertTrue(travel.tick(100,p,True))
        self.assertEqual(travel.portal['npc_source_id'],43);self.assertEqual(travel.context[0],99)
        self.assertEqual(travel.arrivals,0)

    def test_unavailable_npc_menu_selects_another_source_without_fake_arrival(self):
        w=scene();w.own.x,w.own.y=74364,158606;w.own.values.update({0:15,8:1000})
        w.entities[99]=dataclasses.replace(w.own,identity=99,control=2)
        t=CityTravel(w,Mock(),1,role(2),self.data)
        p=SimpleNamespace(position=lambda now:w.own.position,career=None,nav=Mock(),move_to=Mock(return_value=True))
        t.tick(100,p,True);t.observe(802,portal_page(99,['Other service']),101)
        self.assertEqual(t.arrivals,0);self.assertEqual(w.map,'garner')
        t.tick(132,p,True);self.assertEqual(t.portal['npc_source_id'],0)

    def test_source_verified_same_map_shortcut_waits_for_actual_native_arrival(self):
        w=scene();w.own.x,w.own.y=74364,158606;w.own.values.update({0:15,8:1000})
        w.entities[99]=dataclasses.replace(w.own,identity=99,control=2)
        t=PortalShortcut(w,Mock(),self.data)
        node=next(n for n in self.data['nodes'] if n['npc_source_id']==43 and n['map']=='garner')
        edge=next(e for e in node['routes'] if e['map']=='garner')
        t.plan=node,edge;t.portal=node;t.target='garner';t.goal=(220000,276000)
        t.trip_started=100;t.last_progress=100;t.last_position=w.own.position
        p=SimpleNamespace()
        self.assertTrue(t.resume(100,p));t.observe(802,portal_page(99,['Go to Argent City!']),101)
        t.observe(802,portal_page(99,['Teleport']),102)
        self.assertEqual(t.context[1],'map');self.assertEqual(t.arrivals,0)
        self.assertTrue(t.resume(103,p));self.assertEqual(w.own.position,(74364,158606))
        # Only this synthetic server position update permits confirmation.
        w.own.x,w.own.y=edge['arrival_cm'];self.assertFalse(t.resume(104,p))
        self.assertEqual(t.arrivals,1);self.assertFalse(t.busy)

    def test_shortcut_not_started_without_fare_or_time_saving(self):
        w=scene();w.own.values.update({0:15,8:20})
        t=PortalShortcut(w,Mock(),self.data)
        p=SimpleNamespace(adventure=None,town=None,career=None,story=None,vendor=None,party=None,market=None)
        self.assertFalse(t.consider((220000,277000),100,p));self.assertFalse(t.busy)
        self.assertFalse(t.consider((74000,158600),131,p));self.assertFalse(t.busy)

    def test_real_thundoria_to_argent_goal_selects_paid_shortcut_in_one_planning_slice(self):
        n=Navigation(ROOT/'assets/garner-navigation.json');n.enable_incremental()
        w=scene();w.own.x,w.own.y=n.nearest((74364,158606),6)
        origin=w.own.position;w.own.values.update({0:20,8:2000})
        w.entities[99]=dataclasses.replace(w.own,identity=99,control=2,x=74364,y=158606)
        p=SimpleNamespace(adventure=None,town=None,career=None,story=None,vendor=None,
                          party=None,market=None,nav=n,move_to=Mock(return_value=True))
        t=PortalShortcut(w,Mock(),self.data)
        n.begin_turn()
        try:used=t.consider((219250,276750),100,p)
        finally:n.end_turn()
        self.assertTrue(used);self.assertTrue(t.busy)
        self.assertEqual(t.context[0],99);self.assertGreater(t.savings_seconds,300)
        self.assertLess(n.planning_stats()['expanded_nodes'],512)
        self.assertEqual(w.own.position,origin);self.assertEqual(w.own.values[8],2000)

    def test_shopping_selects_compatible_bow_and_not_another_classes_weapon(self):
        from life import LifeItems
        from town import Town
        import random
        w=scene();w.own.model=3;w.own.values.update({0:15,4:2,8:100000,7:0,13:0})
        w.own.equipment={9:8};w.bag_ready=True;w.bag_capacity=24
        w.bag={0:BagItem(1847,10,0,0,0,0,0,True)}
        life=LifeItems(ROOT/'assets');life.services={'shops':{'garner':[{'offers':[1,97,25]}]}}
        town=Town(w,life,ItemCatalog(ROOT/'assets/items.json'),{},random.Random(1),w.own.position)
        self.assertEqual(town.choose_want(),(25,1))


if __name__=='__main__':unittest.main()
