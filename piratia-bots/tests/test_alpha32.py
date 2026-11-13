"""Observed common loot, shared quest mobs and continued earned development."""
import dataclasses
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from coordination import Coordination
from loot import QuestLoot
from skills import Skills
from progression import Progression
from equipment import Equipment,ItemCatalog
from life import LifeItems
from show_diagnostics import render_report
import test_alpha18 as sales
import test_alpha26 as quests

class CommonLootTests(unittest.TestCase):
    def test_observed_grass_shells_and_materials_sell_but_valuables_stay(self):
        f=sales.VendorTests();w,v,p=f.make()
        junk=(4315,4319,4400,4322,3116,1574,1573,1777,4401,1690,3129)
        valuable=(1000,436,437,444,3296,1847,3387,3388,289,3950)
        w.bag={slot:f.item(i,3) for slot,i in enumerate(junk+valuable)}
        self.assertEqual([i for _,i,_ in v.choices(p)],list(junk))
        self.assertTrue(all(i not in v.junk for i in valuable))
        w.bag[0]=dataclasses.replace(w.bag[0],forge=1)
        self.assertNotIn(4315,[i for _,i,_ in v.choices(p)])

    def test_complete_quest_ingredient_stack_stays_until_delivery(self):
        f=sales.VendorTests();w,v,p=f.make();w.bag={0:f.item(3116,10),1:f.item(4315,99)}
        p.story=SimpleNamespace(needed_items=lambda:set(),active=lambda:True,
            quest={'needs':[{'kind':1,'id':3116,'count':10}]})
        self.assertEqual(v.choices(p),[(1,4315,99)])
        p.story.active=lambda:False
        self.assertEqual(v.choices(p),[(0,3116,10),(1,4315,99)])

    def test_new_material_sale_requires_real_bag_and_gold_confirmation(self):
        f=sales.VendorTests();w,v,p=f.make();w.bag={0:f.item(4319,99)}
        w.entities[77]=dataclasses.replace(w.own,identity=77,control=2)
        v.context=77,'ready',200;v.tick(100,p,True)
        self.assertEqual(v.pending[:3],(0,4319,99));self.assertEqual(w.bag[0].count,99)
        w.bag.clear();v.tick(101,p,True);self.assertEqual(v.confirmed_sales,0)
        w.own.values[8]+=99;v.tick(102,p,True);self.assertEqual(v.confirmed_sales,1)

class QuestCompetitionTests(unittest.TestCase):
    def policy(self,index,coordination):
        w,p,q=quests.ProfessionSchedulingTests().policy(1)
        w.own.values[0]=10;q.journal={62:0}
        w.entities[1000].model=237;w.entities[1000].values[0]=10
        p.owner=str(index);p.coordination=coordination
        return w,p,q

    def test_twenty_swordsman_quest_bots_attack_same_pig_and_keep_half_hp_target(self):
        c=Coordination();pairs=[self.policy(i,c) for i in range(20)]
        for w,p,q in pairs:p.tick(100)
        self.assertTrue(all(p.target==1000 and p.attacks==1 for _,p,_ in pairs))
        for w,p,q in pairs:
            w.entities[1000].values[1]=50;p.tick(104)
            self.assertEqual(p.target,1000);self.assertEqual(p.no_damage_retargets,0)
        c.release('0');self.assertTrue(c.claim('outside',('garner',1000,2000),105))
        for w,p,q in pairs:
            w.entities[1000].values[1]=25;p.tick(108)
            self.assertEqual(p.target,1000)

    def test_shared_claim_keeps_ordinary_holder_and_default_exclusivity(self):
        c=Coordination();key=('garner',1,2);c.claim('first',key,0)
        self.assertTrue(c.claim('quest',key,1,shared=True));self.assertEqual(c.targets[key][0],'first')
        c.release('quest');self.assertFalse(c.available('other',key,2));self.assertFalse(c.claim('other',key,2))

    def test_crowded_quest_endpoint_still_requires_real_navigation(self):
        w,p,q=self.policy(0,Coordination());mob=w.entities[1000];mob.x+=700
        p.available_spot=lambda point,now:False
        point=p.approach(mob,p.attack_reach(mob),100)
        self.assertIsNotNone(point);self.assertTrue(p.nav.path(w.own.position,point))
        q.journal.clear();self.assertIsNone(p.approach(mob,p.attack_reach(mob),101))

    def loot(self):
        w,_,_=sales.VendorTests().make()
        p=SimpleNamespace(position=lambda now:w.own.position,sequence=1,emit=Mock())
        l=QuestLoot(w,True);l.competitive={3129}
        w.items={500:(3129,1500,w.own.position,0,999,0)}
        return w,p,l

    def test_quest_drop_contested_but_server_must_confirm(self):
        w,p,l=self.loot();self.assertTrue(l.tick(1,p,{3129}));self.assertEqual(l.confirmed,0)
        w.bag={0:sales.VendorTests().item(3129,1)};l.tick(2,p,{3129});self.assertEqual(l.confirmed,0)
        w.items.clear();l.tick(3,p,{3129});self.assertEqual(l.confirmed,1)
        w.items={501:(4315,1501,w.own.position,0,999,0),502:(3129,1502,w.own.position,1,999,0)}
        self.assertFalse(l.tick(4,p,{4315,3129}))

    def test_competing_drop_refusal_has_bounded_retry_without_reward(self):
        w,p,l=self.loot()
        for now in (1,12,21,32,41,50):l.tick(now,p,{3129})
        self.assertEqual(l.requests,2);self.assertEqual(l.confirmed,0);self.assertFalse(w.bag)

class PostProfessionTests(unittest.TestCase):
    def test_real_promotion_continues_stats_skill_equipment_and_hunting(self):
        f=sales.VendorTests();w,p,q=quests.ProfessionSchedulingTests().policy(1)
        w.own.values.update({0:15,4:1,6:1,7:1,25:5,28:5});q.journal={62:0}
        self.assertIsNone(q.farm());self.assertFalse(q.profession_priority())
        ap=Progression(w,p.send,1);ap.target_job=9;ap.tick(100,True);self.assertEqual(ap.requests,1)
        attr,total,points,_=ap.pending;w.own.values[attr]=total;w.own.values[6]-=1;ap.tick(101,True)
        self.assertEqual(ap.confirmed,1)
        w.bag_ready=True;w.bag_capacity=48;w.bag={0:f.item(3164,1)}
        p.skills=Skills(w,{'first_job':1,'target_job':9},LifeItems(ROOT/'assets'))
        p.tick(102);self.assertEqual(p.skills.requests,1)
        w.skills[66]={'level':1};w.own.values[7]=0;w.bag.clear()
        catalog=ItemCatalog(ROOT/'assets/items.json')
        gear=next((i,g) for i,g in catalog.gear.items() if g['level']<=15 and w.own.model in g['bodies']
            and (g['jobs']==[-1] or 1 in g['jobs']) and g['links'] and all(n in (2,3,4,9) for n in g['links']))
        w.bag={1:f.item(gear[0],1)};p.equipment=Equipment(w,catalog,p.send)
        p.tick(104);self.assertEqual(p.skills.confirmed,1);self.assertEqual(p.equipment.requests,1)
        p.tick(105.1)  # Flush the queued item action before its server acknowledgement.
        w.own.equipment[gear[1]['links'][0]]=gear[0]
        w.entities[1000].model=next(iter(p.planned_models()))
        p.tick(106);self.assertEqual(p.equipment.confirmed,1)
        p.tick(107.1)  # Native attack may wait for the preceding item action to stop.
        self.assertEqual(p.target,1000);self.assertGreater(p.attacks,0);self.assertEqual(w.own.values[4],1)

    def test_diagnostic_shows_runtime_version(self):
        self.assertIn('AutoAccountsAlpha32',render_report({'version':'AutoAccountsAlpha32'}))

if __name__=='__main__':unittest.main()
