import json
import struct
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from classic_wire import Reader, ProtocolError, string, sequence
from headless import Report, Client
from world import World, Entity, entity, attrs, HP, MAX_HP, LV
from navigation import Navigation
from hunter import Hunter, movement, normal_attack, distance

FIXTURES = json.loads((ROOT/'tests/fixtures/native_world.json').read_text())


def enter_packet():
    return (bytes(6)+string('garner')+b'\0'+bytes.fromhex(FIXTURES['own_base'])
            +b'\0\x19\0\0\0'+b'\0'+bytes.fromhex(FIXTURES['own_attrs']))


def world_fixture():
    world = World()
    world.enter(enter_packet())
    return world


class WorldTests(unittest.TestCase):
    def test_native_base_and_attribute_writer_fixtures(self):
        for label in ('own','monster','own_worn'):
            r = Reader(bytes.fromhex(FIXTURES[label+'_base']))
            actor = entity(r)
            r.end()
            self.assertEqual(actor.x,223600 if label=='monster' else 223200)
            self.assertEqual(actor.control,5 if label=='monster' else 1)
            r = Reader(bytes.fromhex(FIXTURES[label+'_attrs']))
            self.assertEqual(attrs(r)[MAX_HP],100)
            r.end()

    def test_enter_map_decodes_own_health_position_skill(self):
        world = world_fixture()
        self.assertEqual(world.own.position,(223200,278700))
        self.assertEqual(world.own.values[HP],100)
        self.assertEqual(world.map,'garner')
        self.assertEqual(world.default_skill,25)

    def test_entity_appears_updates_and_leaves(self):
        world = world_fixture()
        packet = (b'\0'+bytes.fromhex(FIXTURES['monster_base'])+bytes(4)
                  +bytes.fromhex(FIXTURES['monster_attrs'])+b'\0')
        world.observe(504,packet)
        self.assertEqual(world.entities[456].control,5)
        world.observe(509,struct.pack('>IBHB I',456,3,1,1,50))
        self.assertEqual(world.entities[456].values[HP],50)
        world.observe(505,b'\0'+struct.pack('>I',456))
        self.assertNotIn(456,world.entities)

    def test_move_uses_authoritative_first_point(self):
        world = world_fixture()
        packet = struct.pack('>IIBHH',123,1,1,1,1)+sequence(struct.pack('<iiii',223500,278500,223900,278500))
        world.observe(508,packet)
        self.assertEqual(world.own.position,(223500,278500))
        self.assertEqual(world.own.state,1)

    def test_damage_updates_hp_without_modern_state_timestamps(self):
        world = world_fixture()
        packet = (struct.pack('>IIBBHBBB',123,1,4,1,0,0,0,0)+bytes(24)+bytes(2)
                  +struct.pack('>BHBI',3,1,HP,25))
        world.observe(508,packet)
        self.assertEqual(world.own.values[HP],25)
        self.assertEqual(world.damage_events,1)

    def test_truncated_world_data_fails_before_actions(self):
        with self.assertRaises(ProtocolError):
            World().enter(enter_packet()[:35])

    def test_client_keeps_initial_visibility_until_world_handler_attaches(self):
        client = Client(Mock(),Report())
        client.service(504,b'synthetic')
        self.assertEqual(list(client.pending_world),[(504,b'synthetic')])
        handler = Mock()
        client.world_handler = handler
        client.service(505,b'gone')
        handler.assert_called_once_with(505,b'gone')


class NavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nav = Navigation(ROOT/'assets/argent-navigation.json')

    def test_all_three_native_argent_spawns_reach_hunting_area(self):
        for start in ((223200,278700),(219400,277900),(224500,270300)):
            path = self.nav.path(start,self.nav.waypoints[0])
            self.assertGreater(len(path),2)
            self.assertTrue(all(self.nav.free(self.nav.cell(point)) for point in path))
            for a,b in zip(path,path[1:]):
                ca,cb = self.nav.cell(a),self.nav.cell(b)
                if ca[0]!=cb[0] and ca[1]!=cb[1]:
                    self.assertTrue(self.nav.free((ca[0],cb[1])) and self.nav.free((cb[0],ca[1])))

    def test_outside_crop_has_no_path(self):
        self.assertFalse(self.nav.path((0,0),self.nav.waypoints[0]))


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.world = world_fixture()
        self.nav = Navigation(ROOT/'assets/argent-navigation.json')
        self.send = Mock()
        self.policy = Hunter(self.world,self.nav,self.send,Report(),lambda text:None)
        self.policy.started = 0

    def monster(self,control=5,model=75,hp=100,level=1):
        entity = Entity(model,456,1456,control,1,223300,278700,40,{HP:hp,MAX_HP:100,LV:level})
        self.world.entities[456] = entity
        return entity

    def test_attacks_weak_monster_with_real_ids_and_handle(self):
        self.monster()
        self.policy.tick(100)
        self.assertEqual(self.policy.attacks,1)
        cmd,payload = self.send.call_args.args
        self.assertEqual(cmd,6)
        self.assertEqual(payload,normal_attack(123,1,1,25,456,1456,(223200,278700)))

    def test_never_targets_players_npcs_pets_or_strong_mobs(self):
        for control,model,level in ((1,75,1),(2,75,1),(10,75,1),(5,119,7),(5,75,20)):
            candidate = self.monster(control,model,level=level)
            self.assertFalse(self.policy.eligible(candidate,100))

    def test_never_targets_corpses(self):
        self.assertFalse(self.policy.eligible(self.monster(hp=0),100))
        corpse = self.monster()
        corpse.state = 7
        self.assertFalse(self.policy.eligible(corpse,100))

    def test_low_health_retreats_and_does_not_attack(self):
        self.monster()
        self.world.own.values[HP] = 25
        self.policy.tick(100)
        self.assertTrue(self.policy.resting)
        self.assertEqual(self.policy.attacks,0)
        self.assertEqual(self.policy.mode,'отступление и восстановление')
        self.world.own.values[HP] = 90
        self.policy.tick(105)
        self.assertFalse(self.policy.resting)

    def test_unknown_or_dead_health_does_not_issue_commands(self):
        self.monster()
        self.world.own.values.pop(HP)
        self.policy.tick(100)
        self.send.assert_not_called()
        self.world.own.values[HP] = 0
        self.policy.tick(102)
        self.send.assert_not_called()

    def test_low_health_cancels_server_auto_attack_once_even_at_home(self):
        self.monster()
        self.world.own.values[HP] = 30
        self.policy.tick(100)
        _, payload = self.send.call_args.args
        self.assertEqual(payload,movement(123,1,[(223200,278700),(223200,278700)]))
        self.policy.tick(102)
        self.assertEqual(self.send.call_count,1)

    def test_request_rate_is_bounded(self):
        self.monster()
        for t in (100,100.1,100.5,101):
            self.policy.tick(t)
        self.assertEqual(self.send.call_count,1)

    def test_search_movement_is_short_and_walkable(self):
        self.policy.tick(100)
        self.assertEqual(self.policy.moves,1)
        _,payload = self.send.call_args.args
        reader = Reader(payload)
        self.assertEqual((reader.long(),reader.long(),reader.byte()),(123,1,1))
        points = list(struct.iter_unpack('<ii',reader.sequence()))
        self.assertLessEqual(sum(distance(a,b) for a,b in zip(points,points[1:])),600)
        self.assertTrue(all(self.nav.free(self.nav.cell(p)) for p in points))

    def test_bot_pauses_on_other_maps(self):
        self.world.map = 'darkblue'
        self.monster()
        self.policy.tick(100)
        self.send.assert_not_called()


if __name__=='__main__':
    unittest.main()
