"""A reused walking corridor still checks the bot's individual destination."""
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from route_search import RoutePending
from navigation import Navigation
import test_alpha24
import test_alpha76


class NearbyCampCorridorTests(unittest.TestCase):
    def make(self):
        nav=test_alpha24.IncrementalNavigationTests().nav()
        start=(1050,1050)
        old_goal=(6050,1050)
        nav.begin_turn(expansions=25000)
        with patch('navigation.time.thread_time',return_value=0):
            original=nav.path(start,old_goal)
        nav.end_turn()
        self.assertTrue(original)
        return nav,start,old_goal

    def test_neighboring_camp_gets_checked_route_without_new_astar(self):
        nav,_,old_goal=self.make()
        start,goal=(950,1050),(6250,1050)
        expanded=nav.planning_stats()['expanded_nodes']
        nav.begin_turn(expansions=0)
        try:
            path=nav.path(start,goal)
        finally:
            nav.end_turn()
        self.assertEqual((path[0],path[-1]),(start,goal))
        self.assertIn(old_goal,path)
        self.assertEqual(nav.planning_stats()['expanded_nodes'],expanded)
        self.assertTrue(all(nav.line_clear(a,b) for a,b in zip(path,path[1:])))

    def test_an_old_search_can_yield_to_a_ready_suitable_camp(self):
        _,policy=test_alpha76.Combat76Tests().policy()
        origin=policy.world.own.position
        goal=(188350,274550)
        alternate=(188450,274550)
        policy.search_goal=goal
        policy.search_started=100
        policy.nav.camp_route_ready=Mock(return_value=True)
        policy.nav.cancel_pending=Mock()
        policy.move_to=Mock(side_effect=[RoutePending(),RoutePending(),True])
        with self.assertRaises(RoutePending):
            policy.move_to_camp(goal,[goal,alternate],110,origin)
        policy.nav.camp_route_ready.assert_not_called()
        self.assertTrue(policy.move_to_camp(goal,[goal,alternate],126,origin))
        self.assertEqual(policy.search_goal,alternate)
        policy.nav.camp_route_ready.assert_called_once_with(origin,alternate)
        policy.move_to.assert_called_with(alternate,126,use_portals=False)

    def test_wall_between_camps_requires_a_real_search(self):
        nav,_,_=self.make()
        cell=nav.cell((6150,1050))
        cells=bytearray(nav.cells)
        cells[cell[1]*nav.width+cell[0]]=0
        nav.cells=bytes(cells)
        nav.begin_turn(expansions=0)
        try:
            with self.assertRaises(RoutePending):
                nav.path((950,1050),(6250,1050))
        finally:
            nav.end_turn()

    def test_route_from_argent_to_far_west_finishes_in_normal_node_limit(self):
        nav=Navigation(Path(__file__).resolve().parents[1]/'assets'/'garner-navigation.json')
        nav.enable_incremental()
        start,goal=(214181,276634),(84850,246050)
        nav.begin_turn(expansions=25000)
        try:
            with patch('navigation.time.thread_time',return_value=0):
                path=nav.path(start,goal)
        finally:
            nav.end_turn()
        self.assertEqual((path[0],path[-1]),(start,goal))
        self.assertTrue(all(nav.line_clear(a,b) for a,b in zip(path,path[1:])))
