"""Regression scenarios from bot 69 and the verified route catalog."""
import struct
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock,patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from inventory import BagItem
from portal_shortcut import PortalShortcut
from regions import Regions
import test_alpha76


def ticket(identity):
    return BagItem(identity,1,0,0,0,0,0,True)


class RouteAndDefenceTests(unittest.TestCase):
    def policy(self,monsters=0):
        return test_alpha76.Combat76Tests().policy(monsters)

    def test_owned_andes_ticket_beats_long_walk_from_argent_to_same_camp(self):
        world,policy=self.policy()
        regions=Regions(ROOT/'assets')
        policy.nav=regions.nav('garner')
        world.own.x,world.own.y=223200,278700
        world.own.values.update({0:40,1:100,31:100,2:150,32:150})
        world.bag_ready=True
        world.bag={5:ticket(3051),6:ticket(4602)}
        shortcut=PortalShortcut(world,Mock(),regions.portal_catalog,regions.hunting_travel_data)
        self.assertTrue(shortcut.consider((103250,268150),100,policy))
        self.assertEqual(shortcut.ticket[0],3051)
        self.assertGreater(shortcut.savings_seconds,100)
        self.assertTrue(shortcut.resume(101,policy))
        world.own.x,world.own.y=101800,297500
        self.assertTrue(shortcut.resume(102,policy))
        del world.bag[5]
        self.assertFalse(shortcut.resume(103,policy))
        self.assertEqual(shortcut.arrivals,1)

    def test_argent_ticket_is_not_a_shortcut_to_valhalla_merchant(self):
        world,policy=self.policy()
        regions=Regions(ROOT/'assets')
        policy.nav=regions.nav('garner')
        world.own.x,world.own.y=135726,268849
        world.own.values.update({0:40,1:100,31:100,2:150,32:150})
        world.bag_ready=True
        world.bag={6:ticket(4602)}
        shortcut=PortalShortcut(world,Mock(),regions.portal_catalog,regions.hunting_travel_data)
        self.assertFalse(shortcut.consider((112250,276450),100,policy))
        self.assertFalse(shortcut.busy)

    def test_native_attacker_interrupts_far_target_even_outside_hunting_plan(self):
        world,policy=self.policy(2)
        world.own.values.update({0:40,4:9,1:1000,31:1000})
        world.entities[1001].model=136
        world.entities[1001].values[0]=33
        policy.planned_models=lambda:{75}
        policy.region={"farms":{}}
        policy.target=1000
        policy.next_action=110
        before=world.combat_revision
        payload=(struct.pack('>IIB',world.own_id,5,4)+b'\0'*6
                 +struct.pack('>I',1001)+b'\0'*22+struct.pack('>BHBI',0,1,1,910))
        with patch('world.time.monotonic',return_value=100):
            world.observe(508,payload)
        self.assertGreater(world.combat_revision,before)
        self.assertTrue(policy.wake_for_combat(100.01))
        policy.tick(100.01)
        self.assertEqual(policy.target,1001)
        self.assertEqual(policy.attacks,1)

    def test_combined_strike_from_motion_waits_for_stop_and_rechecks_route(self):
        world,policy=self.policy(1)
        x,y=world.own.position
        target=world.entities[1000]
        target.x,target.y=x+700,y
        policy.move_to((x+1100,y),99)
        policy.clock=100
        self.assertTrue(policy.attack_on_approach(100,target,(x+620,y),None,None))
        self.assertEqual(policy.attacks,0)
        self.assertTrue(policy.flush_action(100.2))
        self.assertEqual(policy.attacks,0)
        world.stop_revision+=1
        world.stop_packet_kind=1
        world.stop_packet_number=policy.last_sent_sequence
        self.assertTrue(policy.flush_action(100.21))
        self.assertEqual(policy.attacks,1)
        body=policy.send.call_args.args[1]
        self.assertEqual(struct.unpack('<iiii',body[13:29]),(x,y,x+620,y))
