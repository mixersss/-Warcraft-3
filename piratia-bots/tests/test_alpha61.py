"""Land hunting, real supply deadlocks and pre-quote repair refusals."""
import copy,dataclasses,json,random,struct,sys,unittest
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import test_alpha53 as repair_examples
import test_alpha60 as supply_examples
import test_alpha42 as magic
import test_alpha26 as scheduling
import test_pet_economy as pets
from classic_wire import string
from farm_plan import HuntLearning
from regions import Regions
from town import Town

class Ground61Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.regions=Regions(ROOT/'assets',400)
 def test_home_camps_exclude_all_known_sea_species_but_preserve_sea_knowledge(self):
  removed=0
  original=json.loads((ROOT/'assets/regions.json').read_text())
  for name,old in original.items():
   farms=self.regions.get(name)['farms']
   for key in old['farms']:
    mob=self.regions.mob_knowledge.get(int(key))
    if mob['territory']!=0:self.assertNotIn(key,farms);removed+=1
    else:self.assertIn(key,farms)
  self.assertEqual(removed,22)
  self.assertEqual(self.regions.mob_knowledge.get(90)['territory'],1)
 def test_report28_level28_shortlist_has_only_real_ground_camps_and_coordinates(self):
  w,_=magic.MagicTests().make();w.own.values.update({0:28,31:1000})
  region=self.regions.get('garner');learning=HuntLearning('report28')
  chosen=learning.choose(region,w.own,100,position=(220000,270000))
  self.assertTrue(chosen)
  for model in chosen:
   self.assertEqual(self.regions.mob_knowledge.get(model)['territory'],0)
   self.assertTrue(region['farms'][str(model)]['points'])
  self.assertFalse({58,90,91,97}&chosen)
 def test_cached_held_sea_choice_is_not_retained(self):
  w,_=magic.MagicTests().make();w.own.values.update({0:26,31:1000})
  sea={'90':{'territory':1,'level':26,'hp':1,'points':[(0,0)]}}
  c=HuntLearning(1);c.selected={90}
  self.assertEqual(c.choose({'farms':sea},w.own,100,hold=True),set())
  self.assertEqual(c.admissible({'farms':sea},w.own,100),set())
 def test_land_filter_applies_to_visible_assist_targets(self):
  w,p=magic.MagicTests().make();p.mob_knowledge=self.regions.mob_knowledge
  e=copy.copy(next(e for e in w.entities.values() if e.identity!=w.own_id));e.model=90
  self.assertFalse(p.eligible(e,100,{90}))
 def test_report_shows_real_map_tile_coordinates(self):
  w,p=magic.MagicTests().make();p.region=self.regions.get('garner');p.mob_knowledge=self.regions.mob_knowledge
  p.planned_models=lambda:{136};p.local_hunting_region=lambda:p.region
  report=p.hunting_coordinates();self.assertEqual(report['sites'][0]['model'],136)
  for cm,tile in zip(report['sites'][0]['points_cm'],report['sites'][0]['coordinates']):
   self.assertEqual(tile,[round(cm[0]/100,2),round(cm[1]/100,2)])
  self.assertTrue(report['source_regions_not_live_monster_positions'])
 def test_changing_region_invalidates_same_level_cached_choice(self):
  w,_=magic.MagicTests().make();w.own.values.update({0:26,31:1000})
  c=HuntLearning(1);record={'territory':0,'level':26,'hp':10,'points':[(0,0)]}
  self.assertEqual(c.choose({'farms':{'1':record}},w.own,100),{1})
  self.assertEqual(c.choose({'farms':{'2':record}},w.own,101),{2})

class Repair61Tests(unittest.TestCase):
 def test_report31_unaffordable_preventive_repair_yields_without_visiting_or_paying(self):
  w,g,r,s,p=repair_examples.Repair53Tests().make();w.bag={};w.own.values.update({0:31,8:363})
  w.own.equipment={6:27};w.own.equipment_details={6:{'identity':27,'valid':True,'endurance':2994,'max_endurance':10000,'parameters':(0,0),'instance_attributes':(),'forge':0}}
  r.preventive=r.budget_preflight=True
  self.assertEqual(r.estimated_fee((1,6)),705)
  self.assertFalse(r.tick(100,p));s.assert_not_called();p.move_to.assert_not_called()
  self.assertEqual(r.summary()['estimated_funding_needed'],705);self.assertEqual(w.own.values[8],363)
 def test_native_insufficient_gold_refusal_ends_wait_and_defers_same_item(self):
  ex=repair_examples.Repair53Tests();w,g,r,s,p=ex.make();ex.open_quote(r,s,p)
  self.assertTrue(r.observe(517,string('Insufficient gold. Unable to repair'),5))
  self.assertFalse(r.busy);self.assertEqual(r.native_refusals,1);self.assertEqual(r.timeouts,0)
  self.assertFalse(r.tick(100,p));self.assertEqual(r.requests,1)
  w.own.values[8]+=1000;self.assertTrue(r.tick(101,p))
 def test_unrelated_notice_does_not_cancel_native_quote(self):
  ex=repair_examples.Repair53Tests();w,g,r,s,p=ex.make();ex.open_quote(r,s,p)
  self.assertFalse(r.observe(517,string('OWNER60_XP rate=14 scale=100'),5));self.assertTrue(r.busy)
 def test_quote_timeout_backoff_applies_across_other_merchants(self):
  ex=repair_examples.Repair53Tests();w,g,r,s,p=ex.make();ex.open_quote(r,s,p);r.tick(20,p)
  r.failed.clear();r.next_try=0;self.assertFalse(r.tick(30,p));self.assertEqual(r.requests,1)
 def test_item_disappearance_before_quote_timeout_preserves_native_bag_without_crashing(self):
  ex=repair_examples.Repair53Tests();w,g,r,s,p=ex.make();ex.open_quote(r,s,p)
  w.bag.pop(19);self.assertFalse(r.tick(20,p));self.assertFalse(r.busy)
  self.assertEqual(r.confirmed,0);self.assertNotIn(19,w.bag)

class Coral61Tests(unittest.TestCase):
 def make(self):
  from equipment import Equipment
  from unittest.mock import Mock
  w,p=magic.MagicTests().make();w.own.model=1;w.own.values.update({0:35,4:4})
  w.bag_ready=True;w.bag_capacity=48
  w.skills={214:{'level':8,'state':0,'energy':7}}
  w.own.equipment={5:4666,6:635,7:4611,8:872,9:82}
  w.own.equipment_details={k:dict(dataclasses.asdict(pets.item(i,energy=100 if i in (635,872) else 0)),identity=i) for k,i in w.own.equipment.items()}
  w.bag={0:pets.item(867,energy=100),25:pets.item(817,energy=100)}
  p.emit=Mock();return w,p,Equipment(w,magic.GEAR,Mock())
 def test_report13_equips_attack_coral_before_unlearned_support_coral(self):
  w,p,e=self.make();self.assertTrue(e.tick(100,p));self.assertEqual(e.pending[0],867)
  self.assertEqual(p.emit.call_args.args[0][-4:],struct.pack('>hh',0,-1))
 def test_unneeded_coral_cannot_flip_flop_with_necklace(self):
  w,p,e=self.make();w.own.required_coral_links={7}
  self.assertIsNone(magic.GEAR.upgrade(w.own,817,10,w.bag[25]))
 def test_ring_in_second_slot_preserves_attack_coral_and_needs_only_that_slot(self):
  w,p,e=self.make();w.own.equipment[7]=867;w.own.equipment_details[7]=dict(dataclasses.asdict(pets.item(867,energy=100)),identity=867)
  w.own.required_coral_links={7};w.own.equipment.pop(8);w.own.equipment_details.pop(8)
  change=magic.GEAR.transition(w.own,4611,10,pets.item(4611))
  self.assertIsNotNone(change);self.assertEqual(change[0][7],867);self.assertEqual(change[0][8],4611)
 def test_worn_noncoral_is_not_mistaken_for_empty_coral_charge(self):
  w,p,e=self.make();w.own.required_coral_links={7}
  # An unused support slot with a normal necklace has no coral energy.
  self.assertIsNone(magic.GEAR.upgrade(w.own,817,10,pets.item(817,energy=100)))

class Supplies61Tests(unittest.TestCase):
 def make(self):
  from test_mechanics import actor
  w=actor();w.map='garner';w.own.model=4;w.own.values.update({0:22,4:5,8:23449})
  w.own.equipment={2:381};w.own.equipment_details={};w.bag={14:pets.item(105),15:pets.item(360)}
  town=Town(w,magic.LIFE,magic.GEAR,{'first_job':5,'target_job':13},random.Random(1),w.own.position)
  portals=json.loads((ROOT/'assets/portals.json').read_text())
  return w,town,SimpleNamespace(travel=SimpleNamespace(portals=portals))
 def test_report16_missing_apples_does_not_block_remote_staff_procurement(self):
  w,t,p=self.make();plan=t.plan_supplies(100,p)
  self.assertEqual((plan['map'],plan['item']),('magicsea',97));self.assertTrue(plan['critical'])
 def test_xp_supply_scan_does_not_pick_optional_pet_books_instead_of_trip(self):
  w,t,p=self.make();w.own.equipment={9:97};w.bag={0:pets.item(1847,10),1:pets.item(4602)}
  w.skills={99:{'level':1,'state':1}};t.progression_visit=True
  t.hunt_travel=SimpleNamespace(plan={'kind':'ticket'},purchase_goals=lambda:[(3073,1,'hunt ticket')])
  # Base-game fixtures have no custom ticket seller; install its released
  # source-backed stock into this isolated fixture, never shared LIFE.
  t.life=copy.copy(t.life);t.life.prices=dict(t.life.prices);t.life.prices[3073]=5000
  shop={'key':'owner-ticket-test','position':list(w.own.position),'offers':[3073],'name':'Tickets'}
  t.npcs=SimpleNamespace(shops=lambda name:[shop] if name=='garner' else [])
  plan=t.plan_supplies(100,p)
  self.assertIsNotNone(plan);self.assertEqual(plan['item'],3073)
 def test_hunt_ticket_is_selected_before_optional_care_goals(self):
  w,t,p=self.make();w.own.equipment={9:97};w.bag={0:pets.item(1847,10),1:pets.item(4602)}
  w.skills={99:{'level':1,'state':1}};t.progression_visit=True
  t.hunt_travel=SimpleNamespace(plan={'kind':'ticket'},purchase_goals=lambda:[(3073,1,'hunt ticket')])
  self.assertEqual(t.choose_want(),(3073,1))

 def test_cancelled_hunt_ticket_releases_merchant_walk(self):
  import unittest.mock
  w,t,p=self.make();w.own.equipment={9:97}
  w.bag={0:pets.item(1847,10),1:pets.item(4602)}
  t.wanted=(3073,1);t.trip_purchase=True
  t.target_shop={'position':list(w.own.position)}
  t.hunt_travel=SimpleNamespace(plan=None,purchase_goals=lambda:[])
  t.plan_supplies=unittest.mock.Mock(return_value=None)
  t.choose_want=unittest.mock.Mock(return_value=None)
  p.move_to=unittest.mock.Mock()
  self.assertFalse(t.tick(100,p,True))
  self.assertIsNone(t.wanted)
  p.move_to.assert_not_called()

if __name__=='__main__':unittest.main()
