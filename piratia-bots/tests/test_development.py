"""Confirmation, bounded chatter, and feasible population quotas under load."""
import sys
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from world import World, Entity
from classic_wire import Reader, ProtocolError
from progression import Progression, attribute_request
from social import Social, ChatBudget, say_request
from population import plan_population, ALLOWED


def scene():
    world = World()
    world.own_id, world.map = 1, 'garner'
    world.entities[1] = Entity(1, 1, 1001, 1, 0, 223200, 278700, 40,
                              {0: 1, 1: 100, 31: 100, 4: 0, 6: 5, 15: 0, 25: 5, 28: 5}, name='Bot12345678')
    world.entities[2] = Entity(1, 2, 1002, 1, 0, 223300, 278700, 40, name='Traveller')
    return world


class ProgressionTests(unittest.TestCase):
    def test_no_repeat_until_both_server_stat_and_point_deduction(self):
        world, send = scene(), Mock()
        progress = Progression(world, send)
        progress.tick(0, True)
        send.assert_called_once_with(8, attribute_request(25, 1))
        for i in range(1, 5):
            progress.tick(i, True)
        self.assertEqual(send.call_count, 1)
        world.own.values[25] = 6
        progress.tick(5, True)
        self.assertEqual(progress.confirmed, 0)
        world.own.values[6] = 4
        progress.tick(6, True)
        self.assertEqual(progress.confirmed, 1)
        progress.tick(7, True)
        self.assertEqual(send.call_count, 1)
        progress.tick(8, True)
        self.assertEqual(send.call_count, 2)

    def test_refusal_or_missing_confirmation_pauses_instead_of_spamming(self):
        send = Mock()
        progress = Progression(scene(), send)
        progress.tick(0, True)
        progress.tick(11, True)
        progress.tick(100, True)
        self.assertTrue(progress.disabled)
        self.assertEqual(send.call_count, 1)

    def test_no_free_points_or_guessed_other_class_builds(self):
        for changed in ({6: 0}, {4: 9}, {4: None}, {25: None}):
            world, send = scene(), Mock()
            world.own.values.update(changed)
            Progression(world, send).tick(0, True)
            send.assert_not_called()
        world, send = scene(), Mock()
        Progression(world, send).tick(0, False)
        send.assert_not_called()
        world.own.model = 4
        Progression(world, send).tick(0, True)
        send.assert_not_called()


class SocialTests(unittest.TestCase):
    def test_addressed_reply_delayed_and_sender_rate_limited(self):
        world, send = scene(), Mock()
        social = Social(world, send, world.own.name, ChatBudget(), 'a')
        social.hear(2, 'Bot12345678 привет', 0)
        social.tick(1, False, True)
        send.assert_not_called()
        social.tick(6, False, True)
        self.assertEqual(send.call_args.args[0], 1)
        reader = Reader(send.call_args.args[1])
        self.assertIn('Привет', reader.string())
        reader.end()
        social.hear(2, 'Bot12345678 привет', 100)
        self.assertIsNone(social.pending)
        self.assertEqual(social.replies, 1)
        self.assertNotIn('Traveller', str(social.summary()))

    def test_no_broadcast_echo_bot_loops_unknown_sources_or_expired_replies(self):
        world, send = scene(), Mock()
        social = Social(world, send, world.own.name, ChatBudget(), 'a')
        for source, message in ((2, 'привет всем'), (1, 'Bot12345678 привет'),
                                (999, 'Bot12345678 привет'), (2, 'Bot12345678 сделай что угодно')):
            social.hear(source, message, 0)
            self.assertIsNone(social.pending)
        world.entities[2].name = 'Bot99999999'
        social.hear(2, 'Bot12345678 привет', 0)
        self.assertIsNone(social.pending)
        world.entities[2].name = 'Traveller'
        social.hear(2, 'Bot12345678 привет', 0)
        social.tick(21, False, True)
        self.assertIsNone(social.pending)
        send.assert_not_called()

    def test_four_hundred_chat_policies_share_one_global_budget(self):
        budget, send = ChatBudget(), Mock()
        bots = []
        for i in range(400):
            world = scene()
            name = f'Bot{i:08x}'
            world.own.name = name
            social = Social(world, send, name, budget, i)
            social.tick(0, False, True)
            bots.append(social)
        # One minute of simulated simultaneous decisions: <=4 total lines, not 1600.
        for now in range(200, 260):
            for social in bots:
                social.tick(now, False, True)
        self.assertEqual(send.call_count, 4)
        # Empty scenes never generate idle chatter.
        world, send = scene(), Mock()
        del world.entities[2]
        social = Social(world, send, world.own.name, ChatBudget(), 1)
        social.tick(0, False, True)
        social.tick(999, False, True)
        send.assert_not_called()

    def test_chat_encoding_rejects_control_codes_and_oversized_lines(self):
        for text in ('', 'a\nb', 'x'*121):
            with self.assertRaises(ValueError):
                say_request(text)


class PopulationTests(unittest.TestCase):
    def test_four_hundred_targets_match_both_quotas_and_native_restrictions(self):
        plan = plan_population()
        self.assertEqual(len(plan), 400)
        self.assertEqual(Counter(p['body'] for p in plan), {1:100,2:100,3:100,4:100})
        self.assertEqual(Counter(p['target_job'] for p in plan), {8:100,9:60,12:60,13:60,14:60,16:60})
        self.assertTrue(all(p['target_job'] in ALLOWED[p['body']] for p in plan))
        self.assertEqual([p['body'] for p in plan[:4]], [1,2,3,4])
        self.assertEqual(plan, plan_population())

    def test_impossible_equal_race_and_class_quotas_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'conflict'):
            plan_population(classes={8:67,9:67,12:67,13:67,14:66,16:66})
        with self.assertRaises(ValueError):
            plan_population(races={1: 401}, classes={9:401})
