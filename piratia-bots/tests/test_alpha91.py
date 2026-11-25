"""Regressions for the owner Alpha90 Fix9 fleet: real progress, bounded errands."""
import copy
import json
import random
import struct
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import test_alpha11 as inventory
import test_alpha42 as magic
import test_alpha56 as services
import test_alpha86 as live
import test_market as stalls
import test_pet_economy as pets
from audit_leveling import audit
from coordination import Coordination
from recovery import Recovery
from skills import Skills
from xp_boosters import XPBoosters


class Recovery91Tests(unittest.TestCase):
    def make(self):
        w,p=magic.MagicTests().make();w.bag_ready=True;w.bag_capacity=48
        w.own.values.update({1:300,31:1500,2:1000,32:1000})
        p.emit=Mock();return w,p,Recovery(w)

    def test_developed_character_uses_owned_stronger_food_not_reputation_cake(self):
        w,p,r=self.make();w.bag={0:pets.item(1847,10),1:pets.item(3128,3),2:pets.item(2988,1)}
        self.assertTrue(r.tick(10,p));self.assertEqual(p.emit.call_args.args[0][-4:],struct.pack('>hh',1,-1))
        self.assertEqual(w.own.values[1],300);self.assertEqual(w.bag[1].count,3)

    def test_bag_move_and_natural_regeneration_are_not_consumption(self):
        w,p,r=self.make();w.bag={0:pets.item(3128,3)};r.tick(10,p)
        w.bag[4]=w.bag.pop(0);w.own.values[1]=320;r.tick(11,p)
        self.assertEqual(r.confirmed,0)
        w.bag[4]=replace(w.bag[4],count=2);r.tick(12,p)
        self.assertEqual(r.confirmed,1)

    def test_sp_food_requires_both_actual_consumption_and_sp_increase(self):
        w,p,r=self.make();w.own.values.update({1:1500,2:20});w.bag={0:pets.item(3140,2)}
        self.assertTrue(r.tick(10,p));w.bag[0]=replace(w.bag[0],count=1);r.tick(11,p)
        self.assertEqual(r.confirmed,0);w.own.values[2]=221;r.tick(12,p)
        self.assertEqual(r.confirmed,1)

    def test_reputation_and_buff_foods_are_never_hp_or_sp_replacements(self):
        w,p,r=self.make();w.bag={0:pets.item(2988),1:pets.item(3844),2:pets.item(4019)}
        self.assertFalse(r.tick(10,p));p.emit.assert_not_called()


class Progress91Tests(unittest.TestCase):
    def test_missing_future_book_does_not_block_affordable_owned_bolt_upgrade(self):
        w,p=magic.MagicTests().make();w.own.values.update({0:41,4:13,7:2})
        w.skills[99]={'level':3};s=Skills(w,{'first_job':5,'target_job':13})
        blocked={'skill':225,'target_level':1,'cost':1,'blocker':'нужна книга'}
        upgrade={'skill':99,'target_level':4,'cost':1,'bag_slot':None,'action':'upgrade','blocker':''}
        s.plan=SimpleNamespace(guides=True,next_steps=lambda *args:[blocked,upgrade])
        p.send=Mock();self.assertTrue(s.tick(100,p,True));p.send.assert_called_once_with(11,struct.pack('>HB',99,1))
        self.assertEqual(w.skills[99]['level'],3);self.assertEqual(w.own.values[7],2)
        w.skills[99]['level']=4;s.tick(101,p,True);self.assertEqual(s.confirmed,0)
        w.own.values[7]=1;s.tick(102,p,True);self.assertEqual(s.confirmed,1)

    def test_last_point_is_reserved_for_next_missing_guide_book(self):
        w,p=magic.MagicTests().make();w.own.values.update({0:41,4:13,7:1})
        s=Skills(w,{'first_job':5,'target_job':13})
        s.plan=SimpleNamespace(guides=True,next_steps=lambda *args:[{'cost':1,'blocker':'нужна книга'},{'cost':1,'blocker':''}])
        self.assertFalse(s.tick(100,p,True))

    def test_booster_rank_and_nearby_fallback_respect_level_and_actual_offer(self):
        w,p=magic.MagicTests().make();w.own.values.update({0:43,8:40000})
        w.bag={};life=SimpleNamespace(prices={3094:10000,3879:10000,3095:10000,3880:10000})
        b=XPBoosters(w,life,SimpleNamespace(phase=lambda *a:'progression'))
        self.assertEqual(b.purchase_goals()[0][0],3879)
        self.assertEqual(b.purchase_goals(offers={3094})[0][0],3094)
        w.own.values[0]=60;self.assertEqual(b.purchase_goals()[0][0],3095)
        w.own_states={48:1};self.assertEqual(b.purchase_goals(),[])

    def test_delayed_booster_echo_does_not_pause_combat_or_fake_buff(self):
        w,p=magic.MagicTests().make();w.bag_ready=True;w.bag={0:pets.item(3879)};w.own.values[0]=43
        b=XPBoosters(w,pets.LIFE,SimpleNamespace(phase=lambda *a:'progression'));p.emit=Mock()
        self.assertTrue(b.tick(100,p,True));self.assertFalse(b.tick(114,p,True))
        self.assertEqual(b.timeouts,0);self.assertEqual(b.confirmed,0)
        del w.bag[0];w.own_states={48:2};b.tick(115,p,True);self.assertEqual(b.confirmed,1)

    def test_fairy_berry_already_in_flight_prevents_second_booster_use(self):
        w,p=magic.MagicTests().make();w.bag_ready=True;w.bag={0:pets.item(3844)}
        p.petcare=SimpleNamespace(pending={'kind':'berry'});p.emit=Mock()
        b=XPBoosters(w,pets.LIFE,SimpleNamespace(phase=lambda *a:'progression'))
        self.assertFalse(b.tick(100,p,True));p.emit.assert_not_called()

    def test_camp_cache_reuses_geometry_but_checks_new_blacklist(self):
        w,p=magic.MagicTests().make();p.coordination=None;p.nav=Mock()
        p.nav.local=None;p.nav.land_component.return_value=1;p.nav.nearest.side_effect=lambda x:tuple(x)
        points=[[100,200],[300,400]]
        self.assertEqual(p.reachable_camp_goals(points,10),[(100,200),(300,400)])
        p.goal_blacklist[(100,200)]=100
        self.assertEqual(p.reachable_camp_goals(points,11),[(300,400)])
        self.assertEqual(p.nav.nearest.call_count,2)

    def test_voyager_never_displaces_coral_with_ring_in_occupied_hands(self):
        w,t,p=services.corals.CoralSupplyTests().make();w.own.values[0]=35
        w.bag={0:services.BagItem(285,1,100,100,0,0,0,True)}
        e=services.Equipment(w,services.corals.GEAR,Mock())
        w.own.equipment[8]=286;p.emit=Mock();self.assertFalse(e.tick(100,p))
        self.assertEqual(w.own.equipment[7],867);p.emit.assert_not_called()


class TradeAndAudit91Tests(unittest.TestCase):
    def test_real_surplus_stock_can_trade_despite_xp_starvation(self):
        w,send,m,p=stalls.MarketTests().make();m.gem_only=True;m.gem_seller=True
        p.started=0;m.next_shift=0;w.skills[241]={'level':3}
        w.bag={0:replace(stalls.MarketTests().item(885,12),max_energy=1)}
        self.assertTrue(m.sale_due(p,300))
        w.map='magicsea';self.assertFalse(m.sale_due(p,300))
        w.map='garner';w.bag={};self.assertFalse(m.sale_due(p,300))

    def test_full_gem_bag_yields_hunt_priority_without_free_items(self):
        w,p=magic.MagicTests().make();w.bag_ready=True;w.bag_capacity=3
        w.bag={0:pets.item(885)};p.fast_progression=True
        self.assertFalse(p.hunt_before_errands(300));self.assertEqual(w.bag[0].count,1)

    def test_shared_empty_camp_expires_and_does_not_hide_other_maps(self):
        directory=Coordination();point=(220000,270000)
        directory.note_empty_camp('garner',point,100)
        self.assertEqual(directory.available_camps('garner',[point],101),[])
        self.assertEqual(directory.available_camps('magicsea',[point],101),[point])
        self.assertEqual(directory.available_camps('garner',[point],131),[point])

    def test_gem_reservation_is_bounded_and_does_not_hide_all_earned_stock(self):
        w,send,m,p=stalls.MarketTests().make();w.bag={0:stalls.MarketTests().item(863,20)}
        m.forging_economy=True;m.catalog.focused_prices[863]=100000
        m.crafting=SimpleNamespace(stone_needs=Mock(return_value={863:20}))
        self.assertEqual(m.reserve_count(863),2)
        self.assertEqual(m.reserve_count(863),2);self.assertEqual(m.crafting.stone_needs.call_count,1)

    def test_gem_only_stalls_exclude_other_loot_and_have_finite_longer_shift(self):
        w,send,m,p=stalls.MarketTests().make();m.gem_only=True;m.gem_seller=True
        w.bag={0:replace(stalls.MarketTests().item(885,12),max_energy=1),1:stalls.MarketTests().item(3428,20)}
        self.assertTrue(m.offers(p));self.assertTrue(all(w.bag[row[3]].identity in m.gem_ids() for row in m.offers(p)))
        m.opened(100);self.assertGreaterEqual(m.trade_until,700);self.assertLessEqual(m.trade_until,1000)

    def test_audit_ignores_credentials_and_records_zero_xp_without_claiming_root_cause(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'accounts.json').write_text('DO NOT READ')
            (root/'bot-report-2.json').write_text(json.dumps({'bot_index':2,'hunt':{'world':{'level':41,'profession':13},'hunting_learning':{'session_xp_net':0,'seconds_without_xp':700}}}))
            (root/'bot-report-3.json').write_text('broken')
            result=audit(root);self.assertEqual(result['reports'],1);self.assertEqual(result['no_xp_10min'],1)
            self.assertEqual(result['read_errors'],[{'file':'bot-report-3.json','error':'JSONDecodeError'}])
            self.assertNotIn('DO NOT READ',json.dumps(result))


if __name__=='__main__':unittest.main()
