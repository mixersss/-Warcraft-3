"""Broad ordinary loot disposal while keeping progression and quest goods."""
import dataclasses
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import test_alpha18 as base

class BroadJunkTests(unittest.TestCase):
    def test_common_trophies_include_later_land_sea_and_expensive_plain_drops(self):
        f=base.VendorTests();w,v,p=f.make()
        ids=(1218,1584,1648,1661,1680,1696,1722,1778,1806,4321,4359,4368,
             4456,4494,4500,4519,4524,4538,4542,4803,4909)
        w.bag={slot:f.item(i,1) for slot,i in enumerate(ids)}
        self.assertEqual([i for _,i,_ in v.choices(p)],list(ids))
        self.assertGreater(v.junk[4500]['table_price'],100)

    def test_full_bag_of_new_common_trophies_is_sold_with_per_stack_confirmation(self):
        f=base.VendorTests();w,v,p=f.make();w.bag_capacity=48
        ids=(4321,4359,4368,4456,4494,4500,4519,4524)
        w.bag={slot:f.item(ids[slot%len(ids)],3) for slot in range(48)}
        w.entities[77]=dataclasses.replace(w.own,identity=77,control=2)
        v.context=77,'ready',200
        for slot in range(48):
            v.tick(100+slot*2,p,True)
            self.assertEqual(v.pending[:3],(slot,ids[slot%len(ids)],3))
            self.assertIn(slot,w.bag)
            w.bag.pop(slot);w.own.values[8]+=1
            v.tick(101+slot*2,p,True)
        self.assertEqual(v.confirmed_sales,48);self.assertEqual(len(w.bag),0)
        self.assertFalse(v.tick(197,p,True))

    def test_expansion_keeps_quest_stacks_modified_instances_and_valuable_goods(self):
        f=base.VendorTests();w,v,p=f.make()
        protected=(1000,1001,1002,436,437,444,3296,3164,3457,885,1012,3425,
                   1746,1754,3387,3388,3391,3363,3364,3367,3380,1631,1641,289)
        w.bag={slot:f.item(i,1) for slot,i in enumerate(protected)}
        self.assertEqual(v.choices(p),[])
        w.bag={0:f.item(4500,3),1:dataclasses.replace(f.item(4321,3),parameters=(1,0))}
        p.adventure=SimpleNamespace(farm=lambda:None,journal={700:0},grind={700:(None,4500)})
        self.assertEqual(v.choices(p),[])
        p.adventure.journal.clear()
        self.assertEqual(v.choices(p),[(0,4500,3)])

    def test_missing_sale_confirmation_keeps_new_material_and_backs_off(self):
        f=base.VendorTests();w,v,p=f.make();w.bag={0:f.item(4500,3)}
        w.entities[77]=dataclasses.replace(w.own,identity=77,control=2)
        v.context=77,'ready',200;v.tick(100,p,True);v.tick(113,p,True)
        self.assertEqual(w.bag[0].count,3);self.assertEqual(v.confirmed_sales,0)
        self.assertEqual(v.sale_timeouts,1);self.assertGreater(v.next_sale,113)

if __name__=='__main__':unittest.main()
