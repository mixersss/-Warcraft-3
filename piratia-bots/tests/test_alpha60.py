"""Blocked weapons, paid-ticket planning and numeric native XP evidence."""
import random
import sys
import unittest
import copy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from xp_diagnostics import XPDiagnostics
from classic_wire import string
from town import Town
from coordination import Coordination
import test_alpha26 as scheduling
import test_alpha42 as magic

class Supply60Tests(unittest.TestCase):
 def test_report278_race_level_gold_can_find_and_equip_real_remote_staff(self):
  from test_mechanics import actor
  from test_pet_economy import item
  w=actor();w.map='garner';w.own.model=4;w.own.values.update({0:13,4:5,8:4133})
  w.own.equipment={9:9,6:9999};w.own.equipment_details={9:{'identity':9,'valid':True,'endurance':9996,'max_endurance':10000}}
  w.bag={0:item(1847,6),1:item(4602),2:item(4603),3:item(4604)}
  town=Town(w,magic.LIFE,magic.GEAR,{'first_job':5,'target_job':13},random.Random(1),w.own.position)
  import json
  policy=SimpleNamespace(travel=SimpleNamespace(portals=json.loads((ROOT/'assets/portals.json').read_text())))
  plan=town.plan_supplies(100,policy)
  self.assertEqual((plan['map'],plan['item'],plan['critical'],plan['price']),('magicsea',97,True,1218))
  self.assertIsNotNone(magic.GEAR.upgrade(w.own,97,30,item(97)))
  self.assertEqual(w.own.values[8],4133);self.assertEqual(w.own.equipment[9],9)
 def test_missing_staff_allows_supplier_work_during_emergency_xp_phase(self):
  w,p,q=scheduling.ProfessionSchedulingTests().policy();w.own.values.update({0:13,4:5,8:4133})
  w.own.equipment={9:9};w.skills={99:{'level':3,'state':0}};w.bag={};w.bag_ready=True
  p.adventure=None;p.target=None;p.activity=SimpleNamespace(hunting=lambda now:True)
  p.economy=None;p.petcare=None
  town=Town(w,magic.LIFE,magic.GEAR,{'first_job':5,'target_job':13},random.Random(1),w.own.position)
  # No current-map offer is required to permit discovery of the remote staff.
  town.critical_items=lambda *a:[];town.combat_items=set();p.clock=100
  self.assertTrue(town.combat_supply_required())
  callback=Mock(return_value=True);self.assertTrue(p.task('town',town,callback,100));callback.assert_called_once()
 def test_working_staff_releases_optional_supplier_priority(self):
  w,p=magic.MagicTests().make();town=Town(w,magic.LIFE,magic.GEAR,None,random.Random(1),w.own.position)
  self.assertFalse(town.combat_supply_required())
 def test_wrong_weapon_explains_server_inactive_skill_without_forcing_activation(self):
  w,p=magic.MagicTests().make();w.own.equipment={9:9};w.skills[99]['state']=0
  self.assertIsNone(p.combat_skills.select(100));self.assertEqual(p.combat_skills.reason,'не выполнено требование оружия')
  self.assertEqual(w.skills[99]['state'],0)

class Evidence60Tests(unittest.TestCase):
 def test_read_only_native_zero_scale_is_distinguished_from_zero_activity(self):
  c=XPDiagnostics();line='OWNER60_XP rate=14 scale=0 base=120 before=438284 after=438284 monster=85 ok=1'
  self.assertTrue(c.observe(517,string(line)));r=c.summary()
  self.assertTrue(r['fatigue_zero_observed']);self.assertEqual(r['recent'][0]['native_xp_delta'],0)
  self.assertTrue(r['no_direct_experience_grants'])
 def test_native_increase_and_errors_are_separate(self):
  c=XPDiagnostics()
  self.assertTrue(c.observe(517,string('OWNER60_XP rate=14 scale=100 base=120 before=10 after=1690 monster=85 ok=1')))
  self.assertEqual(c.summary()['recent'][0]['native_xp_delta'],1680)
  self.assertTrue(c.observe(517,string('OWNER60_XP rate=14 scale=100 base=120 before=1690 after=1690 monster=85 ok=0')))
  self.assertTrue(c.summary()['native_error_observed'])
 def test_unrelated_or_malformed_notices_do_not_crash_or_save_chat(self):
  c=XPDiagnostics()
  for b in (b'\0',b'',string('ordinary message'),string('OWNER60_XP rate=.. scale=0 base=1 before=0 after=0 monster=85 ok=1')):
   self.assertFalse(c.observe(517,b))
  self.assertEqual(c.summary()['receipts'],0)
 def test_telemetry_is_bounded(self):
  c=XPDiagnostics()
  for i in range(50):c.observe(517,string('OWNER60_XP rate=14 scale=100 base=1 before=0 after=1 monster=85 ok=1'))
  self.assertEqual(len(c.summary()['recent']),12)
 def test_raw_fatigue_and_effective_scale_are_not_confused(self):
  c=XPDiagnostics();c.observe(517,string('OWNER60_XP rate=14 scale=0 base=120 before=10 after=1690 monster=85 ok=1 effective=100'))
  r=c.summary()['recent'][0];self.assertEqual((r['scale'],r['effective_scale'],r['native_xp_delta']),(0,100,1680))

class Coordination60Tests(unittest.TestCase):
 def test_huge_goal_list_uses_nearby_real_goals_and_keeps_lease(self):
  c=Coordination(400);goals=[(i*1000,0) for i in range(2000)]
  first=c.choose_zone('one','garner',goals,100,(0,0));self.assertIn(first,goals[:24])
  self.assertEqual(c.choose_zone('one','garner',list(reversed(goals)),101,(0,0)),first)
 def test_no_imaginary_goal_created_to_avoid_crowding(self):
  c=Coordination(400);goals=[(0,0),(1000,0)]
  for n in range(400):self.assertIn(c.choose_zone(str(n),'garner',goals,100,(0,0)),goals)

class Scouting60Tests(unittest.TestCase):
 def test_actual_wolf_rectangle_gets_multiple_dry_legal_search_points(self):
  import json
  from navigation import Navigation
  from mob_knowledge import MobKnowledge
  from farm_scouting import scout_points
  r=json.loads((ROOT/'assets/regions.json').read_text())['garner']
  nav=Navigation(ROOT/'assets'/r['navigation']);m=MobKnowledge(ROOT/'assets/world-mobs.json')
  areas=m.by_map['garner'][136];points=scout_points(nav,areas,r['farms']['136']['points'])
  self.assertGreater(len(points),20);self.assertLessEqual(len(points),97)
  for p in points:
   self.assertTrue(nav.free(nav.cell(p)));self.assertTrue(nav.combat_allowed(p))
   self.assertTrue(any(a['rectangle_cm'][0][0]<=p[0]<=a['rectangle_cm'][1][0] and a['rectangle_cm'][0][1]<=p[1]<=a['rectangle_cm'][1][1] for a in areas))
 def test_conditional_spawns_are_not_invented_as_active_targets(self):
  from farm_scouting import scout_points
  nav=SimpleNamespace(nearest=lambda p,r:p,combat_allowed=lambda p:True)
  self.assertEqual(scout_points(nav,[{'rectangle_cm':[[0,0],[5000,5000]],'conditions_not_evaluated':True}],[]),[])

class Care60Tests(unittest.TestCase):
 def test_ready_owned_fairy_has_only_its_chosen_fruit_in_purchase_goals(self):
  import test_pet_economy as pets
  w,c,p=pets.FairyTests().make();c.life=copy.copy(c.life)
  c.life.owner_shops={'catalog_revision':60,'fresh_fairies':True};c.maintenance_only=False;c.progression_first=True
  w.bag={1:pets.item(232),2:pets.item(2312,6)}
  fruits={i for i,n,r in c.purchase_goals() if i in pets.FRUITS.values()}
  self.assertEqual(fruits,{pets.FRUITS[c.stat]})
 def test_first_pet_does_not_override_xp_but_feeding_owned_pet_still_does(self):
  import test_pet_economy as pets
  w,c,p=pets.FairyTests().make();c.life=copy.copy(c.life)
  c.life.owner_shops={'catalog_revision':60,'fresh_fairies':True};c.progression_first=True
  c.life.prices=dict(c.life.prices);c.life.prices[2312]=1000
  self.assertFalse(c.affordable_care())
  w.bag={1:pets.item(232,endurance=49)}
  self.assertTrue(c.needs_food_visit());self.assertTrue(c.affordable_care())
 def test_primary_worn_bow_is_repaired_before_twenty_percent(self):
  import test_alpha53 as examples
  w,g,r,s,p=examples.Repair53Tests().make();w.bag={};w.own.values[0]=34
  w.own.equipment={6:27,9:9999};w.own.equipment_details={6:{'identity':27,'valid':True,'endurance':2499,'max_endurance':10000,'parameters':(0,0),'instance_attributes':(),'forge':0}}
  self.assertEqual(r.candidates(),[]);r.preventive=True;self.assertEqual(r.candidates(),[(1,6)])
 def test_repair_walk_times_out_without_fake_purchase_or_repair(self):
  import test_alpha53 as examples
  w,g,r,s,p=examples.Repair53Tests().make()
  # The NPC is far away; an accepted movement request is not arrival.
  w.entities[3].x+=10000;p.move_to.return_value=True
  p.nav.nearest.side_effect=lambda pt,radius:pt
  self.assertTrue(r.tick(100,p));self.assertFalse(r.tick(220,p))
  self.assertEqual(r.approach_timeouts,1);self.assertEqual(r.confirmed,0);s.assert_not_called()

if __name__=='__main__':unittest.main()
