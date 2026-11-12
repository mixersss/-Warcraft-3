"""Real economy boundaries, bot-only parties, owned chests and class-specific progression."""
import json,random,struct,sys,unittest
from pathlib import Path
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from classic_wire import Reader,string,ProtocolError
from life import LifeItems,Chests
from equipment import ItemCatalog
from inventory import BagItem
from town import Town,trade_page,buy_request
from party import BotDirectory,Party
from career import Career
from story import Story
from skills import Skills
from progression import Progression,BUILDS
from test_development import scene
from test_adventure import role,offers,page
from regions import Regions

LIFE=LifeItems(ROOT/'assets');GEAR=ItemCatalog(ROOT/'assets/items.json')
def item(i,n=1):return BagItem(i,n,100,100,0,0,0,True)
def shop_packet(npc,identity):return struct.pack('>IBIBBBH',npc,1,0,1,2,1,identity)

class ChestTests(unittest.TestCase):
    def test_owned_chest_level_space_class_and_consumption(self):
        w=scene();w.bag_ready=True;w.bag_capacity=6;w.bag={0:item(436)}
        c=Chests(w,LIFE);p=Mock(sequence=1)
        self.assertFalse(c.tick(0,p,True))
        w.own.values[0]=5;w.bag_capacity=4
        self.assertFalse(c.tick(0,p,True))
        w.bag_capacity=6
        self.assertTrue(c.tick(0,p,True))
        self.assertEqual(p.emit.call_args.args[0][-4:],struct.pack('>hh',0,-1))
        c.tick(1,p,True);self.assertEqual(c.confirmed,0)
        w.bag.clear();c.tick(2,p,True);self.assertEqual(c.confirmed,1)
        w.bag={1:item(985)};w.own.values[0]=10
        self.assertFalse(c.tick(10,p,True)) # Requires real first profession.
    def test_unsupported_chest_is_not_opened_and_refusal_backs_off(self):
        w=scene();w.bag_ready=True;w.bag_capacity=10;w.own.values[0]=10;w.bag={0:item(9999)}
        c=Chests(w,LIFE);p=Mock(sequence=1)
        self.assertFalse(c.tick(0,p,True))
        w.bag={0:item(436)};self.assertTrue(c.tick(1,p,True))
        c.tick(14,p,True);self.assertFalse(c.tick(20,p,True));self.assertEqual(p.emit.call_count,1)

class ShopTests(unittest.TestCase):
    def make(self):
        w=scene();w.bag_ready=True;w.bag_capacity=20;w.own.values[8]=1000
        return w,Town(w,LIFE,GEAR,role(1),random.Random(1),w.own.position)
    def test_page_and_request_match_audited_classic_layout(self):
        self.assertEqual(trade_page(shop_packet(99,1847)),(99,[(1847,2,0)]))
        self.assertEqual(buy_request(99,2,0,10),struct.pack('>IHBBBBB',99,309,1,2,0,0,10))
        with self.assertRaises(ProtocolError):trade_page(shop_packet(99,1847)[:-1])
    def test_food_purchase_requires_real_offer_and_two_confirmations(self):
        w,t=self.make();send=Mock();t.context=(99,'shop',8);t.wanted=(1847,10)
        t.observe(805,shop_packet(99,1847),0,send)
        send.assert_called_once_with(308,buy_request(99,2,0,10))
        self.assertEqual(w.own.values[8],1000);self.assertFalse(w.bag)
        w.bag[0]=item(1847,10);t.tick(1,Mock(),True);self.assertEqual(t.confirmed,0)
        w.own.values[8]=900;t.tick(2,Mock(),True);self.assertEqual(t.confirmed,1)
    def test_no_money_no_offer_or_timeout_does_not_spend_or_retry(self):
        w,t=self.make();w.own.values[8]=0;self.assertIsNone(t.choose_want())
        send=Mock();t.wanted=(1847,10);t.context=(99,'shop',8)
        t.observe(805,shop_packet(99,1847),0,send);send.assert_not_called()
        w.own.values[8]=1000;t.wanted=(1847,10);t.context=(99,'shop',8)
        t.observe(805,shop_packet(99,1),0,send);send.assert_not_called()
    def test_shop_menu_uses_server_trade_function_not_unrelated_action(self):
        w,t=self.make();send=Mock();t.context=(99,'talk',8)
        payload=struct.pack('>IB',99,1)+string('Hi')+b'\x02'+string('Combine')+string('Trade')+b'\0'
        t.observe(802,payload,0,send)
        self.assertEqual(send.call_args.args,(301,struct.pack('>IHBB',99,303,1,1)))
    def test_city_rest_has_arrival_and_finite_duration(self):
        w,t=self.make();p=Mock();p.position.return_value=w.own.position
        t.next_break=0;t.note_progress(0,0);t.note_progress(12,0)
        self.assertTrue(t.tick(1,p,True));self.assertTrue(t.tick(2,p,True))
        self.assertEqual(t.breaks,1);t.next_shop=999
        self.assertFalse(t.tick(200,p,True));self.assertGreater(t.next_break,200)

class PartyTests(unittest.TestCase):
    def make(self):
        w=scene();d=BotDirectory();send=Mock();p=Party(w,send,'Bot00000002',2,d)
        d.update('Bot00000001',1,'garner',w.own.position,1,0)
        d.update('Bot00000002',2,'garner',w.own.position,1,0)
        return w,d,send,p
    def test_only_registered_nearby_bot_leader_is_accepted(self):
        w,d,send,p=self.make()
        p.observe(5001,string('Human')+struct.pack('>IH',88,0),1)
        send.assert_called_once_with(6003,struct.pack('>I',88));send.reset_mock()
        p.observe(5001,string('Bot00000001')+struct.pack('>IH',99,0),1)
        send.assert_called_once_with(6002,struct.pack('>I',99));self.assertEqual(p.members,())
    def test_membership_requires_server_refresh_not_accept_request(self):
        w,d,send,p=self.make()
        payload=b'\x01\x02'+b''.join(struct.pack('>I',i)+string(n)+string('')+struct.pack('>H',0)
                          for i,n in ((1,'Bot00000001'),(2,'Bot00000002')))
        p.observe(5002,payload,1);self.assertEqual(len(p.members),2)
        self.assertEqual(d.peers('Bot00000001',1)['Bot00000002']['team'],p.members)
        p.observe(5002,b'\x00\x00',2)
        self.assertEqual(p.members,())
        self.assertFalse(d.peers('Bot00000001',2)['Bot00000002']['team'])
    def test_some_bots_invite_with_native_names_and_throttle(self):
        w,d,send,p=self.make();p=Party(w,send,'Bot00000001',1,d)
        p.tick(1,1);send.assert_called_once_with(6001,string('Bot00000002'))
        p.tick(2,1);self.assertEqual(send.call_count,1)
        p.tick(65,1);self.assertEqual(send.call_count,1) # Candidate registry expired.

class LearningTests(unittest.TestCase):
    def test_catalog_books_obey_class_and_prerequisites(self):
        w=scene();w.own.values.update({0:10,4:1,7:5})
        self.assertTrue(LIFE.can_learn(w,LIFE.books[3164]))
        self.assertFalse(LIFE.can_learn(w,LIFE.books[3206]))
        prerequisite=next(b for b in LIFE.books.values() if b['prerequisites'] and '1' in b['jobs'])
        self.assertFalse(LIFE.can_learn(w,prerequisite))
    def test_learning_owned_book_waits_for_points_and_skill_update(self):
        w=scene();w.own.values.update({0:10,4:1,7:5});w.bag_ready=True;w.bag={0:item(3164)}
        s=Skills(w,role(1),LIFE);p=Mock(sequence=1)
        self.assertTrue(s.tick(0,p,True));w.skills[66]={'level':1}
        s.tick(1,p,True);self.assertEqual(s.confirmed,0)
        w.own.values[7]=4;s.tick(2,p,True);self.assertEqual(s.confirmed,1)
    def test_different_classes_choose_their_configured_earned_builds(self):
        choices={}
        for job in BUILDS:
            w=scene();w.own.model={8:2,9:1,12:3,13:4,14:4,16:1}[job]
            first={8:1,9:1,12:2,13:5,14:5,16:4}[job]
            w.own.values.update({4:first,25:10,26:10,27:10,28:10,29:10})
            send=Mock();p=Progression(w,send,first);p.target_job=job;p.tick(0,True)
            attr=struct.unpack('>H',send.call_args.args[1][1:3])[0];choices[job]=attr
        self.assertEqual(choices[12],26);self.assertEqual(choices[13],29);self.assertEqual(choices[16],28)
        self.assertGreater(len(set(choices.values())),2)

class QuestCareerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.regions=Regions(ROOT/'assets')
    def test_level40_only_own_advanced_class_is_selected_and_accepted(self):
        for first,target in ((1,8),(1,9),(2,12),(5,13),(5,14),(4,16)):
            w=scene();w.own.values.update({0:40,4:first});r=role(first);r['target_job']=target
            send=Mock();q=Career(w,send,r,LIFE,self.regions);q.context=(99,'talk',8)
            wrong=next(v['title'] for k,v in LIFE.services['quests'].items() if int(k)!=target)
            q.observe(802,offers(99,[(wrong,1),(q.quest['title'],1)]),0)
            self.assertEqual(send.call_args.args[1][-1],1)
            send.reset_mock();q.observe(827,page(99,q.quest['title']),1)
            self.assertEqual(send.call_args.args[0],301)
            self.assertFalse(q.summary()['profession_confirmed'])
    def test_advanced_class_requires_real_level_job_and_quest_journal(self):
        w=scene();send=Mock();q=Career(w,send,role(1),LIFE,self.regions)
        self.assertFalse(q.tick(0,Mock(),True));send.assert_not_called()
        w.own.values.update({0:40,4:1});q.observe(832,struct.pack('>HB',737,0),0)
        self.assertTrue(q.active());self.assertIn(4474,q.needed_items())
        q.tick(1,Mock(),True);self.assertEqual(w.own.values[4],1)
    def test_story_referral_goes_to_real_receiver_without_faking_life_points(self):
        w=scene();w.own.values.update({0:10,4:1,12:1,13:0});q=Story(w,Mock(),role(1),LIFE,self.regions)
        q.observe(832,struct.pack('>HB',200,0),0)
        self.assertEqual(q.quest['position'],[221925,274925]);self.assertEqual(q.quest['title'],'Secretary Message')
        self.assertEqual(w.own.values[13],0)
        q.pending=7;q.observe(831,struct.pack('>H',200),1)
        self.assertEqual(q.quest['journal'],203);self.assertEqual(q.delivered,1)
    def test_story_food_objectives_have_real_drop_species(self):
        w=scene();w.own.values.update({0:15,4:1});q=Story(w,Mock(),role(1),LIFE,self.regions)
        q.observe(832,struct.pack('>HB',204,0),0)
        self.assertEqual(q.needed_items(),{3963,3964,3116})
        self.assertTrue(q.desired_models())

if __name__=='__main__':unittest.main()
