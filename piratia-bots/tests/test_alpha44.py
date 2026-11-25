"""Current-level farming regressions and real class/stall skill prerequisites."""
import sys, unittest
import dataclasses,struct
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from farm_plan import FIELDS
from skill_plan import SkillPlan
import test_alpha43 as previous


class FarmEfficiencyTests(unittest.TestCase):
    def make(self):
        w,l,r=previous.HuntTierTests().make()
        r['farms'].pop('258')
        for model,xp in ((227,20),(999,200)):
            l.rows[str(model)]={k:0 for k in FIELDS}
            l.rows[str(model)].update(wins=2,xp=xp,observed_level=20,
                level_wins=2,level_xp=xp,level_seconds=20)
        return w,l,r

    def test_bad_measured_farm_not_kept_as_nearest_alternative(self):
        w,l,r=self.make()
        self.assertEqual(l.choose(r,w.own,100,position=(1000,0)),{999})
        self.assertNotIn(227,l.admissible(r,w.own,100))
        self.assertEqual(l.summary()['inefficient_models'],[227])

    def test_blocked_benchmark_does_not_veto_safe_work(self):
        w,l,r=self.make();l.avoid[999]=500
        self.assertIn(227,l.choose(r,w.own,100))
        self.assertIn(227,l.admissible(r,w.own,100))

    def test_previous_level_and_single_fight_do_not_veto_species(self):
        for field,value in (('observed_level',19),('level_wins',1)):
            with self.subTest(field=field):
                w,l,r=self.make();l.rows['227'][field]=value
                self.assertIn(227,l.choose(r,w.own,100))

    def test_zero_xp_species_yields_to_confirmed_earning_species(self):
        w,l,r=self.make();l.rows['227']['level_xp']=0
        self.assertNotIn(227,l.choose(r,w.own,100))
        self.assertEqual(l.rows['227']['wins'],2) # No fabricated loss or reward.

    def test_dangerous_benchmark_not_an_opportunistic_target(self):
        w,l,r=self.make();l.danger_until[999]=500
        self.assertEqual(l.admissible(r,w.own,100),{227})


class StallBookBudgetTests(unittest.TestCase):
    def test_stall_book_needs_actual_price_plus_reserve_not_twenty_thousand(self):
        w,t,p=previous.ShoppingTests().make(job=1,body=1)
        from inventory import BagItem
        w.own.values.update({0:20,4:1,13:1,8:5100})
        w.bag={0:BagItem(1847,10,0,0,0,0,0,True)}
        w.bag[47]=BagItem(4602,2,0,0,0,0,0,True) # Test book budget after the emergency ticket is stocked.
        # Isolate the life-skill request from separate class skill requirements.
        t.role=None
        self.assertIn(3296,t.critical_items())
        self.assertEqual(t.choose_want(),(3296,1))
        w.own.values[8]=5099
        self.assertNotEqual(t.choose_want(),(3296,1))
        w.own.values[13]=0
        self.assertNotIn(3296,t.critical_items())


class SkillPrerequisiteTests(unittest.TestCase):
    def make(self):
        from test_development import scene
        from life import LifeItems
        from test_adventure import role
        w=scene();w.own.values.update({0:20,4:4,7:1})
        life=LifeItems(ROOT/'assets')
        return w,life,SkillPlan(w,role(4),life)

    def test_marine_learns_diligence_before_lightning(self):
        w,life,plan=self.make();steps=plan.next_steps()
        self.assertEqual(steps[0]['skill'],210)
        self.assertEqual(steps[0]['blocker'],'нужна книга')
        self.assertIn(steps[0]['book'],plan.missing_books())

    def test_upgrade_uses_earned_single_point_instead_of_reserving_two(self):
        w,life,plan=self.make();w.skills[210]={'level':1}
        steps=plan.next_steps()
        self.assertTrue(any(s['skill']==210 and not s['blocker'] and s['action']=='upgrade' for s in steps))

    def test_no_book_purchase_without_real_skill_points(self):
        w,life,plan=self.make();w.own.values[7]=0
        self.assertEqual(plan.missing_books(),[])
        self.assertTrue(all(s['blocker']=='нужны очки навыков' for s in plan.next_steps()))


class BankTests(unittest.TestCase):
    def make(self):
        import test_market
        from bank import Bank
        w,send,market,policy=test_market.MarketTests().make()
        policy.market=market;w.item_types=market.gear.types
        bank=Bank(w,send,market.life.npcs)
        return w,send,market,policy,bank

    def packet(self,w,identity=684,count=3,slot=0,sync=0,capacity=48):
        body=bytes([sync])+(struct.pack('>H',capacity) if sync==0 else b'')
        body+=struct.pack('>HH5HBB2IBH',slot,identity,count,100,100,0,0,0,1,0,0,0,65535)
        return struct.pack('>IIB',w.own_id,1,26)+body

    def test_classic_vault_snapshot_is_separate_from_bag(self):
        w,s,m,p,b=self.make();before=dict(w.bag)
        w.observe(508,self.packet(w));self.assertTrue(w.bank_ready)
        self.assertEqual(w.bank[0].identity,684);self.assertEqual(w.bag,before)
        self.assertEqual(w.bank_revision,1)

    def test_corrupt_or_uninitialised_delta_does_not_mutate_vault(self):
        for payload in ('truncated','out_of_range','delta'):
            with self.subTest(payload=payload):
                w,s,m,p,b=self.make()
                packet=self.packet(w,slot=49 if payload=='out_of_range' else 0,sync=1 if payload=='delta' else 0)
                if payload=='truncated':packet=packet[:-1]
                w.observe(508,packet)
                self.assertTrue(w.bank_disabled);self.assertFalse(w.bank_ready);self.assertEqual(w.bank,{})

    def test_deposit_requires_both_native_inventory_deltas(self):
        from inventory import BagItem
        w,s,m,p,b=self.make();item=BagItem(684,3,100,100,0,0,0,True)
        w.bag={0:item};w.bank_ready=True;w.bank_capacity=48;b.state='open'
        self.assertTrue(b.tick(10,p,True));body=p.emit.call_args.args[0]
        self.assertEqual(body[8],26);self.assertEqual(body[9:],struct.pack('>BHHBH',0,0,3,1,0))
        self.assertEqual(w.bag[0],item);self.assertEqual(w.bank,{})
        w.bag={};b.tick(11,p,True);self.assertEqual(b.deposits,0)
        w.bank={0:item};b.tick(12,p,True);self.assertEqual(b.deposits,1)

    def test_withdrawal_requires_bag_and_bank_confirmations(self):
        from inventory import BagItem
        w,s,m,p,b=self.make();item=BagItem(684,2,100,100,0,0,0,True)
        w.bag={};w.bank={0:item};w.bank_ready=True;w.bank_capacity=48
        b.state='open';b.mode='withdraw';b.tick(10,p,True)
        self.assertEqual(p.emit.call_args.args[0][9:],struct.pack('>BHHBH',1,0,2,0,0))
        w.bank={};b.tick(11,p,True);self.assertEqual(b.withdrawals,0)
        w.bag={0:item};b.tick(12,p,True);self.assertEqual(b.withdrawals,1)

    def test_timeout_preserves_items_and_releases_work(self):
        from inventory import BagItem
        w,s,m,p,b=self.make();item=BagItem(684,3,100,100,0,0,0,True)
        w.bag={0:item};w.bank_ready=True;w.bank_capacity=48;b.state='open'
        b.tick(10,p,True);b.tick(23,p,True)
        self.assertFalse(b.busy);self.assertEqual(b.timeouts,1)
        self.assertEqual(w.bag,{0:item});self.assertEqual(b.deposits,0)
        self.assertEqual(p.emit.call_args.args[0][8],27)

    def test_completed_quest_items_and_stall_book_cannot_be_archived(self):
        from inventory import BagItem
        w,s,m,p,b=self.make();w.bag={0:BagItem(684,3,100,100,0,0,0,True)}
        p.story=SimpleNamespace(needed_items=lambda:set(),active=lambda:True,
                               quest={'needs':[{'kind':1,'id':684,'count':3}]})
        self.assertEqual(b.candidates(p),[])

    def test_menu_requires_actual_source_and_a_known_fee(self):
        from classic_wire import string
        from bank import Bank
        w,s,m,p,b=self.make();b.state='talk';b.context=77
        packet=struct.pack('>IB',77,1)+string('Bank')+bytes([1])+string('Vault (200G Fee)')
        self.assertTrue(b.observe(802,packet,10));self.assertEqual(s.call_args.args[0],301)
        self.assertEqual(b.state,'opening');self.assertEqual(b.deposits,0)

    def test_bank_trip_without_position_progress_yields_to_other_work(self):
        from inventory import BagItem
        w,s,m,p,b=self.make();w.bag_capacity=8;w.bag={0:BagItem(684,3,100,100,0,0,0,True)}
        self.assertTrue(b.tick(0,p,True))
        self.assertFalse(b.tick(36,p,True));self.assertGreater(b.next_visit,36)
        self.assertFalse(b.busy);self.assertEqual(w.bag[0].count,3)


class GroupHealingTests(unittest.TestCase):
    def make(self):
        import test_alpha42 as old
        w,p=old.MagicTests().make()
        w.skills[97]=old.spell(sp=34)
        peer=dataclasses.replace(w.own,identity=333,handle=433,name='Human',
            x=w.own.x+50,values=dict(w.own.values))
        peer.values[1]=30;w.entities[333]=peer
        p.party=SimpleNamespace(members=(w.own.name,'Human'))
        return w,p,peer

    def test_heals_only_confirmed_visible_group_member_without_local_hp_change(self):
        w,p,peer=self.make();before=peer.values[1];p.tick(100)
        self.assertEqual(struct.unpack('>III',p.send.call_args.args[1][-12:]),(97,peer.identity,peer.handle))
        self.assertEqual(peer.values[1],before)

    def test_stranger_is_not_a_group_patient(self):
        w,p,peer=self.make();p.party.members=(w.own.name,)
        self.assertIsNone(p.combat_skills.healing_target(97,p.party,100))

    def test_queued_heal_rechecks_membership(self):
        from hunter import normal_attack
        w,p,peer=self.make()
        p.pending_action=(normal_attack(w.own_id,1,1,97,peer.identity,peer.handle,w.own.position),100,100,w.stop_revision)
        p.party.members=();p.send.reset_mock();p.flush_action(101)
        p.send.assert_not_called()

    def test_swordsman_and_archer_both_habitat_skills_are_entity_casts(self):
        import test_alpha42 as old
        for job,skill,link,kind in ((1,81,9,1),(2,90,6,3)):
            with self.subTest(job=job):
                w,p=old.MagicTests().make();w.own.model=1;w.own.values[4]=job
                item=next(i for i,k in p.combat_skills.catalog.types.items() if k==kind)
                w.own.equipment={link:item};w.skills={skill:old.spell()}
                self.assertEqual(p.combat_skills.select(100),skill)
                p.tick(100);self.assertEqual(struct.unpack('>III',p.send.call_args.args[1][-12:])[0],skill)


if __name__=='__main__':unittest.main()
