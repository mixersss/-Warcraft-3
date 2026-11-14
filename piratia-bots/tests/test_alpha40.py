"""No-fight areas, safe firing positions and native immune termination."""
import copy
import dataclasses
import json
import struct
import sys
import threading
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from navigation import Navigation
from hunter import normal_attack
import test_coordination as base
import test_alpha19 as phases


def zone_nav():
    n=Navigation.__new__(Navigation);n.map='garner';n.origin=(2220,2770)
    n.width=n.height=40;n.cells=bytes([1])*1600;n.local=threading.local()
    n.waypoints=[(222450,277450)];bits=bytearray(200)
    for y in range(40):
        for x in range(13,40):
            i=y*40+x;bits[i//8]|=1<<(7-i%8)
    n.combat_bits=bytes(bits);n.combat_zone_revision='test-native-no-fight'
    return n


class SafeTargetTests(unittest.TestCase):
    def policy(self,monsters=1):
        f=base.CohortCombatTests();f.nav=Navigation(ROOT/'assets/argent-navigation.json')
        w,p=f.policy(monsters=monsters);p.nav=zone_nav();p.route=[0]
        return w,p

    def test_protected_monster_is_not_attacked_and_bot_continues_farm_route(self):
        w,p=self.policy();p.tick(100)
        self.assertEqual(p.attacks,0);self.assertIsNone(p.target);self.assertGreater(p.moves,0)
        self.assertGreater(p.protected_target_checks,0)
        self.assertEqual(p.last_protected_target['model'],75)
        self.assertNotIn(1000,p.blacklist)

    def test_protected_bear_does_not_exclude_another_monster_of_same_species(self):
        w,p=self.policy(monsters=2)
        w.entities[1001].x=223100;p.tick(100)
        self.assertEqual(p.target,1001);self.assertEqual(p.attacks,1)
        self.assertEqual(w.entities[1000].model,w.entities[1001].model)

    def test_moving_into_protection_cancels_attack_before_next_attack_timer(self):
        w,p=self.policy();w.entities[1000].x=223100;p.tick(100)
        self.assertEqual(p.attacks,1)
        w.entities[1000].x=223300;p.tick(100.1)
        self.assertIsNone(p.target);self.assertEqual(p.protected_fights_stopped,1)
        self.assertEqual(p.send.call_args.args,(7,b''));self.assertEqual(p.attacks,1)
        self.assertNotIn(1000,p.blacklist)
        self.assertEqual(w.entities[1000].values[1],100)

    def test_monster_can_be_selected_again_after_server_moves_it_outside(self):
        w,p=self.policy();w.entities[1000].x=223100;p.tick(100)
        w.entities[1000].x=223300;p.tick(100.1)
        w.entities[1000].x=223100;p.tick(101)
        self.assertEqual(p.target,1000);self.assertEqual(p.attacks,2)

    def test_queued_attack_is_dropped_if_target_enters_protection(self):
        w,p=self.policy();w.entities[1000].x=223300
        body=normal_attack(w.own_id,5,1,w.default_skill,1000,w.entities[1000].handle,w.own.position)
        p.pending_action=(body,100,101,0)
        self.assertTrue(p.flush_action(102))
        self.assertIsNone(p.pending_action);self.assertEqual(p.attacks,0);p.send.assert_not_called()

    def test_bot_in_protection_walks_to_legal_firing_position(self):
        w,p=self.policy();w.own.x=223350;w.entities[1000].x=223250
        p.tick(100)
        self.assertEqual(p.target,1000);self.assertEqual(p.attacks,0);self.assertGreater(p.moves,0)
        self.assertTrue(p.nav.combat_allowed(p.move_endpoint))
        self.assertEqual(w.own.x,223350) # No fabricated movement out of safe area.

    def test_combined_immune_and_off_bits_release_target_immediately(self):
        w,p=self.policy(monsters=2)
        w.entities[1000].x=223100;w.entities[1001].x=223050;p.tick(100)
        first=p.target
        phases.ActionPhaseTests().skill(w,p,64|1024)
        p.tick(101)
        self.assertNotEqual(p.target,first);self.assertEqual(p.immune_fights_released,1)
        self.assertGreater(p.blacklist[first],101)

    def test_damage_in_legal_area_preserves_productive_fight(self):
        w,p=self.policy();w.entities[1000].x=223100;p.tick(100)
        for now in (102,104,106,108):
            w.entities[1000].values[1]-=10;p.tick(now)
        self.assertEqual(p.target,1000);self.assertEqual(p.attacks,1)
        self.assertEqual(p.protected_fights_stopped,0)

    def test_bot_help_request_for_protected_target_is_refused_without_idle_assist(self):
        import test_alpha21 as cooperative
        w,p,s,person,c=cooperative.CooperativeTests().make();p.nav=zone_nav()
        self.assertTrue(c.hear(77,s.name+', помоги с мобом!',101))
        self.assertEqual(c.refusals,1);self.assertEqual(c.accepts,0)
        self.assertIsNone(p.helper.source);self.assertEqual(p.attacks,0)

    def test_active_assistance_ends_when_target_enters_protected_area(self):
        from help_player import HelpPlayer
        w,p=self.policy();w.entities[1000].x=223100
        w.entities[77]=dataclasses.replace(w.own,identity=77,control=1)
        helper=HelpPlayer(w);helper.request_bot(77,1000,100,p)
        w.entities[1000].x=223300
        self.assertFalse(helper.tick(101,p));self.assertIsNone(helper.source)
        self.assertIsNone(p.assist_target)


class RealZoneTests(unittest.TestCase):
    def test_farm_destinations_do_not_lead_into_protected_regions(self):
        regions=json.loads((ROOT/'assets/regions.json').read_text())
        for name,region in regions.items():
            n=Navigation(ROOT/'assets'/region['navigation'])
            for record in region['farms'].values():
                for point in record['points']:self.assertTrue(n.combat_allowed(point),(name,point))
        self.assertTrue(regions['garner']['farms']['258']['points'])

    def test_actual_argent_and_mine_safety_flags_do_not_block_walking(self):
        n=Navigation(ROOT/'assets/garner-navigation.json')
        self.assertEqual(n.combat_zone_revision,'alpha40-native-no-fight-v1')
        for point in ((223200,278700),(188351,280526)):
            self.assertFalse(n.combat_allowed(point))
            self.assertIsNotNone(n.nearest(point,6))
        self.assertTrue(n.combat_allowed((195000,256300)))
        self.assertTrue(n.combat_allowed((189927,277527))) # Report14 actor's tile is not protected.

    def test_full_garner_and_argent_crop_use_identical_combat_flags(self):
        full=Navigation(ROOT/'assets/garner-navigation.json');crop=Navigation(ROOT/'assets/argent-navigation.json')
        for x in range(1900,2450,17):
            for y in range(2400,2900,13):
                p=(x*100+50,y*100+50)
                self.assertEqual(full.combat_allowed(p),crop.combat_allowed(p))
        self.assertFalse(crop.combat_allowed((0,0)))

    def test_all_twenty_nine_maps_have_native_combat_masks(self):
        catalog=json.loads((ROOT/'assets/world-navigation.json').read_text())
        for name,info in catalog['maps'].items():
            n=Navigation(ROOT/'assets'/info['navigation'])
            self.assertIsNotNone(n.combat_bits,name)
            self.assertEqual(len(n.combat_bits),(n.width*n.height+7)//8)
        self.assertFalse(Navigation(ROOT/'assets/garner-navigation.json').combat_allowed(None))


if __name__=='__main__':unittest.main()
