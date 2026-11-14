"""Fair quest turns, dry city trading, earned history and bounded actual price learning."""
import dataclasses,json,math,random,struct,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from study_queue import StudyQueue
from market_prices import MarketPrices
from market import MarketDirectory
from life import LifeItems
from story import Story,STEPS
from test_adventure import role
from test_development import scene
from trade_dialogue import variants,render
import test_market as prior

class QueueTests(unittest.TestCase):
    def test_waiters_keep_their_turn_and_all_three_hundred_get_admitted(self):
        q=StudyQueue(limit=20,seconds=60,rest_seconds=900);seen=set()
        for now in range(0,901,60):
            admitted={str(i) for i in range(300) if q.turn(str(i),now)}
            self.assertLessEqual(len(q.active),20);seen.update(admitted)
        self.assertEqual(len(seen),300)

    def test_holder_expiry_does_not_renew_on_polling(self):
        q=StudyQueue(limit=1,seconds=60)
        self.assertTrue(q.turn('a',0));self.assertTrue(q.turn('a',30))
        self.assertFalse(q.turn('b',31));self.assertFalse(q.turn('a',60));self.assertTrue(q.turn('b',60))

    def test_stale_waiter_is_not_admitted_while_disconnected(self):
        q=StudyQueue(limit=1,seconds=600)
        q.turn('a',0);q.turn('gone',1)
        self.assertTrue(q.turn('b',601));self.assertNotIn('gone',q.active)

class HistoryTests(unittest.TestCase):
    def make(self):
        w=scene();w.own.values.update({0:15,4:1,12:1,13:0})
        q=Story(w,Mock(),role(1),LifeItems(ROOT/'assets'),SimpleNamespace(study_queue=StudyQueue()))
        return w,q

    def test_only_native_delivered_commit_is_saved(self):
        w,q=self.make()
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'history.json';q.load(path)
            q.observe(832,struct.pack('>HB',200,0),0)
            self.assertFalse(path.exists());q.pending=7
            q.observe(831,struct.pack('>H',200),1)
            data=json.loads(path.read_text());self.assertEqual(data['confirmed_completed'],[200])
            _,other=self.make();other.load(path)
            self.assertEqual(other.quest['journal'],203);self.assertEqual(w.own.values[13],0)

    def test_cancellation_without_commit_is_not_a_completed_history(self):
        w,q=self.make();q.observe(832,struct.pack('>HB',200,0),0)
        q.observe(831,struct.pack('>H',200),1)
        self.assertEqual(q.completed,set());self.assertEqual(q.delivered,0)

    def test_another_city_can_request_a_real_study_trip(self):
        from city_travel import CityTravel
        w,q=self.make();w.map='magicsea'
        self.assertTrue(q.study_turn(100))
        p=SimpleNamespace(career=None,town=None,story=q,wants_story=lambda:q.study_turn(100))
        self.assertEqual(CityTravel(w,Mock(),7,role(1)).destination(p),'garner')

    def test_antidote_branch_visits_letter_receiver_then_collects_actual_subquest(self):
        from inventory import BagItem
        w,q=self.make();q.journal={207:0};q.ready=True
        w.bag={0:BagItem(3966,1,0,0,0,0,0,True)};q.select_step()
        self.assertTrue(q.quest['intermediate']);self.assertEqual(q.quest['position'],[225075,277025])
        q.intermediate_wait=(3966,1,100);q.pending=7;q.context=(77,'commit',100)
        w.bag={};p=SimpleNamespace(position=lambda now:w.own.position,nav=Mock(),move_to=Mock())
        q.tick(20,p,False)
        self.assertEqual(q.quest['journal'],208);self.assertEqual(q.completed,set())
        q.observe(832,struct.pack('>HB',208,0),21)
        self.assertEqual(q.needed_items(),{1678,3968,1614})
        w.bag={0:BagItem(3967,1,0,0,0,0,0,True)};q.journal={207:1};q.completed.add(208);q.select_step()
        self.assertEqual(q.quest['journal'],207);self.assertEqual(q.quest['position'],[227789,283199])

    def test_cross_city_referral_uses_actual_receiver_map(self):
        w,q=self.make();q.observe(832,struct.pack('>HB',220,0),10)
        self.assertEqual(q.quest['map'],'magicsea');self.assertEqual(q.quest['receiver'],[89804,364010])

class PitchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from navigation import Navigation
        cls.nav=Navigation(ROOT/'assets/garner-navigation.json');cls.life=LifeItems(ROOT/'assets')
        cls.region=json.loads((ROOT/'assets/regions.json').read_text())['garner']

    def test_at_least_eighty_dry_safe_spaced_pitches_around_several_city_anchors(self):
        from stall_pitches import city_pitches
        pitches=city_pitches('garner',self.region['spawns'][0],self.nav,self.life.npcs,self.region['spawns'])
        self.assertGreaterEqual(len(pitches),80)
        for i,p in enumerate(pitches):
            self.assertTrue(self.nav.free(self.nav.cell(p)));self.assertFalse(self.nav.combat_allowed(p))
            self.assertTrue(all(math.dist(p,other)>=450 for other in pitches[i+1:]))
        bank=next(n for n in self.life.npcs.by_service['bank'] if n['name']=='Banker - Monica')
        self.assertTrue(any(math.dist(p,bank['position'])<1500 for p in pitches[:80]))
        self.assertTrue(any(math.dist(p,(219220,276700))<1500 for p in pitches[:80]))

    def test_shared_city_pitches_do_not_depend_on_individual_home(self):
        d=MarketDirectory(argent_target=80)
        a=d.pitches('garner',(223200,278700),self.nav,self.life.npcs,self.region['spawns'])
        b=d.pitches('garner',(219400,277900),self.nav,self.life.npcs,self.region['spawns'])
        self.assertIs(a,b)

    def test_real_runtime_limit_permits_eighty_argent_leases(self):
        d=MarketDirectory(live_count=lambda now:300,argent_target=80)
        self.assertEqual([d.reserve(str(i),'garner',0) for i in range(80)],list(range(80)))
        self.assertIsNone(d.reserve('81','garner',0))

class PriceTests(unittest.TestCase):
    def test_only_explicit_confirmation_updates_bounded_persistent_guide(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'prices.json';p=MarketPrices(path)
            self.assertEqual(p.guide(684,5000),5000);self.assertFalse(path.exists())
            p.confirmed(684,10000,5000);p.save(force=True)
            self.assertEqual(p.guide(684,5000),6000)
            self.assertEqual(MarketPrices(path).guide(684,5000),6000)
            for i in range(20):p.confirmed(684,2000000000,5000)
            self.assertLessEqual(p.guide(684,5000),10000)

    def test_wrong_gold_delta_never_counts_as_stall_purchase(self):
        w,s,m,p=prior.MarketTests().make();w.entities[2].stall='Shop';m.context=(2,10)
        m.observe(854,prior.MarketTests().packet(),2)
        w.bag={0:prior.MarketTests().item(885,1)};w.own.values[8]-=1
        m.tick(4,p,True);self.assertEqual(m.confirmed_buys,0)

    def test_protected_scrolls_blueprints_and_runes_are_tradeable_not_junk(self):
        from vendor import Vendor
        w,s,m,p=prior.MarketTests().make()
        junk=json.loads((ROOT/'assets/junk-items.json').read_text())['items']
        for identity in (684,1092,1000,1001,1002,1003,2300,2301,2302,3425,3457):
            self.assertIn(identity,m.catalog.items);self.assertNotIn(str(identity),junk)

class DialogueTests(unittest.TestCase):
    def test_trade_conversation_selects_one_bot_and_keeps_its_followups(self):
        from conversations import Conversations
        c=Conversations(ROOT/'assets')
        self.assertEqual(sum(c.claim_trade('garner',77,str(i),100) for i in range(80)),1)
        self.assertTrue(c.claim_trade('garner',77,'0',104))
        self.assertFalse(c.claim_trade('garner',77,'1',105))
        self.assertTrue(c.claim_trade('garner',77,'1',106,addressed=True))
        self.assertFalse(c.claim_trade('garner',77,'0',107))
    def test_more_than_four_thousand_distinct_bounded_grounded_wordings(self):
        lines=set(variants('sale',item=684,count=3,price=5000,place='Аргент, 2232,2787'))
        self.assertGreaterEqual(len(lines),4000)
        self.assertTrue(all(len(t.encode('cp1251'))<=120 and 'ID684' in t and '5000G' in t for t in lines))

    def test_large_prices_and_locations_are_never_cut_out_of_the_core(self):
        text=render(random.Random(1),'sale',item=65535,count=99,price=2000000000,place='Ледынь, 4095,4095')
        self.assertIn('2000000000G',text);self.assertLessEqual(len(text.encode('cp1251')),120)

if __name__=='__main__':unittest.main()
