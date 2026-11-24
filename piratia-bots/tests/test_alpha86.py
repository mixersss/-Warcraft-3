"""Empty-mine routing and bounded Amplifier of Strive purchases."""
import copy
import random
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from navigation import Navigation
from regions import Regions
from town import Town
from xp_boosters import XPBoosters
import test_alpha76
import test_alpha79
import test_pet_economy as pets


class LiveBottleneckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assets=Path(__file__).resolve().parents[1]/'assets'
        cls.regions=Regions(cls.assets)

    def test_new_direction_can_finish_report_route_after_first_budget_exhausts(self):
        nav=Navigation(self.assets/'garner-navigation.json')
        nav.enable_incremental()
        start,goal=(112250,276450),(99750,260650)
        nav.begin_turn(expansions=120000)
        try:
            with patch('navigation.time.thread_time',return_value=0):
                route=nav.path(start,goal)
        finally:
            nav.end_turn()
        self.assertEqual((route[0],route[-1]),(start,goal))
        self.assertTrue(all(nav.line_clear(a,b) for a,b in zip(route,route[1:])))
        self.assertGreater(nav.planning_stats()['expanded_nodes'],20000)

    def test_empty_abandoned_one_has_no_farms_but_retains_exit(self):
        entrance=self.regions.mine_exit_entrance
        p=tuple(entrance['position'])
        self.assertTrue(self.regions.abandoned_mine_one('garner',p))
        self.assertEqual(self.regions.hunting_arrival_sites('garner',p),{})
        self.assertTrue(self.regions.mine_exit_step('garner',p,False))
        self.assertFalse(any(self.regions.abandoned_mine_one('garner',x)
                            for f in self.regions.get('garner')['farms'].values() for x in f['points']))

    def test_watchdog_respects_progressing_mine_search_without_ordinary_camp(self):
        world,policy=test_alpha76.Combat76Tests().policy()
        _,travel,_=test_alpha79.MineAndReactionTests().planned_mine()
        travel.world=world
        travel.approach_clock=(None,400,None,100,None)
        policy.hunt_travel=travel
        policy.nav.nearest=Mock(side_effect=lambda point,radius:tuple(point))
        policy.nav.pending_farm_search=Mock(return_value=('mine route',500))
        policy.progress_monitor.fast_tick(100,policy)
        policy.nav.pending_farm_search.return_value=('mine route',8000)
        policy.progress_monitor.fast_tick(220,policy)
        self.assertEqual(policy.progress_monitor.recoveries,0)
        self.assertIn('продолжает продвигаться',policy.progress_monitor.reason)

    def test_progression_buys_3094_nearby_and_records_spent_gold(self):
        world,_=test_alpha76.Combat76Tests().policy()
        world.own.values.update({0:43,4:8,8:30000})
        world.map='garner';world.own.x,world.own.y=223200,278700
        world.bag_ready=True;world.bag_capacity=48
        world.bag={0:pets.item(1847,10),1:pets.item(4602)}
        _,policy=test_alpha76.Combat76Tests().policy()
        policy.world=world;policy.nav=self.regions.nav('garner')
        policy.activity=SimpleNamespace(hunting=lambda now:True)
        policy.move_to=Mock(return_value=True)
        policy.hunt_before_errands=lambda now:True
        life=copy.copy(pets.LIFE)
        life.prices={**life.prices,3094:10000}
        shop={'position':(223300,278700),'offers':[3094]}
        life.services={'shops':{'garner':[shop]}}
        town=Town(world,life,self.regions.items,{},random.Random(1),world.own.position)
        town.xp_boosters=XPBoosters(world,life,SimpleNamespace(phase=lambda *a:'progression'))
        self.assertTrue(policy.task('town',town,lambda:town.tick(100,policy,True),100))
        self.assertEqual(town.wanted,(3094,1))
        self.assertEqual(town.visit_deadline,130)
        shop['position']=(219000,270700)
        self.assertIsNone(town.nearby_xp_boost(policy,101))
        town.pending=(3094,0,30000,150)
        world.bag[2]=pets.item(3094)
        town.tick(102,policy,False)
        self.assertEqual(town.xp_boosters.purchased_items,{})
        world.own.values[8]=20000
        town.tick(103,policy,False)
        self.assertEqual(town.xp_boosters.purchased_items,{3094:1})
        self.assertTrue(town.xp_boosters.tick(104,policy,True))
        del world.bag[2]
        world.own_states={48:1}
        town.xp_boosters.tick(105,policy,True)
        self.assertEqual(town.xp_boosters.confirmed_items,{3094:1})
