"""Regression coverage for wrong-city Senna waits and class-balanced travel."""
import collections
import json
import random
import struct
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from adventure import Adventure, NPCS
from city_travel import CityTravel, TELEPORTERS
from classic_wire import Reader, string
from headless import Report
from hunter import Hunter, hunt
from regions import Regions
from roles import RoleStore, ALLOWED
from show_diagnostics import collect, render_report
from town import function_request
from world import Entity, attrs
from test_adventure import role, offers, page
from test_hunt import FIXTURES
import test_alpha26 as base


def menu(npc, labels, number=3):
    return struct.pack('>IB',npc,number)+string('Teleport')+bytes([len(labels)])+b''.join(string(s) for s in labels)+b'\x00'


def enter_city(map_name, position):
    raw=bytes.fromhex(FIXTURES['own_base'])
    raw=raw.replace(struct.pack('>II',223200,278700),struct.pack('>II',*position))
    values=attrs(Reader(bytes.fromhex(FIXTURES['own_attrs'])))
    values.update({0:9,4:0})
    attributes=struct.pack('>BH',3,len(values))+b''.join(struct.pack('>BI',key,value&0xffffffff) for key,value in values.items())
    return bytes(6)+string(map_name)+b'\x00'+raw+bytes.fromhex(FIXTURES['own_skills'])+bytes.fromhex(FIXTURES['own_states'])+attributes


class RemoteProfessionTests(unittest.TestCase):
    def test_senna_pending_dialogue_and_cooldown_cannot_restart_in_wrong_city(self):
        for first in (2,5):
            world,policy,quest=base.ProfessionSchedulingTests().policy(first)
            quest.priority_started=True
            quest.context=(88,'senna','commit',quest.role['promotion'])
            quest.pending=(6,None,200)
            quest.deadline=200
            quest.next_visit=300
            policy.travel=CityTravel(world,policy.send,1,role(first))
            policy.move_to=Mock(return_value=True)
            policy.tick(100)
            self.assertIsNone(quest.context)
            self.assertIsNone(quest.pending)
            self.assertTrue(policy.move_to.called)
            self.assertLess(__import__('math').dist(policy.move_to.call_args.args[0],TELEPORTERS['garner']),220)
            self.assertEqual(policy.travel.target,'darkblue' if first==2 else 'magicsea')
            self.assertEqual(quest.requests,0)

    def test_hunt_router_transfers_to_both_cities_and_accepts_local_promotion(self):
        for first,destination,label,mission in ((2,'darkblue','Icicle City',59),(5,'magicsea','Shaitan City',60)):
            with self.subTest(first=first):
                clock=[100.0]
                captured=[]
                stop=threading.Event()
                client=Mock()
                client.enter_payload=enter_city('garner',TELEPORTERS['garner'])
                client.pending_world=collections.deque()
                client.wire.last_send=100.0
                report=Report()
                navigation=Regions(ROOT/'assets')
                chosen=role(first)
                store=Mock()
                store.resolve.return_value=chosen
                store.rebalance_novice.return_value=chosen
                def factory(*args,**kwargs):
                    policy=Hunter(*args,**kwargs)
                    captured.append(policy)
                    return policy
                step=[0]
                def receive(deadline):
                    clock[0]+=1
                    step[0]+=1
                    policy=captured[0]
                    if step[0]==1:
                        clock[0]+=3
                        w=policy.world
                        w.entities[77]=Entity(11,77,177,2,0,*TELEPORTERS['garner'],40)
                        return 828,b'\x00'
                    if step[0]==2:return 802,menu(77,['Other destination','Go to '+label+'!'],18)
                    if step[0]==3:return 802,menu(77,['Cancel','Teleport'],7)
                    if step[0]==4:
                        target=Adventure(policy.world,Mock(),role=chosen)
                        # Coordinates are audited regional guide positions.
                        point=(131577,50700) if first==2 else (87614,357250)
                        return 516,enter_city(destination,point)
                    if step[0]==5:
                        q=policy.adventure
                        policy.world.entities[88]=Entity(11,88,188,2,0,*q.npcs['senna'],40)
                        return 828,b'\x00'
                    if step[0]==6:return 802,offers(88,[(chosen['promotion'],1)])
                    if step[0]==7:return 827,page(88,chosen['promotion'])
                    if step[0]==8:return 832,struct.pack('>HB',mission,0)
                    stop.set()
                    raise TimeoutError()
                client.wire.receive.side_effect=receive
                client.service.side_effect=lambda command,payload:client.world_handler(command,payload)
                with patch('hunter.Hunter',side_effect=factory),patch('hunter.time.monotonic',side_effect=lambda:clock[0]),patch.object(Report,'write'):
                    hunt(client,60,stop,report,navigation,tell=lambda text:None,
                         bot_name='Bot00000001',adventure_mode=True,role_store=store,tactic='farm')
                policy=captured[0]
                self.assertEqual(policy.world.map,destination)
                self.assertEqual(policy.travel.arrivals,1)
                self.assertTrue(policy.adventure.profession_local)
                self.assertEqual(policy.adventure.active(),mission)
                self.assertEqual(policy.adventure.accepted,1)
                self.assertEqual(policy.world.own.values[4],0)
                client.wire.send.assert_any_call(301,function_request(77,18,1))
                client.wire.send.assert_any_call(301,function_request(77,7,1))

    def test_missing_menu_reports_actual_labels_and_bounded_retry(self):
        world,policy,quest=base.ProfessionSchedulingTests().policy(2)
        travel=CityTravel(world,policy.send,1,role(2))
        travel.target='darkblue';travel.context=(77,'menu',110)
        travel.observe(802,menu(77,['Unavailable']),100)
        self.assertEqual(travel.last_menu,['Unavailable'])
        self.assertIn('Icicle City',travel.last_problem)
        self.assertEqual(travel.next_trip,130)
        self.assertEqual(travel.arrivals,0)

    def test_senna_missing_offer_is_visible_in_diagnostics(self):
        world,policy,quest=base.ProfessionSchedulingTests().policy()
        quest.context=(88,'senna','talk',None)
        quest.process_event(802,offers(88,[('Unknown title',0)]),100)
        text=render_report({'adventure':quest.summary()})
        self.assertIn('Unknown title',text)
        self.assertIn('Swordsman Promotion',text)
        self.assertIn('не предложил',text)


class BalancedClassTests(unittest.TestCase):
    def test_two_hundred_bodies_reach_feasible_fifty_thirty_split(self):
        with tempfile.TemporaryDirectory() as d:
            store=RoleStore(Path(d)/'roles.json',rng=random.Random(27))
            for i in range(200):store.resolve(str(i),i%4+1,0)
            assigned=[store.rebalance_novice(str(i),i%4+1,0,{}) for i in range(200)]
            counts=collections.Counter(r['target_job'] for r in assigned)
            self.assertEqual(counts,{8:50,9:30,12:30,13:30,14:30,16:30})
            self.assertTrue(all(r['target_job'] in ALLOWED[r['body']] for r in assigned))

    def test_real_professions_and_started_quests_never_change(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'roles.json'
            path.write_text(json.dumps({'current':{'body':1,'target_job':9},'other':{'body':1,'target_job':9}}))
            store=RoleStore(path,rng=random.Random(1))
            before=path.read_bytes()
            for actual,journal in ((1,{}),(9,{}),(0,{58:0}),(0,{62:0})):
                self.assertEqual(store.rebalance_novice('current',1,actual,journal)['target_job'],9)
            self.assertEqual(path.read_bytes(),before)
            self.assertIn(store.rebalance_novice('current',1,0,{})['target_job'],(12,16))

    def test_diagnostics_never_read_private_data_or_echo_arbitrary_report_fields(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'data').mkdir()
            (root/'data/bot-local.json').write_text('PRIVATE_STATE')
            (root/'bot-report-01.json').write_text(json.dumps({'password':'SECRET_VALUE','account':'SECRET_ACCOUNT','bot_index':1,'adventure':{'state':'ожидает ответ'}}))
            text=collect(root)
            self.assertIn('ожидает ответ',text)
            for secret in ('PRIVATE_STATE','SECRET_VALUE','SECRET_ACCOUNT'):self.assertNotIn(secret,text)

    def test_server_resource_audit_is_read_only_and_reports_known_mission_titles(self):
        from audit_server import audit
        with tempfile.TemporaryDirectory() as d:
            resource=Path(d)/'resource'
            scripts=resource/'script/MisScript'
            scripts.mkdir(parents=True)
            mission=scripts/'MissionScript01.lua'
            original=b'DefineMission(63,"Hunter Promotion",59)\n'
            mission.write_bytes(original)
            (scripts/'NpcScript01.lua').write_text('GiveItem(player,436,1)')
            report=audit(d)
            self.assertIn('Hunter Promotion: название найдено',report)
            self.assertIn('Объявлений DefineMission в MissionScript01.lua: 1',report)
            self.assertIn('ссылка выдачи',report)
            self.assertEqual(mission.read_bytes(),original)
            self.assertEqual(len(list(resource.rglob('*'))),4)


if __name__=='__main__':unittest.main()
