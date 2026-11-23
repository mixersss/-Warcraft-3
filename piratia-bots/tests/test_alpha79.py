"""Live-fleet regressions for the mine approach and combat reaction."""
import dataclasses
import struct
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from route_search import RoutePending
import test_travel58
import test_alpha76


class MineAndReactionTests(unittest.TestCase):
    def planned_mine(self):
        fixture=test_travel58.Travel58Tests()
        world,travel,policy=fixture.make()
        travel.plan=dict(fixture.plan(world,'event'),name='Silver Mine 1 to Silver Mine 2',
                         position=[178614,264696],arrival_cm=[22967,2878],to_map='eastgoaf',event_model=193,event_id=6)
        travel.target_started=100
        return world,travel,policy

    def test_selected_mine_is_kept_when_an_old_camp_route_is_active(self):
        world,travel,policy=self.planned_mine()
        policy.camp_route_active=lambda now:True
        policy.search_goal=(113120,273504)
        travel.next_check=900
        travel.economy.phase=lambda *args:'trade'
        self.assertTrue(travel.tick(110,policy,True))
        self.assertEqual(travel.plan['name'],'Silver Mine 1 to Silver Mine 2')
        policy.move_to.assert_called_once()

    def test_mine_path_search_progress_is_distinct_from_stationary_failure(self):
        _,travel,_=self.planned_mine()
        self.assertFalse(travel.approach_expired(100,travel.plan,('same search',100)))
        self.assertFalse(travel.approach_expired(140,travel.plan,('same search',200)))
        self.assertTrue(travel.approach_expired(175,travel.plan,('same search',200)))

    def test_pending_mine_search_does_not_restart_previous_hunt_walk(self):
        world,policy=test_alpha76.Combat76Tests().policy()
        _,travel,_=self.planned_mine()
        travel.world=world
        travel.tick=Mock(side_effect=RoutePending)
        policy.hunt_travel=travel
        policy.search_goal=(190050,261050)
        policy.move_to=Mock()
        policy.tick(120)
        self.assertIsNone(policy.search_goal)
        self.assertEqual(policy.mode,'строит путь к выбранному входу в шахту')
        policy.move_to.assert_not_called()

    def test_current_attacker_is_answered_before_optional_equipment(self):
        world,policy=test_alpha76.Combat76Tests().policy(monsters=1)
        target=world.entities[1000]
        world.own_attackers[target.identity]=(target.handle,100)
        policy.equipment=Mock(context=None,pending=None)
        policy.equipment.tick.return_value=True
        policy.tick(100.05)
        self.assertEqual(policy.attacks,1)
        self.assertEqual(policy.immediate_defences,1)
        policy.equipment.tick.assert_not_called()

    def test_mine_door_request_and_arrival_are_counted_separately(self):
        world,travel,policy=self.planned_mine()
        world.own.x,world.own.y=travel.plan['position']
        world.entities[90]=dataclasses.replace(world.own,identity=90,model=193,
                                               event_id=6,event_identity=90)
        self.assertTrue(travel.tick(101,policy,True))
        self.assertEqual(travel.mine_requests,1)
        self.assertEqual(travel.mine_arrivals,0)
        self.assertTrue(travel.tick(102,policy,True))
        world.map='eastgoaf'
        world.own.x,world.own.y=22967,2878
        self.assertFalse(travel.tick(103,policy,True))
        self.assertEqual(travel.mine_arrivals,1)
        self.assertEqual(travel.last_arrival['map'],'eastgoaf')

    def test_mine_xp_requires_positive_own_server_attribute_update(self):
        world,_=test_alpha76.Combat76Tests().policy()
        world.map='eastgoaf'
        world.own.values[15]=100
        payload=lambda identity,xp:struct.pack('>IBHBI',identity,0,1,15,xp)
        world.observe(509,payload(99999,1000))
        world.observe(509,payload(world.own_id,80))
        world.observe(509,payload(world.own_id,140))
        world.map='garner'
        world.observe(509,payload(world.own_id,155))
        self.assertEqual(world.summary()['xp_gained_from_attribute_updates_by_map'],{'eastgoaf':60,'garner':15})
