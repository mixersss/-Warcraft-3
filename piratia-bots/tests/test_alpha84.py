"""Progression regressions for native rewards, target ranking and short routes."""
import struct
import unittest
from unittest.mock import Mock

from hunt_travel import HuntTravel
import test_alpha76
import test_alpha79


class ProgressionTests(unittest.TestCase):
    def test_reward_arriving_after_target_release_is_still_learned(self):
        world,policy=test_alpha76.Combat76Tests().policy(1)
        mob=world.entities[1000]
        world.own.values[15]=1000
        policy.learning.async_rewards=True
        policy.target=mob.identity
        policy.learning.begin(world,mob,100)
        mob.values[1]=0
        world.own_hits[mob.identity]=(102,True)
        policy.learning.observe(world,102)
        policy.drop_target()
        self.assertEqual(len(policy.learning.pending_rewards),1)
        world.observe(509,struct.pack('>IBHBI',world.own_id,0,1,15,2400))
        policy.learning.observe(world,103)
        stats=policy.learning.rows[str(mob.model)]
        self.assertEqual((stats['wins'],stats['level_xp'],stats['level_seconds']),(1,1400,2))

    def test_paid_travel_compares_observed_and_predicted_xp_in_same_units(self):
        world,policy=test_alpha76.Combat76Tests().policy()
        world.own.values.update({0:55,4:8,31:4000,33:200,34:200,35:150,42:1000})
        travel=HuntTravel.__new__(HuntTravel)
        travel.world=world
        travel.knowledge={
            1:{'level':55,'base_xp':100,'hp':400,'attack_max':100},
            2:{'level':55,'base_xp':200,'hp':400,'attack_max':100},
        }
        self.assertEqual(travel.rate(1,policy,100),50)
        policy.learning.note_server_xp_rate(14)
        policy.learning.session_combat_rates[(55,1)]=(2,2800,4)
        self.assertEqual(travel.rate(1,policy,100),50)
        self.assertGreater(travel.rate(2,policy,100),travel.rate(1,policy,100))
        policy.learning.note_server_xp_rate(10)
        self.assertFalse(policy.learning.session_combat_rates)

    def test_ground_target_prefers_better_xp_per_second_over_nearest_distance(self):
        world,policy=test_alpha76.Combat76Tests().policy(2)
        first,second=(world.entities[i] for i in (1000,1001))
        first.model,second.model=301,302
        world.own.values.update({0:35,4:8,1:1500,31:1500,33:200,34:200,35:100,42:1000,44:480})
        for mob in (first,second):mob.values.update({0:35,1:600,31:600})
        first.x,first.y=world.own.position
        second.x,second.y=first.x+500,first.y
        policy.mob_knowledge={
            301:{'level':35,'base_xp':110,'hp':600,'attack_max':90},
            302:{'level':35,'base_xp':600,'hp':600,'attack_max':90},
        }
        self.assertLess(policy.target_score(second,100),policy.target_score(first,100))

    def test_near_fight_can_cancel_long_camp_search_before_pathing(self):
        world,policy=test_alpha76.Combat76Tests().policy(1)
        mob=world.entities[1000]
        mob.x,mob.y=world.own.x+600,world.own.y
        policy.search_goal=(184950,265650)
        policy.nav.nearest=Mock(side_effect=lambda p,_:p)
        policy.nav.line_clear=Mock(return_value=False)
        policy.nav.pending_farm_search=Mock(return_value=('camp key',398))
        policy.nav.cancel_pending=Mock()
        policy.nav.path=Mock(return_value=[world.own.position,mob.position])
        self.assertIsNotNone(policy.approach(mob,180,100))
        policy.nav.cancel_pending.assert_called_once_with(policy.search_goal)

    def test_visible_mobs_without_xp_do_not_hold_travel_indefinitely(self):
        world,travel,policy=test_alpha79.MineAndReactionTests().planned_mine()
        policy.local_combat_ready=lambda now:True
        policy.learning.last_progress_at=100
        self.assertFalse(travel.tick(110,policy,True))
        policy.move_to.assert_not_called()
        self.assertTrue(travel.tick(221,policy,True))
        policy.move_to.assert_called_once()

    def test_idle_workers_wait_longer_but_combat_still_wakes(self):
        world,policy=test_alpha76.Combat76Tests().policy(1)
        self.assertEqual(policy.decision_interval(0,None),.30)
        self.assertTrue(policy.wake_for_combat(100))
        policy.target=world.entities[1000].identity
        self.assertEqual(policy.decision_interval(0,None),.15)
