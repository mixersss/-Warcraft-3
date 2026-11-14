"""Expansion persistence, actual XP accounting and native two-hand transitions."""
import copy
import json
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from population_growth import PopulationGrowth,balanced_additions
from population import ALLOWED
from roles import RoleStore
from farm_plan import HuntLearning,FIELDS
from equipment import ItemCatalog,Equipment
from inventory import BagItem
import test_development as base
import test_alpha21 as learning_base
from fleet import Fleet


class GrowthTests(unittest.TestCase):
    def initial(self,d):
        d=Path(d)
        state={'version':1,'windows_sid':'synthetic','bots':[
            {'account':f'PB{i:012x}','character':f'Bot{i:08x}',
             'password_dpapi':f'cipher-{i}','secondary_password_dpapi':f'pin-{i}'} for i in range(200)]}
        # A compatible representative old200: 50champions and30ofeachother class.
        jobs=[8]*50+[9]*30+[12]*30+[13]*30+[14]*30+[16]*30
        records={r['character']:{'body':next(b for b in ALLOWED if job in ALLOWED[b]),'target_job':job}
                 for r,job in zip(state['bots'],jobs)}
        (d/'bot-local.json').write_text(json.dumps(state));RoleStore(d/'bot-roles.json').save_records(records)
        return state,records

    def extend(self,d,state,count=300):
        new=copy.deepcopy(state)
        for i in range(len(new['bots']),count):
            new['bots'].append({'account':f'PB{i:012x}','character':f'Bot{i:08x}',
                                'password_dpapi':f'cipher-{i}','secondary_password_dpapi':f'pin-{i}'})
        (Path(d)/'bot-local.json').write_text(json.dumps(new));return new

    def test_only100new_all_old_fields_and_roles_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            state,records=self.initial(d);g=PopulationGrowth(d);new=self.extend(d,state)
            bots=[dict(r) for r in new['bots']];g.assign(bots)
            self.assertTrue(all(r['preserve_existing'] for r in bots[:200]))
            self.assertTrue(all(not r['preserve_existing'] for r in bots[200:]))
            self.assertEqual(new['bots'][:200],state['bots'])
            saved=RoleStore(Path(d)/'bot-roles.json').read_records()
            self.assertEqual({k:saved[k] for k in records},records)
            self.assertEqual(Counter(r['target_job'] for r in saved.values()),{8:50,9:50,12:50,13:50,14:50,16:50})
            self.assertEqual(json.loads((Path(d)/'backups/before-growth-300/bot-local.json').read_text()),state)

    def test_resume_partial_no_new_plan_no_duplicate_identities(self):
        with tempfile.TemporaryDirectory() as d:
            state,_=self.initial(d);g=PopulationGrowth(d);plans=copy.deepcopy(g.ledger['plans'])
            self.extend(d,state,237);again=PopulationGrowth(d)
            self.assertEqual(again.ledger['plans'],plans)
            new=self.extend(d,state);bots=[dict(r) for r in new['bots']];again.assign(bots)
            again.confirm(201);again.confirm(201)
            resumed=PopulationGrowth(d);resumed.assign(bots)
            self.assertTrue(bots[200]['preserve_existing']);self.assertFalse(bots[201]['preserve_existing'])
            self.assertEqual(resumed.ledger['confirmed_indices'],[201])
            self.assertEqual(len({r['character'] for r in bots}),300)

    def test_complete_expansion_never_adds_another100(self):
        with tempfile.TemporaryDirectory() as d:
            state,_=self.initial(d);g=PopulationGrowth(d);new=self.extend(d,state)
            bots=[dict(r) for r in new['bots']];g.assign(bots)
            for i in range(201,301):g.confirm(i)
            again=PopulationGrowth(d);again.assign(bots)
            self.assertTrue(all(b['preserve_existing'] for b in bots));self.assertEqual(len(bots),300)

    def test_changed_old_credentials_refuse_before_creation(self):
        with tempfile.TemporaryDirectory() as d:
            state,_=self.initial(d);PopulationGrowth(d)
            state['bots'][0]['password_dpapi']='changed'
            (Path(d)/'bot-local.json').write_text(json.dumps(state))
            with self.assertRaises(RuntimeError):PopulationGrowth(d)

    def test_failed_confirmation_save_remains_retryable(self):
        with tempfile.TemporaryDirectory() as d:
            state,_=self.initial(d);g=PopulationGrowth(d);self.extend(d,state)
            with patch('population_growth.atomic_json',side_effect=OSError('synthetic write failure')):
                with self.assertRaises(OSError):g.confirm(201)
            self.assertTrue(g.permits_creation(201));g.confirm(201)
            self.assertFalse(PopulationGrowth(d).permits_creation(201))

    def test_existing300_without_ledger_are_all_protected(self):
        with tempfile.TemporaryDirectory() as d:
            state,_=self.initial(d);new=self.extend(d,state)
            g=PopulationGrowth(d);g.assign(new['bots'])
            self.assertEqual(g.existing_count,300)
            self.assertTrue(all(r['preserve_existing'] for r in new['bots']))
            self.assertFalse((Path(d)/'population-growth.json').exists())

    def test_missing_old_registry_does_not_invent_profiles(self):
        with tempfile.TemporaryDirectory() as d:
            self.initial(d);(Path(d)/'bot-roles.json').unlink()
            with self.assertRaises(RuntimeError):PopulationGrowth(d)
            self.assertFalse((Path(d)/'population-growth.json').exists())

    def test_partial_without_ledger_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            state,_=self.initial(d);self.extend(d,state,220)
            with self.assertRaises(RuntimeError):PopulationGrowth(d)

    def test_completed_new_role_rebalance_is_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            state,_=self.initial(d);g=PopulationGrowth(d);new=self.extend(d,state);g.assign(new['bots'])
            store=RoleStore(Path(d)/'bot-roles.json');records=store.read_records();name=new['bots'][200]['character']
            body=records[name]['body'];records[name]['target_job']=ALLOWED[body][-1];store.save_records(records)
            PopulationGrowth(d).assign(new['bots'])
            self.assertEqual(store.read_records()[name],records[name])

    def test_every_generated_profile_compatible_for_unbalanced_prefix(self):
        for body in ALLOWED:
            old={str(i):{'body':body,'target_job':ALLOWED[body][0]} for i in range(200)}
            before=copy.deepcopy(old);plans=balanced_additions(old,100)
            self.assertEqual(old,before);self.assertEqual(len(plans),100)
            self.assertTrue(all(p['target_job'] in ALLOWED[p['body']] for p in plans))

    def test_native_saved_character_refused_even_with_global_creation_request(self):
        from auto_bots import ensure_character
        from classic_wire import ProtocolError
        client=Mock()
        with self.assertRaises(ProtocolError):ensure_character({'character':'Bot00000000','preserve_existing':True},client,[])
        client.create_character.assert_not_called()


class LevelingTests(unittest.TestCase):
    def make(self):return learning_base.LearningTests().make()
    def test_cumulative_native_xp_crossing_level_is_not_lost(self):
        w,l,t=self.make();l.begin(w,t,100);w.own.values.update({0:11,15:70});l.finish(w,110,'win')
        self.assertEqual(l.rows['103']['xp'],60);self.assertEqual(l.rows['103']['level_ups'],1)
    def test_lower_xp_after_loss_never_fabricates_reward(self):
        w,l,t=self.make();l.begin(w,t,100);w.own.values.update({0:11,15:5});l.finish(w,110,'win')
        self.assertEqual(l.rows['103']['xp'],0)
    def test_session_actual_xp_per_minute_including_hold_and_loss(self):
        w,l,t=self.make();r={'farms':{'103':{'level':3,'hp':69,'points':[[0,0]],'drops':[]}}}
        l.choose(r,w.own,100);w.own.values[15]=130;l.choose(r,w.own,160,hold=True)
        self.assertEqual(l.summary()['session_xp_per_minute'],120)
        w.own.values[15]=110;l.choose(r,w.own,220,hold=True)
        self.assertEqual(l.summary()['session_xp_net'],100);self.assertEqual(l.summary()['session_xp_lost'],20)
    def test_xp_loss_does_not_reset_no_progress_clock(self):
        w,l,t=self.make();r={'farms':{'103':{'level':3,'hp':69,'points':[[0,0]],'drops':[]}}}
        l.choose(r,w.own,100);w.own.values[15]=5;l.choose(r,w.own,160)
        self.assertEqual(l.summary()['seconds_without_xp'],60)
    def test_same_completed_fight_cannot_start_endless_new_probes(self):
        w,l,t=self.make();l.rows['103']={k:0 for k in FIELDS};l.rows['103'].update(wins=1,seconds=10,xp=20)
        r={'farms':{str(i):{'level':10,'hp':20,'points':[[i*100,0]],'drops':[]} for i in range(100,108)}}
        l.choose(r,w.own,100,position=(0,0));self.assertTrue(l.probing)
        l.choose(r,w.own,176,position=(0,0));self.assertFalse(l.probing)
        self.assertEqual(len(l.probe_attempts),1)
    def test_probe_prefers_nearby_viable_camp(self):
        w,l,t=self.make();l.rows['103']={k:0 for k in FIELDS};l.rows['103'].update(wins=1)
        r={'farms':{'1':{'level':10,'hp':100,'points':[[100,0]],'drops':[]},
                    '2':{'level':10,'hp':10,'points':[[60000,0]],'drops':[]}}}
        self.assertEqual(l.choose(r,w.own,100,position=(0,0)),{1})
    def test_catalog_xp_uses_native_exp_and_preserves_locations(self):
        mobs=json.loads((ROOT/'assets/world-mobs.json').read_text())['monsters']
        self.assertEqual(mobs['103']['base_xp'],7);self.assertEqual(mobs['258']['base_xp'],80)
        self.assertEqual(len(mobs),608);self.assertEqual(sum(bool(v['locations']) for v in mobs.values()),426)
    def test_soft_rewarding_target_scores_above_armoured_dry_target(self):
        w,l,t=self.make();w.own.values.update({33:30,34:40})
        r={'farms':{'1':{'level':10,'hp':100,'base_xp':55,'defence':5,'points':[[100,0]],'drops':[]},
                    '2':{'level':10,'hp':100,'base_xp':0,'defence':100,'points':[[100,0]],'drops':[]}}}
        l.choose(r,w.own,100,position=(0,0));self.assertGreater(l.scores[1],l.scores[2])
    def test300_independent_learners_and_fleet_records(self):
        with tempfile.TemporaryDirectory() as d:
            fleet=Fleet(300,Path(d)/'population-status.json');w,_,_=self.make()
            r={'farms':{'103':{'level':3,'hp':69,'points':[[0,0]],'drops':[]}}}
            for i in range(1,301):
                l=HuntLearning(i);l.choose(r,w.own,100);l.choose(r,w.own,160)
                fleet.update(i,connected=True,level=10,job=1,xp_per_minute=l.summary()['session_xp_per_minute'])
            self.assertEqual(fleet.write()['connected'],300)

    def test_diagnostic_renders_actual_nested_learning_metrics(self):
        from show_diagnostics import render_report
        from show_levels import render
        text=render_report({'hunt':{'hunting_learning':{'session_xp_per_minute':42,'session_xp_net':84,'seconds_without_xp':5}}})
        self.assertIn('опыт/мин=42',text);self.assertIn('прирост=84',text)
        self.assertIn('42',render({'bots':{'1':{'xp_per_minute':42,'seconds_without_xp':5}}}))


class LoadoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.catalog=ItemCatalog(ROOT/'assets/items.json')
    def world(self):
        w=base.scene();w.own.values.update({0:15,4:1});w.own.model=1;w.bag_ready=True;w.bag_capacity=24
        w.own.equipment={9:1};w.bag={0:BagItem(1,1,20,20,0,0,0,True)};return w
    def test_second_identical_sword_uses_empty_left_hand_and_waits_for_that_hand(self):
        w=self.world();p=SimpleNamespace(emit=Mock(),sequence=1);e=Equipment(w,self.catalog,Mock())
        self.assertTrue(e.tick(100,p));self.assertEqual(e.pending[1],[6]);e.tick(101,p)
        self.assertEqual(e.confirmed,0) # The identical right sword is not an acknowledgment.
        w.own.equipment[6]=1;e.tick(102,p);self.assertEqual(e.confirmed,1)
    def test_known_twohand_marker_does_not_block_real_upgrade(self):
        w=self.world();w.own.equipment={9:8,6:9999}
        self.assertIsNotNone(self.catalog.upgrade(w.own,1,20))
    def test_unknown_marker_partner_remains_protected(self):
        w=self.world();w.own.equipment={9:55555,6:9999}
        self.assertIsNone(self.catalog.upgrade(w.own,1,20))
    def test_pair_plan_can_cross_temporarily_weaker_first_sword(self):
        w=self.world();catalog=copy.deepcopy(self.catalog)
        catalog.gear[8]['score']=100;catalog.gear[1]['score']=60
        w.own.equipment={9:8,6:9999};w.bag[1]=w.bag[0]
        self.assertIsNone(catalog.upgrade(w.own,1,20))
        plan=catalog.pair_upgrade(w,{},100);self.assertEqual(plan[0],20)
        w.own.equipment={9:1};w.bag.pop(plan[1])
        self.assertEqual(catalog.upgrade(w.own,1,20),(60,[6]))
    def test_stronger_twohand_is_kept_instead_of_weaker_pair(self):
        w=self.world();catalog=copy.deepcopy(self.catalog);catalog.gear[8]['score']=200
        w.own.equipment={9:8,6:9999};w.bag[1]=w.bag[0]
        self.assertIsNone(catalog.pair_upgrade(w,{},100))
    def test_twohand_compares_against_both_swords(self):
        w=self.world();w.own.equipment={9:1,6:1}
        self.assertIsNone(self.catalog.upgrade(w.own,8,20))
    def test_full_bag_and_wrong_job_cannot_start_pair_plan(self):
        w=self.world();w.own.equipment={9:8,6:9999};w.bag[1]=w.bag[0];w.bag_capacity=2
        self.assertIsNone(self.catalog.pair_upgrade(w,{},100))
        w.bag_capacity=24;w.own.values[4]=2;self.assertIsNone(self.catalog.pair_upgrade(w,{},100))
