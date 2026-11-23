"""Native class clothing, chained chests, targeted magic and coral replacement."""
import copy,json,random,struct,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from equipment import Equipment,ItemCatalog
from life import LifeItems,Chests
from combat_skills import CombatSkills
from inventory import BagItem
from town import Town
from world import skip_look
from classic_wire import Reader
from navigation import Navigation
import test_development as base
import test_coordination as combat_base

GEAR=ItemCatalog(ROOT/'assets/items.json');LIFE=LifeItems(ROOT/'assets')
def item(identity,energy=0):return BagItem(identity,1,20,20,energy,100 if energy else 0,0,True)
def spell(level=1,sp=32,energy=0):return {'level':level,'state':1,'sp':sp,'interval_ms':6000,'energy':energy}

class ClothingTests(unittest.TestCase):
    def make(self,job=1,body=1):
        w=base.scene();w.own.model=body;w.own.values.update({0:15,4:job});w.bag_ready=True;w.bag_capacity=24
        w.own.equipment={2:4308,3:465,4:641,9:8};return w
    def test_every_first_class_chest_body_armour_equips_in_native_slot2(self):
        for job,body,identity in ((1,1,296),(2,3,311),(4,1,336),(4,4,351),(5,3,372),(5,4,359)):
            with self.subTest(job=job,body=body):
                w=self.make(job,body);w.bag={0:item(identity)};p=SimpleNamespace(sequence=1,emit=Mock())
                e=Equipment(w,GEAR,Mock());before=copy.deepcopy(w.own.equipment)
                self.assertTrue(e.tick(100,p));self.assertEqual(e.pending[:2],(identity,[2]))
                self.assertEqual(w.own.equipment,before);self.assertEqual(e.confirmed,0)
                self.assertEqual(p.emit.call_args.args[0][-4:],struct.pack('>hh',0,-1))
                w.own.equipment[2]=identity;e.tick(101,p);self.assertEqual(e.confirmed,1)
    def test_bought_complete_armour_gloves_boots_require_each_confirmation(self):
        w=self.make();w.bag={0:item(290),1:item(466),2:item(642)};p=SimpleNamespace(sequence=1,emit=Mock());e=Equipment(w,GEAR,Mock())
        worn=[]
        for n in range(3):
            self.assertTrue(e.tick(100+n*3,p));identity,links,_=e.pending;self.assertEqual(len(links),1)
            link=links[0];w.own.equipment[link]=identity
            w.bag={s:i for s,i in w.bag.items() if i.identity!=identity}
            e.tick(101+n*3,p);worn.append(link)
        self.assertEqual(set(worn),{2,3,4});self.assertEqual(e.confirmed,3)
    def test_next_owned_clothing_is_processed_before_starting_another_fight(self):
        w=self.make();w.bag={0:item(296),1:item(466)};p=SimpleNamespace(sequence=1,emit=Mock())
        e=Equipment(w,GEAR,Mock());e.tick(100,p);identity,links,_=e.pending
        w.own.equipment[links[0]]=identity;w.bag.pop(0)
        self.assertTrue(e.tick(101,p));self.assertTrue(e.tick(101.5,p))
        self.assertTrue(e.tick(102,p));self.assertEqual(e.pending[0],466)
    def test_chest_armour_level15_is_not_force_equipped_at_level10(self):
        w=self.make();w.own.values[0]=10;w.bag={0:item(296)}
        e=Equipment(w,GEAR,Mock());self.assertFalse(e.tick(100,Mock()))
        self.assertEqual(e.blockers[0]['reason'],'нужен уровень 15')
        w.own.values[0]=15;self.assertTrue(e.tick(101,Mock(sequence=1)))
    def test_wrong_class_does_not_equip_robe_by_shared_body(self):
        w=self.make(4,3);self.assertIsNone(GEAR.upgrade(w.own,372,20))
    def test_helmets_and_rings_now_have_real_native_slots(self):
        w=self.make(job=5,body=4);self.assertEqual(GEAR.upgrade(w.own,828,20)[1],[0])
        self.assertIn(281,GEAR.gear);self.assertEqual(GEAR.gear[281]['links'],[7,8])
    def test_pending_equipment_blocks_second_item_until_server_reply(self):
        w=self.make();w.bag={0:item(296),1:item(466)};p=SimpleNamespace(sequence=1,emit=Mock());e=Equipment(w,GEAR,Mock())
        e.tick(100,p);self.assertTrue(e.tick(101,p));self.assertEqual(p.emit.call_count,1)
        e.tick(113,p);self.assertEqual(e.failed,1)
    def test_entire_audited_chest_chain_known_with_real_space_and_level(self):
        self.assertEqual([LIFE.chests[i]['level'] for i in range(436,444)],[5,10,15,20,25,30,35,40])
        self.assertEqual(LIFE.chests[437]['free_slots'],7)
        w=self.make();w.bag={0:item(437)};c=Chests(w,LIFE);p=SimpleNamespace(sequence=1,emit=Mock())
        w.bag_capacity=7;self.assertFalse(c.tick(100,p,True))
        w.bag_capacity=24;self.assertTrue(c.tick(101,p,True));self.assertEqual(c.confirmed,0)
        w.bag={0:item(438),1:item(296)};c.tick(102,p,True);self.assertEqual(c.confirmed,1)
        e=Equipment(w,GEAR,Mock());self.assertTrue(e.tick(103,p));self.assertEqual(e.pending[0],296)
    def test_no_profession_still_cannot_open_class_chest(self):
        w=self.make(0);w.bag={0:item(437)};c=Chests(w,LIFE)
        self.assertFalse(c.tick(100,Mock(),True))

class MagicTests(unittest.TestCase):
    def make(self,job=5,body=3):
        f=combat_base.CohortCombatTests();f.nav=Navigation(ROOT/'assets/argent-navigation.json');w,p=f.policy()
        w.own.model=body;w.own.values.update({0:15,4:job,1:100,31:100,2:200,32:200})
        w.own.equipment={9:97};w.skills={99:spell()};w.default_skill=28
        p.combat_skills=CombatSkills(w,GEAR,ROOT/'assets');return w,p
    def last_skill(self,p):
        bodies=[c.args[1] for c in p.send.call_args_list if c.args[0]==6 and c.args[1][8]==2]
        return struct.unpack('>III',bodies[-1][-12:])[0] if bodies else None
    def test_herbalist_cleric_and_sealmaster_really_send_bolt_not_default_attack(self):
        for job in (5,13,14):
            w,p=self.make(job);p.tick(100)
            self.assertEqual(self.last_skill(p),99);self.assertEqual(p.combat_skills.requests,1)
            self.assertEqual(w.own.values[2],200) # No fabricated local SP deduction.
    def test_spell_uses_range800_instead_of_melee_chase(self):
        w,p=self.make();w.entities[1000].x=w.own.x+650
        from route_search import RoutePending
        p.approach=Mock(side_effect=RoutePending)
        p.tick(100)
        self.assertEqual(self.last_skill(p),99);self.assertEqual(p.moves,0)
        p.approach.assert_not_called()
    def test_cooldown_is_not_treated_as_repeating_auto_attack_or_spammed(self):
        w,p=self.make();p.tick(100);p.tick(103);self.assertEqual(p.combat_skills.requests,1)
        p.tick(105);self.assertEqual(p.combat_skills.requests,1)
        w.entities[1000].values[1]=90;p.tick(106.5)
        p.tick(108);self.assertEqual(p.combat_skills.requests,2)
    def test_queued_spell_keeps_selected_id_after_native_stop(self):
        w,p=self.make();p.action_open=True;p.last_sent_kind=1;p.clock=100;p.tick(100)
        self.assertIsNotNone(p.pending_action);self.assertEqual(p.combat_skills.requests,0)
        p.tick(101.2);self.assertEqual(self.last_skill(p),99);self.assertEqual(p.combat_skills.requests,1)
    def test_insufficient_sp_uses_real_recovery_and_never_casts(self):
        w,p=self.make();w.own.values[2]=0;p.tick(100)
        self.assertIsNone(self.last_skill(p));self.assertTrue(p.mana_resting);self.assertEqual(p.combat_skills.requests,0)
    def test_heal_targets_self_and_waits_for_native_hp_change(self):
        w,p=self.make();w.skills[97]=spell(sp=34);w.own.values[1]=60;p.tick(100)
        self.assertEqual(self.last_skill(p),97)
        body=[c.args[1] for c in p.send.call_args_list if c.args[0]==6 and c.args[1][8]==2][-1]
        self.assertEqual(struct.unpack('>III',body[-12:])[1],w.own_id);self.assertEqual(w.own.values[1],60)
        self.assertEqual(p.combat_skills.heals,1)
    def test_unlearned_inactive_wrong_weapon_and_wrong_class_do_not_cast(self):
        for change in ('unlearned','inactive','weapon','job'):
            w,p=self.make()
            if change=='unlearned':w.skills.clear()
            if change=='inactive':w.skills[99]['state']=0
            if change=='weapon':w.own.equipment={9:8}
            if change=='job':w.own.values[4]=1
            self.assertIsNone(p.combat_skills.select(100))
    def test_explorer_and_seavoyager_lightning_need_charged_equipped_thunder_coral(self):
        for job in (4,16):
            w,p=self.make(job,1);w.own.equipment={9:73,7:867};w.skills={214:spell(sp=27,energy=3)}
            w.own.equipment_details={7:{'identity':867,'energy':100,'valid':True}};p.tick(100)
            self.assertEqual(self.last_skill(p),214)
            w.own.equipment_details[7]['energy']=0
            self.assertIsNone(p.combat_skills.select(110))
    def test_seavoyager_conch_ray_uses_native_target_and_strike_coral(self):
        w,p=self.make(16,1);w.own.equipment={9:73,6:635};w.skills={216:spell(sp=23,energy=3)}
        w.own.equipment_details={6:{'identity':635,'energy':100,'valid':True}};p.tick(100)
        self.assertEqual(self.last_skill(p),216)
    def test_tornado_control_is_not_mistaken_for_primary_damage_or_mana_farm(self):
        w,p=self.make(4,1);w.own.equipment={9:73,5:817};w.skills={213:spell(energy=1)}
        w.own.equipment_details={5:{'identity':817,'energy':100,'valid':True}}
        self.assertIsNone(p.combat_skills.select(100));self.assertFalse(p.combat_skills.needs_mana(100))
        w.own.values[1]=60;self.assertEqual(p.combat_skills.control(100),213)
    def test_missing_wrong_and_unknown_charge_coral_do_not_fake_cast(self):
        w,p=self.make(4,1);w.skills={214:spell(energy=3)}
        for equip,details in (({},{}),({7:817},{}),({7:867},{})):
            w.own.equipment=equip;w.own.equipment_details=details
            self.assertIsNone(p.combat_skills.select(100))
    def test_real_safe_zone_still_prevents_magic_attack(self):
        w,p=self.make();p.nav.combat_allowed=Mock(return_value=False);p.tick(100)
        self.assertIsNone(self.last_skill(p))

class CoralTests(unittest.TestCase):
    def make(self):
        w=base.scene();w.own.values.update({0:15,4:4,8:1000,7:2});w.own.model=1
        w.bag_ready=True;w.bag_capacity=24;w.bag={0:BagItem(1847,10,0,0,0,0,0,True)}
        t=Town(w,LIFE,GEAR,{'first_job':4,'target_job':16},random.Random(1),w.own.position);return w,t
    def test_corals_are_equipped_and_depleted_identical_copy_needs_energy_confirmation(self):
        w,t=self.make();w.own.equipment={7:867};w.own.equipment_details={7:{'identity':867,'energy':0,'valid':False}}
        w.bag[1]=item(867,100);e=Equipment(w,GEAR,Mock());p=SimpleNamespace(emit=Mock(),sequence=1)
        self.assertTrue(e.tick(100,p));e.tick(101,p);self.assertEqual(e.confirmed,0)
        w.own.equipment_details[7].update(energy=100,valid=True);e.tick(102,p);self.assertEqual(e.confirmed,1)
    def test_critical_purchase_reserves_gold_and_can_buy150_coral_below600_gold(self):
        w,t=self.make();w.own.values[8]=300;w.skills={210:spell()}
        w.own.equipment={9:73};self.assertIn(867,t.critical_items());self.assertGreaterEqual(t.spend_limit(867),150)
        self.assertIn(t.choose_want()[0],t.critical_items());self.assertEqual(w.own.values[8],300)
    def test_charged_coral_and_owned_fresh_spare_prevent_repeat_purchase(self):
        w,t=self.make();w.own.equipment={7:867};w.own.equipment_details={7:{'identity':867,'energy':100,'valid':True}}
        self.assertNotIn(867,t.critical_items())
        w.own.equipment_details[7]['energy']=0;w.bag[1]=item(867,100)
        self.assertNotIn(867,t.critical_items())
    def test_partly_depleted_coral_is_replaced_when_charge_cannot_cover_next_spell(self):
        w,t=self.make();w.skills={214:spell(energy=4)};w.own.equipment={7:867}
        w.own.equipment_details={7:{'identity':867,'energy':2,'valid':True}}
        self.assertIn(867,t.critical_items());w.bag[1]=item(867,100)
        e=Equipment(w,GEAR,Mock());self.assertTrue(e.tick(100,Mock(sequence=1)))
    def test_herbalist_buys_usable_staff_before_optional_other_books(self):
        w,t=self.make();w.map='magicsea';w.own.model=3;w.own.values.update({4:5,8:6000});w.own.equipment={9:8}
        wanted=t.critical_items();self.assertTrue(wanted);self.assertEqual(GEAR.types[wanted[0]],9)
    def test_skillbag_native_cost_and_coral_charge_are_retained(self):
        w,t=self.make()
        payload=struct.pack('>HBHHBBHHHIH',28,0,1,214,1,2,29,0,4,8000,0)
        w.read_skills(Reader(payload));self.assertEqual(w.skills[214]['energy'],4)
        self.assertEqual(w.skills[214]['sp'],29);self.assertEqual(w.skills[214]['interval_ms'],8000)
    def test_native_look_full_and_short_keep_current_charge_without_packet_change(self):
        for sync in (0,1):
            data=struct.pack('>BHBH',sync,1,0,2000)
            for slot in range(10):
                if slot!=7:data+=b'\0\0';continue
                data+=struct.pack('>H',867)
                data+=struct.pack('>HHB',20,77,1) if sync else struct.pack('>HHHHHBBB',1,20,20,77,100,0,1,0)
            equipment={};details={};skip_look(Reader(data),equipment,details)
            self.assertEqual(equipment[7],867);self.assertEqual(details[7]['energy'],77)
