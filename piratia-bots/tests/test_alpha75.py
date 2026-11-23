"""Regressions from the Alpha74 fleet snapshot."""
import sys
import struct
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import test_alpha24
import test_travel58
from route_search import RoutePending


class Progress75Tests(unittest.TestCase):
    def test_experience_is_observed_without_selecting_a_camp(self):
        world,policy=test_alpha24.ProgressAndDeathTests().policy()
        policy.learning.choose=Mock(side_effect=AssertionError('no camp selected'))
        world.own.values[15]=10
        policy.tick(100)
        world.own.values[15]=48
        policy.tick(105)
        self.assertEqual(policy.learning.session_gain,38)
        self.assertEqual(policy.learning.last_progress_at,105)

    def test_direct_approach_does_not_wait_for_unrelated_expensive_route(self):
        nav=test_alpha24.IncrementalNavigationTests().nav()
        origin,far,near=(1050,1050),(6050,1050),(1150,1050)
        nav.begin_turn(expansions=1)
        try:
            with self.assertRaises(RoutePending):
                nav.path(origin,far)
            self.assertTrue(nav.local.searches)
            self.assertEqual(nav.path(origin,near),[origin,near])
            self.assertTrue(nav.local.searches)
        finally:
            nav.end_turn()

    def test_visible_mob_defers_optional_town_but_not_weapon_purchase(self):
        world,policy=test_alpha24.ProgressAndDeathTests().policy(monsters=1)
        world.own.values.update({0:10,4:1})
        policy.clock=100
        policy.camp_scouting=True
        policy.region={'farms':{}}
        policy.planned_models=lambda:{75}
        policy.activity=SimpleNamespace(hunting=lambda now:False)
        town=SimpleNamespace(context=None,pending=None,critical_items=lambda:[],
                             combat_supply_required=lambda:False)
        call=Mock(return_value=True)
        self.assertTrue(policy.local_combat_ready(100))
        self.assertFalse(policy.task('town',town,call,100))
        call.assert_not_called()
        town.combat_supply_required=lambda:True
        self.assertTrue(policy.task('town',town,call,100))
        call.assert_called_once()

    def test_distant_ticket_stock_cannot_start_optional_shopping_loop(self):
        fixture=test_travel58.Travel58Tests()
        world,travel,policy=fixture.make()
        world.own.values[8]=50000
        ticket={'item_id':3051,'map':'eastgoaf','minimum_level':1,'birthplace':'Cave',
                'points':[(24000,2200)]}
        travel.data['tickets']=[ticket]
        travel.life=SimpleNamespace(prices={3051:1000,4602:1000},services={'shops':{'garner':[]}})
        wx,wy=world.own.position
        shop={'position':(wx+15000,wy),'offers':[3051,4602]}
        travel.life.services['shops']['garner'].append(shop)
        self.assertFalse(travel.routes(100,policy))
        shop['position']=(wx+1000,wy)
        self.assertEqual(travel.routes(100,policy)[0]['shopping_distance'],1000)
        world.bag={}
        shop['offers']=[3051]
        self.assertFalse(travel.routes(100,policy))

    def test_after_no_xp_an_easy_visible_mob_can_restart_the_cycle(self):
        world,policy=test_alpha24.ProgressAndDeathTests().policy(monsters=1)
        world.own.values.update({0:35,4:1,31:1000})
        entity=world.entities[1000]
        entity.values[0]=22
        policy.camp_scouting=True
        policy.region={'farms':{}}
        policy.mob_knowledge={entity.model:{'territory':0,'base_xp':150,'hp':100}}
        policy.learning.last_progress_at=100
        self.assertFalse(policy.visible_ground_opportunities(250,world.own.position))
        self.assertEqual(policy.visible_ground_opportunities(281,world.own.position),{1000})

    def test_fast_native_hp_loss_triggers_retreat_before_static_threshold(self):
        world,policy=test_alpha24.ProgressAndDeathTests().policy()
        world.own.values.update({1:100,31:100})
        payload=(struct.pack('>IIB',world.own_id,5,4)+b'\0'*6
                 +struct.pack('>I',17)+b'\0'*22+struct.pack('>BHBI',0,1,1,48))
        with patch('world.time.monotonic',return_value=99):
            world.observe(508,payload)
        self.assertEqual(world.own.values[1],48)
        policy.tick(100)
        self.assertTrue(policy.resting)
        self.assertEqual(policy.attacks,0)

    def test_empty_arrival_stops_pinning_one_species(self):
        world,policy=test_alpha24.ProgressAndDeathTests().policy()
        policy.hunt_travel=SimpleNamespace(preferred_model=295,plan=None,site_until=700,site_arrival=('garner',100))
        self.assertEqual(policy.travel_farm_preference(150),295)
        self.assertIsNone(policy.travel_farm_preference(190))
        policy.learning.last_progress_at=200
        self.assertEqual(policy.travel_farm_preference(201),295)
