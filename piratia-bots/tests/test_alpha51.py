"""Saved300->400 preservation/resume and server-constrained per-build skill plans."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from population_growth import PopulationGrowth
from roles import RoleStore,FIRST_JOB
from population import ALLOWED
from builds import PROFILES
from life import LifeItems
from skill_plan import SkillPlan,validate_guides
import test_alpha41 as oldgrowth
import test_development as development
from inventory import BagItem
from unittest.mock import Mock

class Expansion400Tests(unittest.TestCase):
    def initial(self,d,old_ledger=False):
        state,roles=oldgrowth.GrowthTests().initial(d)
        if old_ledger:
            growth=PopulationGrowth(d);state=oldgrowth.GrowthTests().extend(d,state)
            growth.assign(state['bots'])
            for i in range(201,301):growth.confirm(i)
            state=json.loads((Path(d)/'bot-local.json').read_text())
        else:
            state=oldgrowth.GrowthTests().extend(d,state)
            records=RoleStore(Path(d)/'bot-roles.json').read_records()
            for i in range(200,300):records[state['bots'][i]['character']]={'body':1,'target_job':9}
            RoleStore(Path(d)/'bot-roles.json').save_records(records)
        return state
    def extend(self,d,state,count=400):return oldgrowth.GrowthTests().extend(d,state,count)
    def test_only100added_old300_fields_roles_and_backups_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            state=self.initial(d);before=copy.deepcopy(state);oldroles=RoleStore(Path(d)/'bot-roles.json').read_records()
            g=PopulationGrowth(d,400);new=self.extend(d,state);g.assign(new['bots'])
            self.assertEqual(g.existing_count,300);self.assertTrue(all(b['preserve_existing'] for b in new['bots'][:300]));self.assertTrue(all(not b['preserve_existing'] for b in new['bots'][300:]))
            after=RoleStore(Path(d)/'bot-roles.json').read_records();self.assertEqual({k:after[k] for k in oldroles},oldroles)
            disk=json.loads((Path(d)/'bot-local.json').read_text());self.assertEqual(disk['bots'][:300],before['bots'])
            self.assertEqual(json.loads((Path(d)/'backups/before-growth-400/bot-local.json').read_text()),before)
            self.assertTrue(all(r['target_job'] in ALLOWED[r['body']] for r in after.values()))
            counts={j:sum(r['target_job']==j for r in after.values()) for j in (8,9,12,13,14,16)}
            self.assertLessEqual(max(v for j,v in counts.items() if j!=9)-min(counts.values()),1)
    def test_previous_completed_ledger_stays_byte_identical(self):
        with tempfile.TemporaryDirectory() as d:
            state=self.initial(d,True);p=Path(d)/'population-growth.json';original=p.read_bytes()
            g=PopulationGrowth(d,400);new=self.extend(d,state);g.assign(new['bots']);g.confirm(301)
            self.assertEqual(p.read_bytes(),original)
            self.assertEqual(json.loads((Path(d)/'population-growth-400.json').read_text())['confirmed_indices'],[301])
    def test_unfinished_previous_expansion_refuses_without_mutating(self):
        with tempfile.TemporaryDirectory() as d:
            state,_=oldgrowth.GrowthTests().initial(d);g=PopulationGrowth(d);self.extend(d,state,300)
            before={p.name:p.read_bytes() for p in Path(d).glob('*.json')}
            with self.assertRaises(RuntimeError):PopulationGrowth(d,400)
            self.assertEqual(before,{p.name:p.read_bytes() for p in Path(d).glob('*.json')})
    def test_partial_resume_and_confirmation_are_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            state=self.initial(d);g=PopulationGrowth(d,400);plans=copy.deepcopy(g.ledger['plans']);self.extend(d,state,347)
            resumed=PopulationGrowth(d,400);self.assertEqual(resumed.ledger['plans'],plans)
            new=self.extend(d,state);resumed.assign(new['bots']);resumed.confirm(301);resumed.confirm(301)
            again=PopulationGrowth(d,400);again.assign(new['bots']);self.assertTrue(new['bots'][300]['preserve_existing']);self.assertFalse(new['bots'][301]['preserve_existing'])
            for i in range(302,401):again.confirm(i)
            final=PopulationGrowth(d,400);final.assign(new['bots']);self.assertTrue(all(b['preserve_existing'] for b in new['bots']));self.assertEqual(len({b['character'] for b in new['bots']}),400)
    def test_missing_ledger_mid_extension_never_creates(self):
        with tempfile.TemporaryDirectory() as d:
            state=self.initial(d);self.extend(d,state,333)
            with self.assertRaises(RuntimeError):PopulationGrowth(d,400)
    def test_changed_old_prefix_and_bad_target_refused(self):
        with tempfile.TemporaryDirectory() as d:
            state=self.initial(d);PopulationGrowth(d,400);state['bots'][299]['password_dpapi']='changed';(Path(d)/'bot-local.json').write_text(json.dumps(state))
            with self.assertRaises(RuntimeError):PopulationGrowth(d,400)
            for target in (500,399,True):
                with self.assertRaises(ValueError):PopulationGrowth(d,target)
    def test_complete400_without_journal_protected(self):
        with tempfile.TemporaryDirectory() as d:
            state=self.initial(d);new=self.extend(d,state);g=PopulationGrowth(d,400);g.assign(new['bots']);self.assertEqual(g.existing_count,400);self.assertTrue(all(b['preserve_existing'] for b in new['bots']))

class GuideSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.life=LifeItems(ROOT/'assets')
    def make(self,key,job=None):
        profile=PROFILES[key];w=development.scene();w.own.build_id=key;w.own.values.update({0:60,4:job or profile['job'],7:100});w.skills={};w.bag={};w.bag_ready=True
        role={'target_job':profile['job'],'first_job':FIRST_JOB[profile['job']]};return w,SkillPlan(w,role,self.life)
    def test_all_eight_guides_converge_through_actual_prerequisites(self):
        for key,p in PROFILES.items():
            with self.subTest(key=key):
                w,plan=self.make(key);before=copy.deepcopy(w.own.values);steps_taken=0
                while plan.next_steps():
                    step=plan.next_steps()[0];record=self.life.books[step['book']]
                    self.assertIn(str(w.own.values[4]),record['jobs']);self.assertTrue(all(w.skills.get(s,{}).get('level',0)>=lv for s,lv in record['prerequisites']))
                    self.assertIn(step['action'],('learn','upgrade'));w.skills[step['skill']]={'level':step['target_level']};steps_taken+=1;self.assertLess(steps_taken,300)
                self.assertTrue(all(w.skills[s]['level']>=lv for s,lv in plan.goals()));self.assertEqual(w.own.values,before);self.assertEqual(plan.summary()['guide'],key)
    def test_novice_never_learns_and_first_class_skips_future_only_skills(self):
        for key,p in PROFILES.items():
            w,plan=self.make(key);w.own.values[4]=0;self.assertEqual(plan.next_steps(),[])
            w.own.values[4]=FIRST_JOB[p['job']]
            for step in plan.next_steps():self.assertIn(str(w.own.values[4]),self.life.books[step['book']]['jobs'])
    def test_tank_and_spirit_marine_priorities_differ(self):
        _,tank=self.make('voyager_tank');_,spirit=self.make('voyager_spirit')
        self.assertNotEqual(tank.goals(),spirit.goals());self.assertLess(tank.goals().index((212,10)),tank.goals().index((214,10)));self.assertLess(spirit.goals().index((214,10)),spirit.goals().index((212,10)))
    def test_shooter_speed_and_precision_are_separate(self):
        _,fast=self.make('sharpshooter_speed');_,slow=self.make('sharpshooter_precision');self.assertNotEqual(fast.goals(),slow.goals());self.assertLess(fast.goals().index((75,4)),fast.goals().index((78,5)))
    def test_no_reset_of_known_skills_and_only_two_near_term_books(self):
        w,plan=self.make('cleric_spirit');w.skills[99]={'level':10};before=copy.deepcopy(w.skills);steps=plan.next_steps();self.assertTrue(all(s['skill']!=99 for s in steps));self.assertEqual(w.skills,before);self.assertLessEqual(len(plan.missing_books()),2)
        w.own.values[7]=0;self.assertEqual(plan.missing_books(),[])
    def test_corrupt_guide_or_impossible_rank_rejected(self):
        for change in ('job','unknown','rank','cycle'):
            d=copy.deepcopy(self.life.skill_guides);books=copy.deepcopy(self.life.books)
            if change=='job':d['profiles']['crusader_speed']['job']=8
            elif change=='unknown':d['profiles']['cleric_spirit']['goals'][0]=[999999,1]
            elif change=='rank':d['profiles']['cleric_spirit']['goals'][0][1]=11
            else:books[3208]['prerequisites']=[[99,1]]
            with self.subTest(change=change),self.assertRaises(ValueError):validate_guides(d,books)

    def test_primary_book_reserves_points_then_native_confirmation_required(self):
        from skills import Skills
        w,plan=self.make('cleric_spirit');w.own.values[7]=1
        w.bag={0:BagItem(3206,1,100,100,0,0,0,True)}
        policy=Mock(sequence=1);skills=Skills(w,plan.role,self.life)
        self.assertFalse(skills.tick(0,policy,True));policy.emit.assert_not_called()
        w.bag[1]=BagItem(3208,1,100,100,0,0,0,True)
        self.assertTrue(skills.tick(1,policy,True));self.assertEqual(w.own.values[7],1)
        self.assertEqual(policy.emit.call_args.args[0][-4:],b'\x00\x01\xff\xff')
        w.skills[99]={'level':1};skills.tick(2,policy,True);self.assertEqual(skills.confirmed,0)
        w.own.values[7]=0;skills.tick(3,policy,True);self.assertEqual(skills.confirmed,1)

if __name__=='__main__':unittest.main()
