import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from classic_wire import string, Reader, ProtocolError
from adventure import Adventure, NPCS, mission_page, talk_request, select_request, commit_request, FARMS
from roles import RoleStore
from loot import QuestLoot
from headless import creation_look
from navigation import Navigation
from hunter import Hunter
from world import Entity, World
from test_development import scene


def offers(npc, entries):
    # Supplied NpcSdk.SendMissionPage writes command802, native world ID/page,
    # ordinary dialogue/functions, then quest names and server availability bits.
    return (struct.pack('>IB',npc,1)+string('NPC dialogue')+b'\x01'+string('Trade')
            +bytes([len(entries)])+b''.join(string(t)+bytes([state]) for t,state in entries))


def page(npc,title,button=6,needs=(),choice=1,prizes=()):
    result = bytes([button])+struct.pack('>I',npc)+string(title)+bytes([len(needs)])
    for kind,identity,count,done in needs:
        result += struct.pack('>BHHB',kind,identity,count,done)
    result += bytes([choice,len(prizes)])+b''.join(struct.pack('>BHH',*prize) for prize in prizes)
    return result+string('Description')


def role(first):
    return {'first_job':first,'target_job':{1:9,2:12,4:16,5:13}[first],
            'promotion':{1:'Swordsman Promotion',2:'Hunter Promotion',4:'Explorer Promotion',5:'Herbalist Promotion'}[first],
            'label':str(first)}


class QuestTests(unittest.TestCase):
    def make(self,first=1):
        w,send = scene(),Mock()
        quest = Adventure(w,send,role=role(first))
        quest.journal_ready = True
        policy = Mock()
        policy.position.side_effect = lambda now: w.own.position
        policy.target = None
        return w,send,quest,policy

    def test_offer_and_page_both_filter_other_class(self):
        for first in (1,2,4,5):
            w,send,q,p = self.make(first)
            w.own.values[0] = 9
            q.context = 99,'senna','talk',None
            wrong = [role(i)['promotion'] for i in (1,2,4,5) if i!=first]
            q.process_event(802,offers(99,[(title,1) for title in wrong]+[(role(first)['promotion'],1)]),1)
            send.assert_called_once_with(301,select_request(99,3))
            send.reset_mock()
            # Even a mismatched response after selection cannot commit a wrong profession.
            q.process_event(827,page(99,wrong[0]),2)
            send.assert_not_called()
            q.process_event(827,page(99,role(first)['promotion']),2)
            send.assert_called_once_with(301,commit_request(99,6))

    def test_native_server_journal_capture(self):
        fixture = json.loads((ROOT/'tests/fixtures/native_missions.json').read_text())
        packet = bytes.fromhex(fixture['journal_packet'])
        w,send,q,p = self.make()
        q.observe(int.from_bytes(packet[:2],'big'),packet[2:])
        self.assertEqual(q.journal,{701:0,62:1})
        self.assertTrue(q.journal_ready)

    def test_stats_follow_pinned_class_before_promotion(self):
        from progression import Progression,attribute_request
        for first,primary,body in ((1,25,1),(2,26,1),(4,29,1),(5,29,4)):
            world,send = scene(),Mock()
            world.own.model = body
            world.own.values[primary] = 5
            Progression(world,send,first).tick(0,True)
            send.assert_called_once_with(8,attribute_request(primary,6))

    def test_native_journal_accepted_and_delivered_require_notifications(self):
        w,send,q,p = self.make()
        q.observe(828,b'\x01'+struct.pack('>HB',1,1))
        self.assertEqual(q.active(),1)
        q.context = 99,'senna','select','Welcome'
        q.process_event(827,page(99,'Welcome',7),1)
        self.assertEqual(q.delivered,0)
        q.observe(831,struct.pack('>H',1))
        self.assertEqual(q.delivered,1)
        self.assertFalse(q.journal)
        q.context = 99,'senna','select',"Blacksmith's Greetings"
        q.process_event(827,page(99,"Blacksmith's Greetings",6),2)
        self.assertEqual(q.accepted,0)
        q.observe(832,struct.pack('>HB',701,0))
        self.assertEqual(q.accepted,1)
        self.assertEqual(q.active(),701)

    def test_pending_greeting_visits_letter_recipient_and_returns_to_guide(self):
        w,send,q,p = self.make()
        q.journal = {701:0}
        q.context = 99,'senna','select',"Blacksmith's Greetings"
        q.process_event(827,page(99,"Blacksmith's Greetings",8),1)
        self.assertEqual(q.choose_destination(),'goldie')
        send.assert_not_called()
        q.context = 100,'goldie','select',"Blacksmith's Greetings"
        q.process_event(827,page(100,"Blacksmith's Greetings",7),2)
        q.process_event(803,struct.pack('>I',100),3)
        self.assertEqual(q.choose_destination(),'senna')
        self.assertEqual(q.delivered,0)  # Intermediate flag change is not full quest completion.

    def test_server_counts_control_kill_and_item_objectives(self):
        w,send,q,p = self.make()
        w.own.values[0] = 10
        q.journal = {62:0}
        self.assertEqual(q.desired_models(),{237})
        self.assertEqual(q.farm(),(237,None))
        q.observe(830,struct.pack('>HB',62,1))
        self.assertIsNone(q.farm())
        self.assertEqual(q.choose_destination(),'peter')
        q.journal = {64:0}
        self.assertEqual(q.farm(),(125,1678))
        self.assertEqual(q.desired_models(),{125})

    def test_explorer_uses_own_argent_chain_and_own_item(self):
        w,send,q,p = self.make(4)
        w.own.values[0] = 10
        for identity,destination in ((61,'daniel'),(158,'daniel'),(159,'william'),(160,'william'),(161,'daniel')):
            q.journal = {identity:0}
            self.assertEqual(q.choose_destination(),destination)
        self.assertEqual(q.farm(),None)  # The final delivery has no grind.
        q.journal = {160:0}
        self.assertEqual(q.farm(),(104,1595))
        self.assertNotIn(58,q.destinations)

    def test_other_map_class_waits_without_taking_swordsman_route(self):
        for first,identity in ((2,59),(5,60)):
            w,send,q,p = self.make(first)
            w.own.values[0] = 10
            q.journal = {identity:0}
            self.assertFalse(q.tick(20,p))
            send.assert_not_called()
            p.move_to.assert_not_called()
            self.assertIn('другую карту',q.reason)

    def test_existing_foreign_class_quest_is_not_cancelled_or_progressed(self):
        w,send,q,p = self.make(2)
        q.journal = {58:0}
        self.assertFalse(q.tick(20,p))
        send.assert_not_called()
        self.assertEqual(q.journal,{58:0})
        self.assertIn('другой профессии',q.reason)

    def test_no_offers_timeout_and_unsupported_choice_do_not_spam(self):
        w,send,q,p = self.make()
        q.context = 99,'senna','talk',None
        q.process_event(802,offers(99,[('Unknown quest',1)]),1)
        self.assertEqual(q.next_visit,121)
        send.assert_not_called()
        q.context = 99,'senna','select','Welcome'
        q.process_event(827,page(99,'Welcome',6,choice=0,prizes=((0,1,1),(0,2,1))),2)
        send.assert_not_called()
        q.context,q.deadline = (99,'senna','talk',None),10
        self.assertFalse(q.tick(11,p))
        self.assertEqual(q.timeouts,1)
        self.assertFalse(q.tick(12,p))
        send.assert_not_called()

    def test_unknown_mission_fields_fail_closed(self):
        data = page(99,'Welcome',needs=((9,1,1,0),))
        with self.assertRaises(ProtocolError): mission_page(data)
        with self.assertRaises(ProtocolError): mission_page(page(99,'Welcome')[:-1])
        with self.assertRaises(ValueError): commit_request(99,8)

    def test_new_npc_requests_only_use_real_visible_npc_ids_at_audited_location(self):
        w,send,q,p = self.make()
        w.own.x,w.own.y = NPCS['senna']
        x,y = NPCS['senna']
        w.entities[99] = Entity(11,99,1099,2,0,x,y,40)
        self.assertTrue(q.tick(10,p))
        send.assert_called_once_with(301,talk_request(99))
        self.assertTrue(q.tick(11,p))
        self.assertEqual(send.call_count,1)


class RoleTests(unittest.TestCase):
    def test_saved_targets_are_stable_and_existing_lances_get_legal_varied_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RoleStore(Path(tmp)/'roles.json')
            targets = [store.resolve(f'Bot{i:08x}',1,0)['target_job'] for i in range(3)]
            self.assertEqual(targets,[9,12,16])
            self.assertEqual(RoleStore(Path(tmp)/'roles.json').resolve('Bot00000001',1,0)['target_job'],12)
            with self.assertRaises(ProtocolError):store.resolve('Bot00000001',1,1)
            with self.assertRaises(ProtocolError):store.resolve('Bot00000001',4,0)
            self.assertEqual(store.resolve('Bot00000003',4,0)['first_job'],5)

    def test_existing_profession_is_preserved_and_never_rerolled(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RoleStore(Path(tmp)/'roles.json')
            self.assertEqual(store.resolve('Bot00000000',3,5)['first_job'],5)
            with self.assertRaises(ProtocolError):store.resolve('Bot00000001',2,5)

    def test_four_native_looks_and_invalid_body(self):
        for body,hair in enumerate((2000,2062,2124,2291),1):
            look = creation_look(body)
            self.assertEqual(len(look),1626)
            self.assertEqual(struct.unpack_from('<H',look,2)[0],body)
            self.assertEqual(struct.unpack_from('<H',look,0x658)[0],hair)
        with self.assertRaises(ValueError):creation_look(5)


class LootTests(unittest.TestCase):
    def test_only_quest_items_from_recent_attacks_with_server_xp_credit(self):
        w = scene()
        policy = Mock()
        policy.position.side_effect = lambda now: w.own.position
        policy.sequence = 3
        loot = QuestLoot(w)
        loot.note_attack(88,0)
        w.items[500] = (1620,1500,w.own.position,0,88,0)
        self.assertFalse(loot.tick(1,policy,{1620}))
        w.own.values[15] = 7
        self.assertTrue(loot.tick(2,policy,{1620}))
        self.assertEqual(loot.requests,1)
        policy.emit.assert_called_once_with(struct.pack('>IIBII',1,3,8,500,1500))
        self.assertFalse(loot.tick(3,policy,{1620}))
        w.items[501] = (1678,1501,w.own.position,0,88,0)
        self.assertFalse(loot.tick(4,policy,{1620}))
        w.items[502] = (1620,1502,w.own.position,1,88,0)
        w.items[503] = (1620,1503,w.own.position,0,999,0)
        self.assertFalse(loot.tick(5,policy,{1620}))

    def test_classic_item_creation_and_removal(self):
        w = scene()
        w.observe(506,struct.pack('>IIIIIHHBI',500,1500,1620,223200,278700,0,1,0,88))
        self.assertEqual(w.items[500][:5],(1620,1500,(223200,278700),0,88))
        w.observe(507,struct.pack('>I',500))
        self.assertFalse(w.items)


class RoutesTests(unittest.TestCase):
    def test_all_supported_argent_npcs_and_farm_goals_are_reachable(self):
        nav = Navigation(ROOT/'assets/argent-navigation.json')
        start = (223200,278700)
        for label,point in NPCS.items():
            goal = nav.nearest(point)
            self.assertIsNotNone(goal,label)
            self.assertLess(__import__('math').dist(goal,point),220,label)
            self.assertTrue(nav.path(start,goal),label)
        for model,(level,points) in FARMS.items():
            self.assertTrue(any(nav.path(start,nav.nearest(point)) for point in points),str(model))
