"""Retreat recovers after a native movement stop at the mine."""
import unittest
from contextlib import nullcontext
from pathlib import Path

from regions import Regions
from route_search import RoutePending
from test_alpha24 import IncrementalNavigationTests
import test_alpha76


class MineRetreatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.regions=Regions(Path(__file__).resolve().parents[1]/'assets')

    def make(self):
        world,policy=test_alpha76.Combat76Tests().policy(monsters=1)
        policy.nav=self.regions.nav('garner')
        world.own.x,world.own.y=188237,275351
        world.own.values.update({1:41,31:2773})
        world.entities[1000].x,world.entities[1000].y=188630,275350
        policy.home=(224450,277750)
        policy.resting=True
        return world,policy

    def test_latched_movement_stop_cannot_block_retreat(self):
        world,policy=self.make()
        policy.stuck=5
        self.assertFalse(policy.move_to(policy.home,99))
        policy.tick(100)
        self.assertEqual(policy.retreat_replans,1)
        self.assertEqual(policy.moves,1)
        self.assertEqual(policy.attacks,0)
        self.assertTrue(policy.nav.line_clear(world.own.position,policy.retreat_goal))
        self.assertLess(policy.retreat_goal[0],world.own.x)

    def test_native_stop_changes_retreat_goal(self):
        world,policy=self.make()
        policy.tick(100)
        stopped_goal=policy.retreat_goal
        world.move_revision+=1
        world.move_packet_number=world.stop_packet_number=policy.move_packet
        world.move_state=world.stop_packet_kind=1
        policy.tick(102)
        self.assertEqual(policy.blocked_move_stops,1)
        self.assertEqual(policy.retreat_replans,1)
        self.assertEqual(policy.moves,2)
        self.assertNotEqual(policy.retreat_goal,stopped_goal)
        self.assertGreater(policy.goal_blacklist[stopped_goal],102)
        self.assertEqual(policy.attacks,0)


class RouteSharingTests(unittest.TestCase):
    def test_portal_comparison_and_hunting_continue_one_search(self):
        nav=IncrementalNavigationTests().nav()
        start,goal=(1050,1050),(6050,1050)
        nav.begin_turn(expansions=20)
        with self.assertRaises(RoutePending):
            with nav.background_work(True):
                nav.path(start,goal)
        _,search=next(iter(nav.local.searches.items()))
        nav.end_turn()
        for lane in ('foreground','background'):
            nav.begin_turn(expansions=20)
            with self.assertRaises(RoutePending):
                with nav.background_work(True) if lane=='background' else nullcontext():
                    nav.path(start,goal)
            key,active=next(iter(nav.local.searches.items()))
            self.assertEqual(len(nav.local.searches),1)
            self.assertEqual(key[4],'foreground')
            self.assertIs(active,search)
            nav.end_turn()
        for _ in range(100):
            nav.begin_turn(expansions=40)
            try:
                route=nav.path(start,goal)
                break
            except RoutePending:
                continue
            finally:
                nav.end_turn()
        else:
            self.fail('Shared route never finishes')
        nav.begin_turn(expansions=0)
        with nav.background_work(True):
            self.assertEqual(nav.path(start,goal),route)
        nav.end_turn()
