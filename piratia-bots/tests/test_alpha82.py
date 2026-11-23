"""Argent departure, mine sectors and finishing an owned fairy's growth."""
import copy
import dataclasses
import math
import random
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from coordination import Coordination
from hunt_travel import HuntTravel
from regions import Regions
from town import Town
import test_alpha76
import test_pet_economy as pets


class FleetRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.regions=Regions(Path(__file__).resolve().parents[1]/'assets',400)
        cls.regions.full_regions=True

    def mine(self):
        world,policy=test_alpha76.Combat76Tests().policy()
        world.map='eastgoaf'
        world.own.x,world.own.y=22967,2878
        world.own.values.update({0:43,4:8,1:2773,31:2773,33:159,34:178,35:119})
        policy.nav=self.regions.nav(world.map)
        policy.region=self.regions.get(world.map)
        return world,policy

    def test_westbound_argent_bot_walks_to_exit_and_keeps_long_term_goal(self):
        world,policy=test_alpha76.Combat76Tests().policy()
        world.own.x,world.own.y=223250,273139
        policy.nav=self.regions.nav('garner')
        far=(188350,274550)
        policy.shortcut=SimpleNamespace(consider=Mock(return_value=False))
        policy.move_to=Mock(return_value=True)
        self.assertTrue(policy.move_to_camp(far,100))
        policy.shortcut.consider.assert_called_once_with(far,100,policy)
        (exit_point,_),kw=policy.move_to.call_args
        self.assertFalse(kw['use_portals'])
        self.assertLess(math.dist(world.own.position,exit_point),12000)
        self.assertTrue(policy.nav.path(world.own.position,exit_point))
        world.own.x,world.own.y=exit_point
        self.assertEqual(policy.camp_route_waypoint(far,120),far)

    def test_mine_chooses_distinct_dry_sectors_and_keeps_lease_in_combat(self):
        shared=Coordination(400)
        chosen=set()
        for index in range(8):
            world,policy=self.mine()
            policy.coordination=shared
            policy.owner=str(index)
            policy.move_to=Mock(return_value=True)
            self.assertTrue(policy.mine_camp_tick(100))
            chosen.add(policy.mine_goal)
            self.assertGreaterEqual(math.dist(world.own.position,policy.mine_goal),4200)
            self.assertEqual(policy.nav.land_component(policy.mine_goal),6)
            policy.clear_zone()
            self.assertIn((policy.owner,'mine'),shared.zones)
        self.assertEqual(len(chosen),8)

    def test_selected_deeper_floor_uses_verified_visible_event_and_arrival(self):
        world,policy=self.mine()
        policy.started=0
        world.bag_ready=True
        world.bag={0:pets.item(4602)}
        travel=HuntTravel(world,self.regions,SimpleNamespace(prices={}),
                          SimpleNamespace(phase=lambda *args:'progression'),Mock(),'floor test')
        travel.deep_mine_cohort=True
        travel.needs_town=lambda *args:False
        travel.clock=100
        plan=travel.deeper_mine_plan(100,policy)
        self.assertEqual(plan['name'],'Silver Mine 2 - Silver Mine 3')
        self.assertEqual(plan['event_model'],193)
        self.assertEqual(policy.nav.land_component(plan['arrival_cm']),5)
        travel.plan=plan
        world.own.x,world.own.y=plan['position']
        self.assertFalse(travel.use_visible_event(105,policy,plan))
        self.assertEqual(travel.mine_arrivals,0)
        event=dataclasses.replace(world.own,identity=77,model=193,event_identity=77,event_id=plan['event_id'])
        world.entities[event.identity]=event
        travel.plan=plan
        self.assertTrue(travel.use_visible_event(106,policy,plan))
        self.assertTrue(travel.tick(107,policy,True))
        world.own.x,world.own.y=plan['arrival_cm']
        self.assertFalse(travel.tick(108,policy,True))
        self.assertEqual(travel.mine_arrivals,1)

    def test_full_growth_can_continue_during_hunt_only_at_nearby_shop(self):
        world,care,_=pets.FairyTests().make()
        world.bag={0:pets.item(1847,10),1:pets.item(232),2:pets.item(2312,6),3:pets.item(4602)}
        life=copy.copy(pets.LIFE)
        life.prices={**life.prices,276:1000}
        town=Town(world,life,self.regions.items,{},random.Random(1),world.own.position)
        town.petcare=care
        nav=self.regions.nav('garner')
        position=(223200,278700)
        world.own.x,world.own.y=position
        shop={'position':(223300,278700),'offers':[276]}
        life.services={'shops':{'garner':[shop]}}
        _,policy=test_alpha76.Combat76Tests().policy()
        policy.world=world
        policy.nav=nav
        policy.activity=SimpleNamespace(hunting=lambda now:True)
        policy.move_to=Mock(return_value=True)
        policy.hunt_before_errands=lambda now:True
        self.assertTrue(policy.task('town',town,lambda:town.tick(100,policy,True),100))
        self.assertEqual(town.wanted,(276,1))
        self.assertEqual(town.visit_deadline,130)
        shop['position']=(200000,278700)
        self.assertIsNone(town.nearby_fairy_fruit(policy,101))
