"""First-profession scheduling, delayed journal recovery and persistent actors."""
import dataclasses
import json
import random
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from adventure import Adventure, NPCS, talk_request
from city_travel import CityTravel, TELEPORTERS
from farm_plan import FIELDS, HuntLearning, PROFILES
from roles import RoleStore
from world import Entity
from test_adventure import role, offers, page
import test_coordination as base
from test_development import scene
from navigation import Navigation


class ProfessionSchedulingTests(unittest.TestCase):
    def policy(self, first=1):
        fixture = base.CohortCombatTests()
        fixture.nav = Navigation(ROOT / 'assets/argent-navigation.json')
        world, policy = fixture.policy(monsters=1)
        world.own.values.update({0:9, 4:0, 1:100, 31:100})
        quest = Adventure(world, policy.send, role=role(first), tactic='farm')
        quest.journal_ready = True
        policy.adventure = quest
        return world, policy, quest

    def test_dead_target_cannot_starve_real_teleporter_with_new_mobs_visible(self):
        world, policy, quest = self.policy(2)
        world.own.x, world.own.y = TELEPORTERS['garner']
        dead = world.entities[1000]
        dead.values[1] = 0
        policy.target = dead.identity
        world.entities[1001] = dataclasses.replace(dead, identity=1001, handle=2001,
            x=world.own.x+50, y=world.own.y, values={0:1, 1:50, 31:50})
        world.entities[99] = Entity(11,99,1099,2,0,*TELEPORTERS['garner'],40)
        policy.travel = CityTravel(world,policy.send,1,role(2))
        policy.tick(100)
        policy.send.assert_called_once_with(301,talk_request(99))
        self.assertEqual(policy.travel.context[1], 'menu')
        self.assertIsNone(policy.target)
        self.assertEqual(policy.kills, 1)
        self.assertEqual(policy.attacks, 0)

    def test_promotion_precedes_optional_help_shopping_and_loot(self):
        world, policy, quest = self.policy()
        world.own.x, world.own.y = NPCS['senna']
        world.entities[99] = Entity(11,99,1099,2,0,*NPCS['senna'],40)
        policy.loot = Mock()
        policy.helper = Mock()
        policy.helper.source = None
        policy.tick(100)
        policy.send.assert_called_once_with(301,talk_request(99))
        policy.loot.tick.assert_not_called()
        policy.helper.tick.assert_not_called()
        self.assertEqual(policy.attacks,0)

    def test_level_nine_clears_tutorial_delay_and_old_optional_task_pause(self):
        world, policy, quest = self.policy()
        world.own.x, world.own.y = NPCS['senna']
        world.entities[99] = Entity(11,99,1099,2,0,*NPCS['senna'],40)
        quest.next_visit = 500
        quest.context = (99,'senna','select','Welcome')
        policy.task_budget.paused['adventure'] = 500
        policy.tick(100)
        policy.send.assert_called_once_with(301,talk_request(99))
        self.assertEqual(quest.context[2],'talk')

    def test_journal_delay_retries_then_resumes_native_promotion_without_relogin(self):
        world, policy, quest = self.policy()
        quest.journal_ready = False
        world.own.x, world.own.y = NPCS['senna']
        world.entities[99] = Entity(11,99,1099,2,0,*NPCS['senna'],40)
        for now in (100,116,129,130):
            policy.tick(now)
        self.assertEqual(policy.send.call_args_list,[unittest.mock.call(325,b''),unittest.mock.call(325,b'')])
        self.assertFalse(quest.disabled)
        self.assertEqual(policy.attacks,0)
        quest.observe(828,b'\x00')
        policy.tick(131)
        policy.send.assert_called_with(301,talk_request(99))
        quest.observe(802,offers(99,[(quest.role['promotion'],1)]))
        policy.tick(132)
        self.assertEqual(quest.context[2],'select')
        quest.observe(827,page(99,quest.role['promotion']))
        policy.tick(133)
        self.assertEqual(quest.pending[0],6)
        self.assertEqual(world.own.values[4],0)
        self.assertEqual(quest.accepted,0)
        quest.observe(832,struct.pack('>HB',58,0))
        self.assertEqual(quest.accepted,1)
        self.assertEqual(quest.active(),58)

    def test_active_profession_kill_objective_still_allows_real_combat(self):
        world, policy, quest = self.policy()
        world.own.values[0] = 10
        quest.journal = {62:0}
        world.entities[1000].model = 237
        world.entities[1000].values[0] = 10
        policy.tick(100)
        self.assertEqual(policy.target,1000)
        self.assertEqual(policy.attacks,1)
        self.assertEqual(world.own.values[4],0)

    def test_wounded_traveller_recovers_instead_of_waiting_forever_for_safe(self):
        world, policy, quest = self.policy(2)
        world.own.values[1] = 50
        policy.travel = CityTravel(world,policy.send,1,role(2))
        policy.tick(100)
        self.assertTrue(policy.resting)
        self.assertEqual(world.own.values[1],50)
        self.assertEqual(policy.attacks,0)

    def test_all_four_first_jobs_follow_native_accept_and_journal_confirmation(self):
        for first,map_name,mission in ((1,'garner',58),(4,'garner',61),
                                        (2,'darkblue',59),(5,'magicsea',60)):
            with self.subTest(first=first):
                world = scene()
                world.map = map_name
                world.own.values.update({0:9,4:0})
                send = Mock()
                quest = Adventure(world,send,role=role(first),tactic='farm')
                quest.journal_ready = True
                quest.context = (99,'senna','talk',None)
                quest.prepare_priority()
                quest.context = (99,'senna','talk',None)
                quest.process_event(802,offers(99,[(quest.role['promotion'],1)]),100)
                quest.process_event(827,page(99,quest.role['promotion']),101)
                self.assertEqual(quest.pending[0],6)
                self.assertEqual(world.own.values[4],0)
                quest.observe(832,struct.pack('>HB',mission,0))
                self.assertEqual(quest.active(),mission)
                self.assertEqual(quest.accepted,1)

    def test_tutorial_does_not_pin_level_eight_to_level_three_mobs(self):
        world, policy, quest = self.policy()
        world.own.values[0] = 8
        quest.tactic = 'quests'
        quest.journal = {704:0}
        policy.region = {'farms': {'103':{'level':3,'hp':69,'points':[[1,1]],'drops':[]},
                                  '125':{'level':8,'hp':100,'points':[[2,2]],'drops':[]}}}
        quest.region = policy.region
        policy.farm_models = Mock(return_value={125})
        self.assertEqual(policy.planned_models(),{125})
        world.own.values[0] = 10
        quest.journal = {64:0}
        self.assertEqual(policy.planned_models(),{125})


class PersistentClassTests(unittest.TestCase):
    def test_update_never_creates_a_replacement_for_a_missing_saved_character(self):
        from auto_bots import ensure_character
        from classic_wire import ProtocolError
        client = Mock()
        bot = {'character':'Bot00000001','preserve_existing':True}
        with self.assertRaisesRegex(ProtocolError,'Создание замены отключено'):
            ensure_character(bot,client,[])
        client.create_character.assert_not_called()
        self.assertEqual(ensure_character(bot,client,[{'name':bot['character']}]),bot['character'])
        client.create_character.assert_not_called()

    def test_missing_or_short_data_cannot_silently_create_a_new_population(self):
        from runtime_guard import require_population
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)/'data'
            with self.assertRaisesRegex(RuntimeError,'Новые аккаунты не созданы'):
                require_population(data,200)
            self.assertFalse(data.exists())
            data.mkdir()
            state = data/'bot-local.json'
            state.write_text(json.dumps({'version':1,'bots':[{'account':'saved'}]}))
            before = state.read_bytes()
            with self.assertRaises(RuntimeError):require_population(data,200)
            self.assertEqual(require_population(data,1)['saved_bots'],1)
            self.assertEqual(state.read_bytes(),before)
            self.assertEqual(require_population(data,200,allow_new=True)['saved_bots'],1)

    def test_two_hundred_saved_actors_never_reroll_or_rewrite_registry(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'bot-roles.json'
            store = RoleStore(path,rng=random.Random(26))
            expected = [store.resolve(f'Bot{i:08x}',i%4+1,0) for i in range(200)]
            before = path.read_bytes()
            forbidden = Mock()
            forbidden.choice.side_effect = AssertionError('saved actor was rerolled')
            restored = RoleStore(path,rng=forbidden)
            for i, saved in enumerate(expected):
                self.assertEqual(restored.resolve(f'Bot{i:08x}',i%4+1,0),saved)
                self.assertEqual(restored.resolve(f'Bot{i:08x}',i%4+1,saved['first_job']),saved)
            self.assertEqual(path.read_bytes(),before)
            self.assertEqual({r['target_job'] for r in expected},{8,9,12,13,14,16})

    def test_only_new_compatible_class_is_drawn_and_then_saved(self):
        with tempfile.TemporaryDirectory() as directory:
            chooser = Mock()
            chooser.choice.return_value = 16
            store = RoleStore(Path(directory)/'roles.json',rng=chooser)
            first = store.resolve('ExistingUnassigned',1,0)
            chooser.choice.assert_called_once_with([9,12,16])
            self.assertEqual(first['target_job'],16)
            self.assertEqual(store.resolve('ExistingUnassigned',1,0),first)
            self.assertEqual(chooser.choice.call_count,1)


class ProductiveHuntingTests(unittest.TestCase):
    def test_verified_xp_rate_beats_tiny_hp_low_yield_targets(self):
        world = scene()
        world.own.values.update({0:10,1:100,31:100})
        learning = HuntLearning('progress')
        learning.profile = PROFILES[0]
        region = {'farms':{str(m):{'level':10,'hp':100 if m==4 else 1,
            'points':[[m,m]],'drops':[]} for m in (1,2,3,4)}}
        for model in (1,2,3,4):
            learning.rows[str(model)] = dict.fromkeys(FIELDS,0)
            learning.rows[str(model)].update(wins=3,seconds=100,xp=100 if model==4 else 10)
        selected = learning.choose(region,world.own,100)
        self.assertIn(4,selected)
        self.assertGreater(learning.scores[4],max(learning.scores[m] for m in (1,2,3)))
        self.assertEqual(world.own.values[0],10)


if __name__ == '__main__':
    unittest.main()
