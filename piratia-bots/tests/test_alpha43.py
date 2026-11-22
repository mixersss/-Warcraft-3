"""Every supplied NPC placement, useful shopping plans and eight earned-stat builds."""
import copy,json,random,struct,sys,tempfile,unittest
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from npc_knowledge import NpcKnowledge
from builds import BuildStore,PROFILES,observed_speed
from progression import Progression
from equipment import ItemCatalog
from life import LifeItems
from inventory import BagItem
from town import Town
from city_travel import CityTravel
from social import Social,ChatBudget
from classic_wire import ProtocolError
import test_development as base
GEAR=ItemCatalog(ROOT/'assets/items.json');LIFE=LifeItems(ROOT/'assets');NPC=LIFE.npcs

class KnowledgeTests(unittest.TestCase):
    def test_every_real_table_and_placement_included_without_stale_copy(self):
        d=json.loads((ROOT/'assets/world-npcs.json').read_text())
        self.assertEqual(len(NPC.rows),521);self.assertEqual(len(NPC.by_map),20);self.assertEqual(NPC.table_count,29)
        self.assertEqual(len(NPC.by_map['magicsea']),96);self.assertEqual(len(NPC.by_map['garner']),152)
        self.assertEqual(d['excluded_stale_script_table_copies'],['script/magicsea/magicseanpc.txt'])
        self.assertEqual(d['unresolved_functions'],[])
        self.assertEqual(len(NPC.by_key),521)
    def test_unknown_coordinates_are_not_fabricated(self):
        self.assertEqual(len(NPC.unlocated),30);self.assertEqual(NPC.model_count,131)
        placed={n['model'] for n in NPC.rows};self.assertTrue(placed.isdisjoint(NPC.unlocated))
        self.assertFalse(NPC.summary('garner',(223000,278000))['dynamic_spawns_exhaustively_known'])
    def test_all_services_are_searchable_and_live_confirmation_is_explicit(self):
        for service in ('банк','ремонт','телепорт','корабль','квест','кольца'):
            self.assertTrue(NPC.find(service),service)
        self.assertTrue(NPC.summary('garner',(223000,278000))['live_menu_required'])
    def test_staff_bow_and_ring_shops_have_correct_maps(self):
        self.assertTrue(any(n['map']=='magicsea' and 'Smithy' in n['name'] for n in NPC.find('посох')))
        self.assertTrue(any(n['map']=='darkblue' and 'Bash' in n['name'] for n in NPC.find('лук')))
        self.assertTrue(any(n['map']=='garner' for n in NPC.find('кольца')))
        self.assertEqual(len(NPC.shops()),44)
    def test_no_trade_callback_is_invented_for_bank_only_actor(self):
        bank=next(n for n in NPC.find('банк') if not n['offers'])
        self.assertFalse(bank['verified_shop_binding']);self.assertNotIn(bank,NPC.shops())
    def test_find_public_npc_name_and_item_id_without_private_data(self):
        self.assertTrue(NPC.find('Smithy'));self.assertTrue(NPC.find('97'))
        self.assertTrue(all(97 in n['offers'] for n in NPC.sellers(97)))
        from show_npcs import render
        self.assertIn('Smithy',render(NPC,'97'))
    def test_bot_answers_from_shared_knowledge_instead_of_generic_own_location(self):
        w=base.scene();social=Social(w,Mock(),'Bot00000001',ChatBudget(),1)
        social.npc_provider=lambda words:NPC.answer(words,w.map,w.own.position)
        kind,text=social.reply(['где','купить','лук'])
        self.assertEqual(kind,'npc');self.assertIn('Bash',text);self.assertIn('Ледынь',text)
        self.assertLessEqual(len(text.encode('cp1251')),120)
    def test_source_comment_removal_preserves_quotes_and_excludes_disabled_items(self):
        sys.path.insert(0,str(ROOT/'tools'))
        from build_npc_knowledge import uncomment
        text=uncomment('Text(1,"Shop -- open",BuyPage) -- Weapon(999)\n--[[ Other(888) ]]\nWeapon(97)')
        self.assertIn('Shop -- open',text);self.assertNotIn('999',text);self.assertNotIn('888',text)

class ShoppingTests(unittest.TestCase):
    def make(self,job=5,body=3):
        w=base.scene();w.own.model=body;w.own.values.update({0:15,4:job,8:5000,7:0})
        w.own.equipment={9:8};w.bag_ready=True;w.bag_capacity=24
        w.bag={0:BagItem(1847,10,0,0,0,0,0,True)}
        t=Town(w,LIFE,GEAR,{'first_job':job,'target_job':13},random.Random(1),w.own.position)
        p=SimpleNamespace(travel=SimpleNamespace(portals=json.loads((ROOT/'assets/portals.json').read_text())))
        return w,t,p
    def test_mage_in_argent_plans_staff_at_shaitan_seller(self):
        w,t,p=self.make();plan=t.plan_supplies(100,p)
        self.assertIsNotNone(plan);self.assertEqual(plan['map'],'magicsea');self.assertEqual(GEAR.types[plan['item']],9)
        self.assertIn('Smithy',plan['shop']['name']);self.assertEqual(plan['reserved_travel_gold'],1000)
        self.assertEqual(w.own.equipment,{9:8});self.assertEqual(w.own.values[8],5000)
    def test_archer_in_argent_knows_bash_and_plans_real_bow(self):
        w,t,p=self.make(2,1);plan=t.plan_supplies(100,p)
        self.assertEqual(plan['map'],'darkblue');self.assertIn('Bash',plan['shop']['name'])
        self.assertEqual(GEAR.types[plan['item']],3)
    def test_no_route_or_insufficient_roundtrip_budget_does_not_start_remote_trip(self):
        w,t,p=self.make();w.own.values[8]=500
        plan=t.plan_supplies(100,p)
        self.assertTrue(plan is None or plan['map']==w.map)
        w,t,p=self.make();p.travel.portals=None;plan=t.plan_supplies(100,p)
        self.assertTrue(plan is None or plan['map']==w.map)
    def test_missing_food_keeps_medical_supply_priority(self):
        w,t,p=self.make();w.own.equipment={9:97};w.bag.clear();self.assertIsNone(t.plan_supplies(100,p))
        self.assertEqual(t.choose_want()[0],1847)
    def test_rings_become_explicit_goal_for_empty_appropriate_slots(self):
        w,t,p=self.make(1,1);w.own.values.update({0:30,8:200000});w.own.equipment={9:1}
        w.bag[47]=BagItem(4602,1,0,0,0,0,0,True) # Emergency ticket already stocked.
        plan=t.plan_supplies(100,p)
        self.assertIn(GEAR.types[plan['item']],(25,26));self.assertEqual(plan['reason'],'заполняет слот украшения')
    def test_decorations_cannot_replace_required_coral_even_if_more_expensive(self):
        w,t,p=self.make(4,1);w.own.values[0]=80;w.own.equipment={5:817,6:635,7:867,8:281,9:73}
        for identity,g in GEAR.gear.items():
            if g['kind'] in (25,26) and GEAR.compatible(w.own,identity):
                change=GEAR.transition(w.own,identity,20)
                if change:self.assertEqual({k:change[0].get(k) for k in (5,6,7)},{k:w.own.equipment[k] for k in (5,6,7)})
    def test_shopping_destination_cannot_override_novice_profession_or_advanced_quest(self):
        w,t,p=self.make();t.supply_plan=t.plan_supplies(100,p);p.town=t;p.career=None
        travel=CityTravel(w,Mock(),1,{'first_job':5});self.assertEqual(travel.destination(p),'magicsea')
        w.own.values[4]=0;travel.role={'first_job':2};self.assertEqual(travel.destination(p),'darkblue')
    def test_map_arrival_retains_purchase_then_death_clears_it(self):
        w,t,p=self.make();plan=t.plan_supplies(100,p);t.supply_plan=plan
        w.map=plan['map'];t.on_map(110);self.assertEqual(t.supply_plan,plan);self.assertEqual(t.next_shop,110)
        t.on_map(120,True);self.assertIsNone(t.supply_plan)
    def test_refused_supplier_is_temporarily_skipped(self):
        w,t,p=self.make();t.supply_plan=t.plan_supplies(100,p);key=t.supply_plan['shop']['key']
        t.finish(110,300);self.assertGreater(t.failed_suppliers[key],110)
        plan=t.plan_supplies(200,p);self.assertTrue(plan is None or plan['shop']['key']!=key)

class BuildTests(unittest.TestCase):
    def actor(self,build):
        spec=PROFILES[build];job=spec['job'];first={8:1,9:1,12:2,13:5,14:5,16:4}[job]
        w=base.scene();w.own.model={8:2,9:1,12:3,13:4,14:4,16:1}[job]
        w.own.values.update({4:first,0:20,25:10,26:10,27:10,28:10,29:10,6:1})
        send=Mock();p=Progression(w,send,first);p.target_job=job;p.build_id=build
        return w,p,send
    def test_all_eight_builds_use_only_owner_requested_attributes(self):
        self.assertEqual(len(PROFILES),8)
        expected={'crusader_speed':{25,27},'sharpshooter_precision':{26},'sharpshooter_speed':{26,27},
                  'cleric_spirit':{29},'sealmaster_balanced':{28,29},'voyager_spirit':{28,29},
                  'voyager_tank':{28,29},'champion_tank':{25,28}}
        for build,allowed in expected.items():
            self.assertEqual(set(PROFILES[build]['weights']),allowed)
            w,p,send=self.actor(build);before=dict(w.own.values);p.tick(100,True)
            attribute=struct.unpack('>H',send.call_args.args[1][1:3])[0]
            self.assertIn(attribute,allowed);self.assertEqual(w.own.values,before)
    def test_primary_first_point_matches_every_build(self):
        for build,attribute in [('crusader_speed',27),('sharpshooter_precision',26),('sharpshooter_speed',27),
             ('cleric_spirit',29),('sealmaster_balanced',29),('voyager_spirit',29),('voyager_tank',28),('champion_tank',28)]:
            w,p,send=self.actor(build);p.tick(100,True)
            self.assertEqual(struct.unpack('>H',send.call_args.args[1][1:3])[0],attribute,build)
    def test_sustained_allocation_keeps_weights_and_excludes_unrequested_stats(self):
        for build,spec in PROFILES.items():
            w,p,send=self.actor(build);before={k:w.own.values[k] for k in range(25,30)}
            for n in range(120):
                w.own.values[6]=1;p.tick(100+n*4,True)
                attr=struct.unpack('>H',send.call_args.args[1][1:3])[0]
                w.own.values[attr]+=1;w.own.values[6]=0;p.tick(101+n*4,True)
            self.assertEqual(p.confirmed,120)
            for attr in set(before)-set(spec['weights']):self.assertEqual(w.own.values[attr],before[attr],build)
            ratios=[w.own.values[k]/weight for k,weight in spec['weights'].items()]
            self.assertLessEqual(max(ratios)-min(ratios),1,build)
    def test_real_attack_interval210_threshold_then_strength_without_stat_reset(self):
        w,p,send=self.actor('crusader_speed');w.own.values[42]=500
        self.assertEqual(observed_speed(w.own.values),200);p.tick(100,True)
        self.assertEqual(struct.unpack('>H',send.call_args.args[1][1:3])[0],27)
        w,p,send=self.actor('crusader_speed');w.own.values[42]=476;before=dict(w.own.values);p.tick(100,True)
        self.assertGreaterEqual(observed_speed(w.own.values),210)
        self.assertEqual(struct.unpack('>H',send.call_args.args[1][1:3])[0],25);self.assertEqual(w.own.values,before)
    def test_two_variants_are_balanced_and_stable_across_restart(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'bot-builds.json';s=BuildStore(path)
            for job in (12,16):
                selected=[s.resolve('synthetic-'+str(job)+'-'+str(i),job) for i in range(100)]
                self.assertEqual(sorted(Counter(selected).values()),[50,50])
                self.assertEqual([BuildStore(path).resolve('synthetic-'+str(job)+'-'+str(i),job) for i in range(100)],selected)
            text=path.read_text();self.assertNotIn('synthetic',text);self.assertNotIn('password',text)
    def test_saved_build_class_change_requires_verified_novice_path(self):
        with tempfile.TemporaryDirectory() as d:
            s=BuildStore(Path(d)/'bot-builds.json');s.resolve('synthetic',12)
            with self.assertRaises(ProtocolError):s.resolve('synthetic',14)
            self.assertEqual(s.resolve('synthetic',14,True),'sealmaster_balanced')
    def test_zero_points_and_missing_native_confirmation_never_count_as_spent(self):
        w,p,send=self.actor('cleric_spirit');w.own.values[6]=0;p.tick(100,True);send.assert_not_called()
        w.own.values[6]=1;p.tick(101,True);self.assertEqual(p.confirmed,0)
        w.own.values[29]+=1;p.tick(102,True);self.assertEqual(p.confirmed,0)
        w.own.values[6]=0;p.tick(103,True);self.assertEqual(p.confirmed,1)


class HuntTierTests(unittest.TestCase):
    def make(self):
        from farm_plan import HuntLearning,PROFILES as HUNT_PROFILES
        w=base.scene();w.own.values.update({0:20,4:1,31:700,1:700})
        learning=HuntLearning('level20');learning.profile=HUNT_PROFILES[1]
        region={'farms':{'258':{'level':12,'hp':168,'base_xp':80,'points':[[0,0]],'drops':[]},
                         '227':{'level':16,'hp':240,'base_xp':152,'points':[[1000,0]],'drops':[]},
                         '999':{'level':20,'hp':450,'base_xp':250,'points':[[2000,0]],'drops':[]}}}
        return w,learning,region
    def test_native_level_divisor_matches_owner_script(self):
        from farm_plan import xp_level_divisor
        self.assertEqual(xp_level_divisor(20,12),2.6)
        self.assertEqual(xp_level_divisor(20,17),1)
        self.assertEqual(xp_level_divisor(20,16),1)
        self.assertEqual(xp_level_divisor(20,15),1.4)
        self.assertEqual(xp_level_divisor(10,20),3)
    def test_level20_stops_routine_bear12_farm_when_viable_higher_band_exists(self):
        w,l,r=self.make();models=l.choose(r,w.own,100,position=(0,0))
        self.assertNotIn(258,models);self.assertNotIn(258,l.admissible(r,w.own,100));self.assertTrue(models)
    def test_safe_low_level_fallback_remains_when_high_tier_is_unsafe(self):
        w,l,r=self.make();r['farms']['999']['hp']=99999;r['farms']['227']['hp']=99999
        self.assertIn(258,l.choose(r,w.own,100));self.assertIn(258,l.admissible(r,w.own,100))
    def test_old_level12_high_xp_history_cannot_pin_level20_to_bears(self):
        from farm_plan import FIELDS
        w,l,r=self.make();l.rows['258']={k:0 for k in FIELDS}
        l.rows['258'].update(wins=300,xp=999999,seconds=1,observed_level=12,level_wins=300,level_xp=999999,level_seconds=1)
        self.assertNotIn(258,l.choose(r,w.own,100))
    def test_current_level_reward_bucket_resets_without_deleting_lifetime_history(self):
        from farm_plan import HuntLearning
        from world import Entity
        w=base.scene();w.own.values.update({0:10,15:100})
        target=Entity(258,88,188,5,1,0,0,40,{0:12,1:168,31:168})
        l=HuntLearning('bucket');l.begin(w,target,100);w.own.values[15]=120;l.finish(w,110,'win')
        w.own.values[0]=11;l.begin(w,target,120);w.own.values[15]=150;l.finish(w,130,'win')
        self.assertEqual(l.rows['258']['xp'],50);self.assertEqual(l.rows['258']['level_xp'],30)
        self.assertEqual(l.rows['258']['observed_level'],11)
    def test_real_quest_can_still_require_lower_level_monster_and_report_why(self):
        import test_alpha21 as plans
        w,p=plans.PlanIntegrationTests().make();w.own.values.update({0:20,4:1});p.clock=100
        p.story=SimpleNamespace(desired_models=lambda:{258});p.activity.force_until=0
        self.assertEqual(p.planned_models(),{258});self.assertEqual(p.farm_reason()['source'],'story_quest')
        p.activity.force_until=200
        self.assertEqual(p.farm_reason()['source'],'adaptive_xp_hunt')
