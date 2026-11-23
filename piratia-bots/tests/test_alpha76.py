"""Live-fleet bottleneck regressions from Alpha75."""
import struct
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from equipment import Equipment
from inventory import BagItem
from regions import Regions
from route_search import RoutePending
from test_hunt import FIXTURES
import test_alpha11
import test_alpha24
import test_alpha44


class Combat76Tests(unittest.TestCase):
    def policy(self,monsters=0):
        world,policy=test_alpha24.ProgressAndDeathTests().policy(monsters)
        policy.fast_progression=True
        return world,policy

    def test_native_mob_appearance_wakes_a_waiting_hunter(self):
        world,policy=self.policy()
        policy.next_action=102
        before=world.combat_revision
        packet=(b'\0'+bytes.fromhex(FIXTURES['monster_base'])+bytes(4)
                +bytes.fromhex(FIXTURES['monster_attrs'])+b'\0')
        world.observe(504,packet)
        self.assertGreater(world.combat_revision,before)
        self.assertTrue(policy.wake_for_combat(100))
        self.assertEqual(policy.next_action,100)
        self.assertFalse(policy.wake_for_combat(100.05))

    def test_confirmed_stop_wakes_queued_attack_only_after_earliest_send(self):
        world,policy=self.policy(1)
        policy.move_to((224500,278700),99)
        world.move_revision+=1
        world.move_state=0
        policy.tick(100)
        self.assertIsNotNone(policy.pending_action)
        world.stop_revision+=1
        world.stop_packet_number=policy.last_sent_sequence
        world.stop_packet_kind=1
        self.assertFalse(policy.wake_for_combat(100.05))
        self.assertTrue(policy.wake_for_combat(100.16))
        policy.tick(100.16)
        self.assertEqual(policy.attacks,1)

    def test_second_mob_is_tried_when_first_approach_waits_on_routing(self):
        world,policy=self.policy(2)
        point=world.own.position
        world.entities[1000].x=point[0]+600
        world.entities[1001].x=point[0]+700
        world.entities[1000].y=world.entities[1001].y=point[1]
        def approach(mob,*args,**kwargs):
            if mob.identity==1000:raise RoutePending()
            return point[0]+620,point[1]
        policy.approach=Mock(side_effect=approach)
        policy.tick(100)
        self.assertEqual(policy.target,1001)
        self.assertEqual(policy.approach_attacks,1)
        body=policy.send.call_args.args[1]
        self.assertEqual(body[8],2)
        self.assertEqual(struct.unpack('<iiii',body[13:29]),(*point,point[0]+620,point[1]))
        self.assertEqual(struct.unpack('>III',body[-12:])[1:],(1001,world.entities[1001].handle))

    def test_combined_attack_respects_blocked_approach(self):
        world,policy=self.policy(1)
        policy.nav.line_clear=Mock(return_value=False)
        self.assertFalse(policy.attack_on_approach(100,world.entities[1000],(223300,278700),None,None))
        policy.send.assert_not_called()

    def test_goldie_departure_uses_a_verified_direct_ground_route(self):
        world,policy=self.policy()
        policy.nav=Regions(ROOT/'assets').nav('garner')
        world.own.x,world.own.y=219730,270369
        policy.learning.last_progress_at=50
        self.assertFalse(policy.leave_goldie_area(139))
        self.assertTrue(policy.leave_goldie_area(150))
        self.assertEqual(policy.move_goal,(219650,272350))
        self.assertTrue(policy.nav.line_clear(world.own.position,policy.move_goal))


class Equipment76Tests(unittest.TestCase):
    def test_optional_equipment_waits_for_fight_and_requires_bag_confirmation(self):
        world,policy=test_alpha24.ProgressAndDeathTests().policy()
        world.bag={4:test_alpha11.item(289)}
        world.bag_ready=True
        equipment=Equipment(world,test_alpha11.CATALOG,Mock())
        equipment.progression_first=True
        policy.local_combat_ready=Mock(return_value=True)
        self.assertFalse(equipment.tick(10,policy))
        policy.local_combat_ready.return_value=False
        self.assertTrue(equipment.tick(16,policy))
        world.own.equipment[2]=289
        equipment.tick(17,policy)
        self.assertEqual(equipment.confirmed,0)
        world.bag.pop(4)
        equipment.tick(18,policy)
        self.assertEqual(equipment.confirmed,1)
        self.assertEqual(equipment.next_optional,76)

    def test_bank_relief_keeps_patchouli_and_one_gem(self):
        world,_,market,policy,bank=test_alpha44.BankTests().make()
        market.catalog.items[860]={'category':'gem'}
        market.reserve_count=Mock(return_value=10)
        market.protected=Mock(return_value=set())
        market.useful_gear=Mock(return_value=False)
        gem=BagItem(860,1,100,100,1,1,0,True)
        patchouli=BagItem(1000,24,100,100,0,0,0,True)
        world.bag={2:gem,3:gem,4:gem,5:patchouli}
        bank.inventory_relief=True
        self.assertEqual([(slot,item.identity) for slot,item,_ in bank.candidates(policy)],[(4,860)])
