"""Native inventory fixtures, movement continuity, legal progression and fleet isolation."""
import json
import struct
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock,patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from classic_wire import Reader,ProtocolError
from world import World
from inventory import kitbag,BagItem
from equipment import ItemCatalog,Equipment
from skills import Skills
from navigation import Navigation
from hunter import Hunter
from headless import Report
from regions import Regions,birthplace_for
from roles import RoleStore
from adventure import Adventure
from fleet import Fleet
from social import Social,ChatBudget,PHRASES
from test_hunt import FIXTURES,enter_packet,world_fixture
from test_development import scene
from test_adventure import role,offers

CATALOG=ItemCatalog(ROOT/'assets/items.json')

def item(identity):return BagItem(identity,1,100,100,0,0,0,True)


class InventoryTests(unittest.TestCase):
    def test_real_native_writer_boat_instance_and_delta_boundaries(self):
        reader=Reader(bytes.fromhex(FIXTURES['bag_init']))
        sync,capacity,items=kitbag(reader,CATALOG.types)
        reader.end()
        self.assertEqual((sync,capacity),(0,6))
        self.assertEqual({i:v.identity if v else None for i,v in items.items()},{0:289,1:1847,2:None,3:3988})
        world=World(CATALOG.types)
        world.enter(enter_packet()+bytes.fromhex(FIXTURES['bag_init']))
        self.assertTrue(world.bag_ready)
        self.assertFalse(world.bag_disabled)
        world.read_bag(Reader(bytes.fromhex(FIXTURES['bag_delta'])))
        self.assertNotIn(0,world.bag)
        self.assertEqual(world.bag[5].identity,1)
        self.assertEqual(world.bag[3].identity,3988)

    def test_unknown_item_or_truncated_native_packet_pauses_inventory(self):
        for types,packet in (({},FIXTURES['bag_init']),(CATALOG.types,FIXTURES['bag_init'][:-4])):
            world=World(types)
            world.read_bag(Reader(bytes.fromhex(packet)))
            self.assertTrue(world.bag_disabled)

    def test_equipping_requires_owned_compatible_gear_and_appearance_confirmation(self):
        world=scene();send=Mock();policy=Mock(sequence=8)
        equipment=Equipment(world,CATALOG,send)
        self.assertFalse(equipment.tick(0,policy))
        world.bag_ready=True;world.bag={4:item(289)}
        self.assertTrue(equipment.tick(0,policy))
        self.assertEqual(policy.emit.call_args.args[0],struct.pack('>IIBhh',1,8,11,4,-1))
        equipment.tick(1,policy)
        self.assertEqual(equipment.confirmed,0)
        self.assertEqual(world.bag[4].identity,289) # No fabricated inventory change.
        world.own.equipment[2]=289
        equipment.tick(2,policy)
        self.assertEqual(equipment.confirmed,1)
        self.assertFalse(equipment.tick(4,policy))
        self.assertEqual(policy.emit.call_count,1)

    def test_unusable_gear_and_refusal_do_not_repeat_requests(self):
        world=scene();world.bag_ready=True;world.bag={0:item(1),1:item(1847)}
        equipment=Equipment(world,CATALOG,Mock());policy=Mock(sequence=1)
        self.assertFalse(equipment.tick(0,policy)) # Lv10 professional sword, apple.
        world.bag[2]=item(465)
        self.assertTrue(equipment.tick(1,policy))
        equipment.tick(14,policy)
        self.assertFalse(equipment.tick(20,policy))
        self.assertEqual(equipment.failed,1)
        self.assertEqual(policy.emit.call_count,1)

    def test_respawn_discards_old_map_route_and_inventory(self):
        world=World(CATALOG.types)
        world.enter(enter_packet()+bytes.fromhex(FIXTURES['bag_init']))
        world.motion[world.own_id]=([(1,2),(3,4)],0,480)
        world.enter(enter_packet())
        self.assertFalse(world.motion)
        self.assertFalse(world.bag_ready)
        self.assertFalse(world.bag)
        self.assertEqual(world.position(),world.own.position)


class MovementTests(unittest.TestCase):
    def make(self):
        world=world_fixture();send=Mock();nav=Navigation(ROOT/'assets/argent-navigation.json')
        return world,send,Hunter(world,nav,send,Report(),Mock(),'test')

    def test_prediction_uses_only_acknowledged_route_and_stops_at_endpoint(self):
        world,send,policy=self.make()
        initial=world.own.position
        goal=policy.nav.waypoints[0]
        self.assertTrue(policy.move_to(goal,100))
        self.assertEqual(world.position(102),initial)
        packet=struct.pack('>IIBH',world.own_id,1,1,0)+struct.pack('>H',16)+struct.pack('<iiii',*initial,initial[0]+1000,initial[1])
        with patch('world.time.monotonic',return_value=100):world.observe(508,packet)
        self.assertEqual(world.position(101),(initial[0]+480,initial[1]))
        self.assertEqual(world.position(200),(initial[0]+1000,initial[1]))
        self.assertEqual(world.own.position,initial)

    def test_long_route_waits_for_previous_segment_to_finish(self):
        world,send,policy=self.make()
        goal=policy.nav.waypoints[-1]
        policy.move_to(goal,100)
        reader=Reader(send.call_args.args[1]);reader.take(9);points=reader.sequence()
        self.assertEqual(len(points)//8,32)
        world.move_revision+=1;world.move_state=0
        route=list(struct.iter_unpack('<ii',points))
        world.motion[world.own_id]=(route,100,480)
        policy.move_to(goal,policy.move_until-1)
        self.assertEqual(send.call_count,1)
        policy.move_to(goal,policy.move_until-.5)
        self.assertEqual(send.call_count,1)
        # Do not cancel the last half-second of every acknowledged segment.
        policy.move_to(goal,policy.move_until+.6)
        self.assertEqual(send.call_count,2)
        send.assert_called_with(7,b'')
        policy.flush_action(policy.clock+1.1)
        self.assertEqual(send.call_count,3)
        reader=Reader(send.call_args.args[1]);reader.take(9)
        second=list(struct.iter_unpack('<ii',reader.sequence()))
        self.assertLess(__import__('math').dist(second[0],route[-1]),480)

    def test_city_revive_uses_native_command_and_bounded_retries(self):
        world,send,policy=self.make()
        world.own.values[1]=0
        for stamp in (100,107,108,109,138,168,200):policy.tick(stamp)
        self.assertEqual(send.call_count,3)
        policy.tick(300);self.assertEqual(send.call_count,4)
        policy.tick(301);self.assertEqual(send.call_count,4)
        self.assertTrue(all(call.args==(10,b'\x01') for call in send.call_args_list))

    def test_cache_never_returns_shared_mutable_paths(self):
        world,send,policy=self.make();start=world.own.position;end=policy.nav.waypoints[0]
        first=policy.nav.path(start,end);original=list(first)
        first.clear()
        self.assertEqual(policy.nav.path(start,end),original)
        self.assertLessEqual(policy.nav._path.cache_info().currsize,256)


class RegionalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.regions=Regions(ROOT/'assets')

    def test_all_nine_spawns_reach_beginner_farms(self):
        for name,region in self.regions.data.items():
            nav=self.regions.nav(name)
            for raw in region['spawns']:
                start=nav.nearest(raw,12)
                self.assertIsNotNone(start,(name,raw))
                self.assertTrue(nav.path(start,nav.waypoints[0]),(name,raw))

    def test_local_profession_trainers_and_assistants_are_reachable(self):
        for name,firsts in (('garner',(1,4)),('magicsea',(5,)),('darkblue',(2,))):
            nav=self.regions.nav(name);region=self.regions.get(name)
            for first in firsts:
                world=scene();world.map=name
                quest=Adventure(world,Mock(),role=role(first),region=region)
                self.assertTrue(quest.profession_local)
                for key in ('senna','goldie','nila','ditto',quest.trainer,quest.assistant):
                    target=nav.nearest(quest.npcs[key],6)
                    self.assertIsNotNone(target,(name,key))
                    self.assertTrue(nav.path(nav.nearest(region['spawns'][0],12),target),(name,key))

    def test_thirty_new_roles_cover_three_cities_with_compatible_jobs(self):
        from collections import Counter
        with tempfile.TemporaryDirectory() as tmp:
            store=RoleStore(Path(tmp)/'roles.json')
            roles=[store.resolve(f'Bot{i:08x}',i%4+1,0) for i in range(30)]
            cities=Counter(birthplace_for(r['first_job']) for r in roles)
            self.assertEqual(len(cities),3)
            self.assertEqual(set(r['target_job'] for r in roles),{8,9,12,13,14,16})
            self.assertLessEqual(max(Counter(r['body'] for r in roles).values())-min(Counter(r['body'] for r in roles).values()),1)

    def test_quest_drop_species_follow_real_regional_item_drops(self):
        for name,first,mission,dropper in (('magicsea',5,710,96),('darkblue',2,716,216)):
            world=scene();world.map=name;world.own.values[0]=1
            quest=Adventure(world,Mock(),role=role(first),region=self.regions.get(name))
            quest.journal_ready=True;quest.journal={mission:0}
            self.assertIn(dropper,quest.desired_models())

    def test_other_class_offers_are_rejected_in_every_city(self):
        for name,first in (('garner',1),('magicsea',5),('darkblue',2)):
            world=scene();world.map=name;world.own.values[0]=10
            send=Mock();quest=Adventure(world,send,role=role(first),region=self.regions.get(name))
            quest.context=99,'senna','talk',None
            wrong=[role(i)['promotion'] for i in (1,2,4,5) if i!=first]
            quest.process_event(802,offers(99,[(t,1) for t in wrong]),0)
            send.assert_not_called()


class RecoveryTests(unittest.TestCase):
    def test_apple_consumption_and_health_must_both_be_confirmed(self):
        from recovery import Recovery
        world=scene();world.own.values[1]=40
        world.bag_ready=True;world.bag={2:item(1847)}
        policy=Mock(sequence=1);recovery=Recovery(world)
        self.assertTrue(recovery.tick(0,policy))
        self.assertEqual(policy.emit.call_args.args[0],struct.pack('>IIBhh',1,1,11,2,-1))
        world.own.values[1]=60
        recovery.tick(1,policy);self.assertEqual(recovery.confirmed,0)
        world.bag.clear()
        recovery.tick(2,policy);self.assertEqual(recovery.confirmed,1)
        self.assertFalse(recovery.tick(20,policy))

    def test_no_food_creation_dead_use_or_refusal_spam(self):
        from recovery import Recovery
        world=scene();world.own.values[1]=0;world.bag_ready=True;world.bag={0:item(1847)}
        policy=Mock(sequence=1);recovery=Recovery(world)
        self.assertFalse(recovery.tick(0,policy))
        world.own.values[1]=30
        self.assertTrue(recovery.tick(1,policy))
        recovery.tick(14,policy)
        self.assertFalse(recovery.tick(20,policy))
        self.assertEqual(policy.emit.call_count,1)
        self.assertEqual(recovery.timeouts,1)


class SkillsAndFleetTests(unittest.TestCase):
    def test_class_book_and_upgrade_require_skill_and_point_confirmation(self):
        world=scene();world.own.values.update({0:10,4:1,7:4})
        world.bag_ready=True;world.bag={2:item(3164),3:item(3206)}
        skills=Skills(world,role(1));policy=Mock(sequence=4)
        self.assertTrue(skills.tick(0,policy,True))
        self.assertEqual(policy.emit.call_args.args[0][-4:],struct.pack('>hh',2,-1))
        world.skills[66]={'level':1}
        skills.tick(1,policy,True);self.assertEqual(skills.confirmed,0)
        world.own.values[7]=3
        skills.tick(2,policy,True);self.assertEqual(skills.confirmed,1)
        self.assertTrue(skills.tick(6,policy,True))
        policy.send.assert_called_once_with(11,struct.pack('>HB',66,1))
        world.own.values[7]=2;world.skills[66]['level']=2
        skills.tick(7,policy,True)
        self.assertEqual(skills.confirmed,2)
        self.assertFalse(skills.tick(20,policy,True))

    def test_native_skills_are_decoded_not_invented(self):
        world=world_fixture()
        self.assertEqual(len(world.skills),2)
        self.assertTrue(all(0<skill['level']<100 for skill in world.skills.values()))

    def test_fleet_status_tracks_actual_connections_not_requested_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            fleet=Fleet(30,Path(tmp)/'population-status.json')
            fleet.update(1,connected=True,map='garner',body=1,target_job=9)
            fleet.update(2,connected=True,map='magicsea',body=3,target_job=13)
            fleet.update(1,connected=False)
            status=fleet.write()
            self.assertEqual((status['connected'],status['peak_connected'],status['requested']),(1,2,30))
            self.assertEqual(status['cities'],{'magicsea':1})
            with self.assertRaises(ValueError):fleet.update(1,password='secret')

    def test_regional_chat_and_expired_events_and_large_bank(self):
        self.assertGreaterEqual(sum(map(len,PHRASES.values())),100)
        world=scene();world.map='magicsea';send=Mock()
        social=Social(world,send,world.own.name,ChatBudget(),'test')
        social.hear(2,world.own.name+' где город',0)
        social.tick(6,False,True)
        self.assertIn('Шайтана',Reader(send.call_args.args[1]).string())
        for i in range(30):social.event('level',i*121)
        self.assertLessEqual(len(social.events),4)
        social.tick(10000,False,False)
        self.assertFalse(social.events)


if __name__=='__main__':unittest.main()
