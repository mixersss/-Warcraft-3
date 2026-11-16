"""Authoritative owner services, small budgets and nonblocking diagnostics."""
import copy
import json
import random
import struct
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from async_console import AsyncConsole
from owner_services import OwnerServices,LOOT
from inventory import BagItem
from network_pump import NetworkPump
from economy import Economy
from town import Town,trade_page
from classic_wire import ProtocolError,string
from headless import Client
from loot import QuestLoot
from market import MarketCatalog,start_request
from market_prices import MarketPrices
from configure_dungeon_maps import configure,REQUIRED
import test_development as base
import test_coral_supplies as corals
import test_market as markets
from equipment import Equipment


def item(identity):return BagItem(identity,1,0,0,0,0,0,True)

def overlay():
    return {'npcs':[
        {'script_function':'OwnerProgress','position':[221150,271350]},
        {'script_function':'OwnerJewellery','position':[221450,271350]}]}


class OwnerServicesTests(unittest.TestCase):
    def test_level9_caster_earns_level10_with_confirmed_sword_then_requires_magic(self):
        import test_alpha42 as magic
        f=magic.MagicTests();w,p=f.make()
        w.own.values[0]=9;w.own.equipment={9:9}
        w.own.equipment_details={9:{'identity':9,'valid':True,'endurance':20}}
        p.owner_services=SimpleNamespace(busy=False,profession=lambda:None,tick=lambda *a:False)
        for entity in w.entities.values():
            if entity.control==5:entity.x=w.own.x+80;entity.y=w.own.y
        p.tick(100)
        self.assertEqual(f.last_skill(p),w.default_skill)
        p.send.reset_mock();w.own.values[0]=10;p.tick(105)
        self.assertIsNone(f.last_skill(p));self.assertIn('готовит магию',p.mode)

    def test_training_bridge_never_allows_bare_hands_broken_sword_or_advanced_jobs(self):
        import test_alpha42 as magic
        w,p=magic.MagicTests().make();c=p.combat_skills
        w.own.values[0]=9;c.reason='не выполнено требование оружия'
        w.own.equipment={9:9};w.own.equipment_details={9:{'identity':9,'valid':True,'endurance':20}}
        self.assertTrue(c.training_weapon_bridge())
        for changes in ({'endurance':0},{'valid':False},{'identity':8}):
            old=dict(w.own.equipment_details[9]);w.own.equipment_details[9].update(changes)
            self.assertFalse(c.training_weapon_bridge());w.own.equipment_details[9]=old
        for job in (13,14,16):
            w.own.values[4]=job;self.assertFalse(c.training_weapon_bridge())
        w.own.values[4]=5;c.reason='недостаточно SP';self.assertFalse(c.training_weapon_bridge())
        c.reason='не выполнено требование оружия';w.own.equipment={};self.assertFalse(c.training_weapon_bridge())

    def make(self,job=0,level=9):
        w=base.scene();w.own.values.update({0:level,4:job});w.bag_ready=True;w.bag_capacity=24
        w.own.x,w.own.y=221150,271350
        s=OwnerServices(w,{'first_job':4,'target_job':16},overlay(),Mock())
        p=SimpleNamespace(sequence=1,emit=Mock(),world=w,travel=None,nav=Mock(),position=lambda now:w.own.position,move_to=Mock(return_value=False))
        return w,s,p
    def test_first9_and_second40_never_overwrite_already_earned_other_profession(self):
        w,s,p=self.make();self.assertEqual(s.need(),('profession',4))
        w.own.values[4]=4;w.own.values[0]=39;w.skills[214]={'level':1}
        self.assertEqual(s.need(),('bags',48))
        w.own.values[0]=40;self.assertEqual(s.need(),('profession',16))
        w.own.values[4]=5;self.assertIsNone(s.profession())
    def test_restore_missing_spell_does_not_pretend_it_is_already_learned(self):
        w,s,p=self.make(5,20);self.assertEqual(s.need(),('combat',99))
        s.pending=('combat',99,(24,()),20)
        self.assertTrue(s.tick(10,p,True));self.assertEqual(s.confirmed,0)
        w.skills[99]={'level':1};s.tick(11,p,True);self.assertEqual(s.confirmed,1)
    def test_extenders_use_native_item_action_and_need_capacity_and_consumption(self):
        w,s,p=self.make(1,12);w.bag={0:item(3088),1:item(3089)}
        self.assertTrue(s.tick(1,p,True));self.assertEqual(p.emit.call_args.args[0][8:],b'\x0b'+struct.pack('>hh',0,-1))
        w.bag_capacity=28;s.tick(2,p,True);self.assertEqual(s.confirmed,0)
        del w.bag[0];s.tick(3,p,True);self.assertEqual(s.confirmed,1)
        self.assertTrue(s.tick(4,p,True));self.assertEqual(p.emit.call_args.args[0][-4:],struct.pack('>hh',1,-1))
    def test_service_selection_uses_actual_menu_and_same_npc(self):
        w,s,p=self.make();s.context=(99,'profession',4,20)
        payload=struct.pack('>IB',99,1)+string('Choose')+b'\x02'+string('Close')+string('First profession: Explorer')
        self.assertTrue(s.observe(802,payload,10));self.assertEqual(s.pending[:2],('profession',4))
        self.assertEqual(w.own.values[4],0);self.assertEqual(s.confirmed,0)
        w.own.values[4]=4;s.tick(11,p,False);self.assertEqual(s.confirmed,1)
    def test_capacity551_routes_to_world_and_keeps_items(self):
        w,s,p=self.make();w.bag={0:item(1847)}
        client=Client.__new__(Client);client.world_handler=w.observe
        client.service(551,struct.pack('>IH',w.own_id,28))
        self.assertEqual(w.bag_capacity,28);self.assertEqual(w.bag[0].identity,1847)
        client.service(551,struct.pack('>IH',999,48));self.assertEqual(w.bag_capacity,28)
        with self.assertRaises(ProtocolError):w.observe(551,struct.pack('>IH',w.own_id,0))


class SmallBudgetTests(unittest.TestCase):
    def test_voyager_ring_uses_native_right_flag_and_keeps_thunder_coral(self):
        w,t,p=corals.CoralSupplyTests().make();w.own.values[0]=35
        w.own.equipment[8]=872;w.bag={0:BagItem(285,1,100,100,0,0,0,True)}
        p.sequence=1;p.emit=Mock()
        e=Equipment(w,corals.GEAR,Mock())
        self.assertTrue(e.tick(100,p))
        self.assertEqual(e.pending[1],[8]);self.assertEqual(p.emit.call_args.args[0][-2:],struct.pack('>h',-2))
        self.assertEqual(w.own.equipment[7],867);self.assertEqual(e.confirmed,0)
    def test_earned_ground_gem_collects_but_player_throw_and_junk_do_not(self):
        w=base.scene();w.bag_ready=True;w.bag_capacity=48;w.own_hits={123:(9,True)}
        w.items={10:(1678,10,w.own.position,0,123,9),11:(863,11,w.own.position,1,2,9),12:(863,12,w.own.position,1,123,9)}
        loot=QuestLoot(w);loot.allowed_items=set(LOOT);loot.ground_gems={863}
        p=SimpleNamespace(position=lambda now:w.own.position,sequence=1,emit=Mock())
        self.assertTrue(loot.tick(10,p,LOOT))
        self.assertEqual(struct.unpack('>II',p.emit.call_args.args[0][-8:]),(12,12))
        self.assertEqual(loot.confirmed,0)
    def test_level_three_stall_has_eighteen_real_owned_gem_slots_and_bounded_prices(self):
        with patch('owner_shops.read_overlay',return_value={'catalog_revision':56,'prices':{}}):
            catalog=MarketCatalog(ROOT/'assets')
        catalog.enable_curated_catalog()
        w,_,m,p=markets.MarketTests().make();m.catalog=catalog;m.broad_goods=m.focused_goods=True
        w.skills={241:{'level':3}};w.bag={i:BagItem(863,1,0,0,1,1,0,True) for i in range(20)}
        rows=m.offers(p);self.assertEqual(len(rows),18)
        self.assertTrue(all(60000<=price<=150000 for _,price,_,_ in rows))
        self.assertEqual(set(catalog.items),LOOT-{1000,4915})
        self.assertIn(bytes([18]),start_request('Gems',rows))
    def test_last_one_gold_can_buy_essential_infinite_coral_without_fake_charge(self):
        w,t,p=corals.CoralSupplyTests().make(food=0)
        t.life=copy.copy(t.life);t.life.prices=dict(t.life.prices);t.life.prices.update({817:1,867:1,635:1})
        w.own.values[8]=1
        self.assertEqual(t.choose_want(),(867,1));self.assertEqual(t.spend_limit(867),1)
        plan=t.plan_supplies(100,p);self.assertEqual(plan['item'],867)
        self.assertEqual(w.own.values[8],1);self.assertEqual(w.own.equipment_details[7]['energy'],2)
    def test_only_three_work_phases_with_more_than_eighty_percent_xp(self):
        w=base.scene();w.own.values.update({0:35,4:1})
        orders=set()
        for name in ('one','two','three','four','five','six'):
            e=Economy(name,ROOT/'assets');e.focused=True;e.phase(w,100)
            self.assertEqual({k for k,_ in e.stages},{'progression','trade','income'})
            self.assertGreaterEqual(dict(e.stages)['progression'],1440)
            orders.add(tuple(k for k,_ in e.stages))
        self.assertGreater(len(orders),1)


class NetworkAndConsoleTests(unittest.TestCase):
    def test_slow_price_disk_write_does_not_lock_all_bot_price_queries(self):
        with tempfile.TemporaryDirectory() as directory:
            entered=threading.Event();release=threading.Event()
            original=Path.write_text
            def slow(path,*args,**kwargs):
                entered.set();release.wait(2);return original(path,*args,**kwargs)
            prices=MarketPrices(Path(directory)/'prices.json')
            try:
                with patch.object(Path,'write_text',slow):
                    prices.confirmed(863,80000,80000)
                    self.assertTrue(entered.wait(1));started=time.monotonic()
                    self.assertEqual(prices.guide(863,80000),80000)
                    self.assertLess(time.monotonic()-started,.2)
                    release.set();prices.save(force=True)
            finally:release.set()
    def test_blocked_console_cannot_block_worker_and_does_not_grow_without_limit(self):
        entered=threading.Event();release=threading.Event()
        def writer(text,**kwargs):entered.set();release.wait(2)
        c=AsyncConsole(writer,limit=4)
        try:
            c.emit('first');self.assertTrue(entered.wait(1))
            started=time.monotonic()
            for i in range(1000):c.emit('state',i)
            self.assertLess(time.monotonic()-started,.5)
            self.assertLessEqual(c.queue.qsize(),4);self.assertGreater(c.dropped,0)
        finally:release.set()
    def test_backlog_gate_uses_age_or_count_but_keeps_every_packet_in_order(self):
        pump=NetworkPump(SimpleNamespace())
        pump.queue.put((508,b'a',10));self.assertTrue(pump.backlogged(13))
        self.assertEqual(pump.receive(time.monotonic()+1),(508,b'a'))
        self.assertFalse(pump.backlogged(13))
        for i in range(256):pump.queue.put((509,bytes([i]),time.monotonic()))
        pump.bytes=256
        self.assertTrue(pump.backlogged())
        self.assertEqual([pump.receive(time.monotonic()+1)[1] for _ in range(256)],[bytes([i]) for i in range(256)])


class Map56Tests(unittest.TestCase):
    def test_static_mine_and_tower_need_no_nonexistent_entry_scripts(self):
        with tempfile.TemporaryDirectory() as directory:
            game=Path(directory);(game/'GameServer.cfg').write_text('map = garner\n')
            for name in (*REQUIRED,'lonetower'):
                folder=game/'resource'/name;folder.mkdir(parents=True)
                for suffix in ('.blk','.atr'):(folder/(name+suffix)).write_bytes(b'native unchanged')
            result=configure(game,True)
            self.assertIn('eastgoaf',result['added_maps']);self.assertIn('lonetower',result['added_maps'])
            self.assertFalse(configure(game,True)['applied'])


if __name__=='__main__':unittest.main()
