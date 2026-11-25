"""Charge-aware purchases and guarded disposal reproducing Alpha55 blockers."""
import dataclasses
import random
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from coral_supplies import damage_ready,spent_basic
from inventory import BagItem
from town import Town
from combat_skills import CombatSkills
from equipment import ItemCatalog
from life import LifeItems
import test_development as base
import test_alpha18 as vendor_base

GEAR=ItemCatalog(ROOT/'assets/items.json')
LIFE=LifeItems(ROOT/'assets')

def coral(energy=2,identity=867):
    return BagItem(identity,1,10000,10000,energy,100,0,True)


class CoralSupplyTests(unittest.TestCase):
    def make(self,food=3):
        w=base.scene();w.own.model=1
        w.own.values.update({0:24,4:4,8:700,1:100,31:100,7:0})
        w.bag_ready=True;w.bag_capacity=24
        w.bag={0:BagItem(1847,food,0,0,0,0,0,True),1:coral()}
        w.own.equipment={9:74,5:817,7:867}
        w.own.equipment_details={5:{'identity':817,'energy':100,'valid':True},7:{'identity':867,'energy':2,'valid':True}}
        w.skills={214:{'level':8,'state':1,'sp':30,'energy':8}}
        t=Town(w,LIFE,GEAR,None,random.Random(1),w.own.position)
        return w,t,SimpleNamespace(travel=None)

    def test_positive_charge_below_native_cost_is_not_ready(self):
        w,t,p=self.make();self.assertFalse(damage_ready(w,GEAR))
        w.own.equipment_details[7]['energy']=8
        self.assertTrue(damage_ready(w,GEAR))

    def test_wrong_identity_and_inactive_skill_are_not_readiness(self):
        w,t,p=self.make();w.own.equipment_details[7]['energy']=100
        w.own.equipment_details[7]['identity']=868
        self.assertFalse(damage_ready(w,GEAR))
        w.own.equipment_details[7]['identity']=867;w.skills[214]['state']=0
        self.assertFalse(damage_ready(w,GEAR))

    def test_advanced_voyager_can_continue_with_usable_strike(self):
        w,t,p=self.make();w.own.values[4]=16
        w.skills[216]={'level':1,'state':1,'energy':3}
        w.own.equipment[6]=635;w.own.equipment_details[6]={'identity':635,'valid':True,'energy':3}
        self.assertTrue(damage_ready(w,GEAR))

    def test_healthy_voyager_with_three_food_buys_thunder_before_optional_food(self):
        w,t,p=self.make();self.assertEqual(t.choose_want(),(867,1))
        plan=t.plan_supplies(100,p)
        self.assertEqual(plan['item'],867);self.assertEqual(plan['map'],'garner')
        self.assertIn(867,t.combat_items)
        self.assertEqual(w.own.values[8],700);self.assertEqual(w.bag[1].energy,2)

    def test_injured_or_foodless_voyager_keeps_medical_priority(self):
        for food,hp in ((1,100),(3,50)):
            w,t,p=self.make(food);w.own.values[1]=hp
            self.assertIsNone(t.plan_supplies(100,p))
            self.assertIn(t.choose_want()[0],(1847,1848,1849))

    def test_plain_depleted_copy_sellable_but_chargeable_spare_preserved(self):
        w,t,p=self.make();self.assertTrue(spent_basic(w,coral(2)))
        self.assertFalse(spent_basic(w,coral(8)))
        for changed in ({'identity':868},{'forge':1},{'parameters':(1,0)},
                        {'instance_attributes':((25,1),)},{'max_energy':500},{'valid':False}):
            self.assertFalse(spent_basic(w,dataclasses.replace(coral(),**changed)),changed)
        w.skills[214].pop('energy');self.assertFalse(spent_basic(w,coral()))

    def test_no_worn_replacement_means_keep_only_owned_coral(self):
        w,t,p=self.make();w.own.equipment.pop(7)
        self.assertFalse(spent_basic(w,coral()))

    def test_vendor_sells_spent_copies_and_keeps_charged_or_quest_copy(self):
        w,t,p=self.make();_,v,policy=vendor_base.VendorTests().make();v.world=w
        w.bag[2]=coral(100)
        self.assertEqual(v.choices(policy),[(1,867,1)])
        policy.story=SimpleNamespace(needed_items=lambda:{867})
        self.assertEqual(v.choices(policy),[])

    def test_timeout_diagnostics_keep_actual_bag_and_gold_instead_of_success(self):
        w,t,p=self.make();t.pending=(867,1,700,110);t.context=(99,'confirmation',110)
        t.tick(111,p,True)
        self.assertEqual(t.confirmed,0)
        self.assertEqual(t.summary()['last_purchase_failure']['bag_after'],1)
        self.assertEqual(t.last_purchase_failure['gold_after'],700)

    def test_report_includes_native_energy_cost(self):
        w,t,p=self.make();c=CombatSkills(w,GEAR,ROOT/'assets')
        self.assertEqual(c.summary()['native_skill_costs']['214']['energy'],8)


if __name__=='__main__':unittest.main()
