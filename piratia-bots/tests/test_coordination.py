"""Cohort regressions: unique combat targets, timeout recovery and promotion in both tactics."""
import concurrent.futures
import math
import struct
import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from coordination import Coordination,tactic_for
from hunter import Hunter
from headless import Report
from world import Entity
from navigation import Navigation
from regions import Regions
from adventure import Adventure
from test_hunt import world_fixture
from test_adventure import role,offers,page
from test_development import scene


class ReservationsTests(unittest.TestCase):
    def test_thirty_simultaneous_claims_have_one_winner(self):
        coordinator=Coordination();gate=threading.Barrier(30)
        def claim(i):
            gate.wait(timeout=10)
            return coordinator.claim(str(i),('garner',10,100),0)
        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as pool:
            self.assertEqual(sum(pool.map(claim,range(30))),1)

    def test_release_expiry_map_and_respawn_handle_isolation(self):
        c=Coordination();key=('garner',1,2)
        self.assertTrue(c.claim('a',key,0))
        self.assertFalse(c.claim('b',key,1))
        self.assertTrue(c.claim('b',('magicsea',1,2),1))
        self.assertTrue(c.claim('c',('garner',1,3),1))
        self.assertTrue(c.claim('a',key,7)) # Renewable, not abandoned at original deadline.
        self.assertFalse(c.claim('b',key,8))
        self.assertTrue(c.claim('b',key,16))
        c.release('b',zone=True)
        self.assertTrue(c.claim('a',key,17))

    def test_30_farm_destinations_are_balanced_and_stable(self):
        from collections import Counter
        c=Coordination();goals=[(100,200),(300,400),(500,600)]
        chosen=[c.choose_zone(str(i),'garner',goals,0) for i in range(30)]
        self.assertEqual(sorted(Counter(chosen).values()),[10,10,10])
        self.assertEqual(c.choose_zone('0','garner',goals,20),chosen[0])
        c.leave_zone('0')
        self.assertNotIn('0',c.zones)
        c.choose_zone('new','garner',goals,70)
        self.assertEqual(len(c.zones),1)


class CohortCombatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.nav=Navigation(ROOT/'assets/argent-navigation.json')

    def policy(self,index=0,coordinator=None,monsters=1):
        w=world_fixture();w.own_id=123+index;own=w.entities.pop(123);own.identity=w.own_id
        w.entities[w.own_id]=own
        for i in range(monsters):
            identity=1000+i
            w.entities[identity]=Entity(75,identity,2000+i,5,1,223300,278700,40,{0:1,1:100,31:100})
        p=Hunter(w,self.nav,Mock(),Report(),Mock(),f'Bot{index:08x}')
        p.started=0;p.coordination=coordinator
        return w,p

    def test_thirty_bots_attack_thirty_different_visible_monsters(self):
        c=Coordination();policies=[self.policy(i,c,30)[1] for i in range(30)]
        for p in policies:p.tick(100)
        self.assertEqual(len({p.target for p in policies}),30)
        self.assertTrue(all(p.attacks==1 for p in policies))
        # Renew target leases while their own clients report normal HP progress.
        for p in policies:
            p.world.entities[p.target].values[1]=80
            p.tick(104)
        self.assertEqual(len({p.target for p in policies}),30)

    def test_excess_bots_do_not_join_reserved_monster(self):
        c=Coordination();pairs=[self.policy(i,c,1) for i in range(3)]
        for w,p in pairs:p.tick(100)
        self.assertEqual(sum(p.attacks for _,p in pairs),1)
        winner=next(p for _,p in pairs if p.target)
        winner.drop_target()
        _,waiting=next((w,p) for w,p in pairs if p is not winner)
        waiting.tick(104)
        self.assertEqual(waiting.target,1000)
        self.assertEqual(waiting.attacks,1)

    def test_no_damage_target_is_released_and_blacklisted_instead_of_permanent_stop(self):
        c=Coordination();w,p=self.policy(0,c,2)
        p.tick(100);failed=p.target
        for now in (103,106,109,112,115):p.tick(now)
        self.assertEqual(p.no_damage_retargets,1)
        self.assertGreater(p.blacklist[failed],115)
        self.assertNotEqual(p.target,failed)
        self.assertEqual(p.target,1000 if failed==1001 else 1001)
        self.assertTrue(c.available('another',('garner',failed,1000+failed),115))

    def test_observed_damage_keeps_legitimate_long_fight(self):
        w,p=self.policy();p.tick(100)
        for now,hp in ((104,95),(108,90),(112,85),(116,80),(120,75),(124,70),(128,65),(132,60),(136,55)):
            w.entities[p.target].values[1]=hp
            p.tick(now)
        self.assertEqual(p.target,1000)
        self.assertEqual(p.no_damage_retargets,0)

    def test_stuck_state_recovers_and_releases_old_target(self):
        c=Coordination();w,p=self.policy(0,c,1)
        p.tick(100);p.stuck=5
        p.tick(104)
        self.assertEqual(p.recoveries,1)
        self.assertIsNone(p.target)
        self.assertLess(p.stuck,5)
        self.assertGreater(p.moves,0)
        self.assertTrue(c.available('other',('garner',1000,2000),104))
        self.assertNotIn('остановка движения',p.mode)

    def test_releasing_claims_during_quest_travel_preserves_acknowledgement_wait(self):
        w,p=self.policy(monsters=0)
        destination=self.nav.waypoints[0]
        adventure=Mock(reason='задание: путь к наставнику')
        adventure.tick.side_effect=lambda now,policy: policy.move_to(destination,now)
        p.adventure=adventure
        p.tick(100)
        p.tick(101)
        self.assertEqual(p.moves,1)
        self.assertEqual(p.move_goal,destination)

    def test_combat_position_correction_replaces_stale_prediction(self):
        w,p=self.policy()
        w.freeze_prediction(100)
        corrected=(223250,278750)
        packet=(struct.pack('>IIBBHBBB',w.own_id,1,4,1,0,0,0,1)
                +struct.pack('>II',*corrected)+bytes(24)+bytes(2)
                +struct.pack('>BHBI',3,1,1,80))
        w.observe(508,packet)
        self.assertEqual(w.position(102),corrected)
        self.assertEqual(w.own.values[1],80)

    def test_death_releases_target_for_surviving_bot(self):
        c=Coordination();w,p=self.policy(0,c,1)
        p.tick(100);w.own.values[1]=0;p.tick(104)
        self.assertIsNone(p.target)
        self.assertTrue(c.claim('other',('garner',1000,2000),104))

    def test_approach_stops_within_attack_range_and_avoids_occupied_endpoint(self):
        w,p=self.policy();target=w.entities[1000]
        target.x=224000
        point=p.approach(target,230,100)
        self.assertIsNotNone(point)
        self.assertLessEqual(math.dist(point,target.position),210)
        self.assertTrue(p.nav.path(w.own.position,point))
        w.entities[999]=Entity(1,999,9999,1,0,*point,40,{1:100,31:100})
        alternate=p.approach(target,230,100)
        self.assertIsNotNone(alternate)
        self.assertGreaterEqual(math.dist(point,alternate),100)


class TacticsTests(unittest.TestCase):
    def quest(self,first=1,tactic='farm',map_name='garner'):
        w=scene();w.map=map_name
        regions=Regions(ROOT/'assets')
        q=Adventure(w,Mock(),role=role(first),region=regions.get(map_name),tactic=tactic)
        q.journal_ready=True
        return w,q

    def test_default_cohort_has_fifteen_of_each_stable_tactic(self):
        styles=[tactic_for(i) for i in range(1,31)]
        self.assertEqual(styles.count('quests'),15)
        self.assertEqual(styles.count('farm'),15)
        self.assertEqual(tactic_for(4,'adventure'),'quests')
        self.assertEqual(tactic_for(5,'hunt'),'farm')

    def test_farmer_ignores_optional_tutorial_but_preserves_existing_journal(self):
        w,q=self.quest();q.journal={1:0,701:0,704:0}
        before=dict(q.journal)
        self.assertIsNone(q.active())
        self.assertFalse(q.tick(100,Mock()))
        q.send.assert_not_called()
        self.assertEqual(q.journal,before)
        self.assertIsNone(q.farm())

    def test_quest_tactic_keeps_tutorial_before_profession_level(self):
        w,q=self.quest(tactic='quests');q.journal={704:0}
        self.assertEqual(q.active(),704)
        self.assertEqual(q.farm(),(103,1620))

    def test_both_tactics_prioritize_only_pinned_promotion_at_level_nine_in_all_cities(self):
        for tactic in ('quests','farm'):
            for first,map_name in ((1,'garner'),(4,'garner'),(2,'darkblue'),(5,'magicsea')):
                w,q=self.quest(first,tactic,map_name);w.own.values[0]=9
                q.journal={704:0}
                self.assertIsNone(q.active())
                q.context=99,'senna','talk',None
                entries=[('Welcome',1),(role(1 if first!=1 else 2)['promotion'],1),(role(first)['promotion'],1)]
                q.process_event(802,offers(99,entries),100)
                q.send.assert_called_once()
                self.assertEqual(q.context[-1],role(first)['promotion'])
                q.send.reset_mock()
                q.process_event(827,page(99,role(first)['promotion']),101)
                q.send.assert_called_once() # Both styles use normal native accept.

    def test_farm_style_profession_kills_and_items_are_not_skipped(self):
        for first,map_name,mission,model,needed in ((1,'garner',62,237,None),(4,'garner',160,104,1595),
                                                    (2,'darkblue',150,234,1779),(5,'magicsea',82,62,3129)):
            w,q=self.quest(first,'farm',map_name);w.own.values[0]=15
            q.journal={mission:0,704:0}
            self.assertEqual(q.active(),mission)
            self.assertEqual(q.farm(),(model,needed))
            self.assertIn(model,q.desired_models())
            self.assertFalse(q.tick(100,Mock())) # Hunting objective, not NPC chatter.

    def test_farmer_selects_stronger_species_as_server_level_increases(self):
        w,q=self.quest()
        levels=[]
        for level in (1,3,6,10,15):
            w.own.values[0]=level
            models=q.desired_models()
            actual=[q.region['farms'][str(m)]['level'] for m in models]
            self.assertTrue(all(m<=level for m in actual))
            levels.append(max(actual))
        self.assertEqual(levels,sorted(set(levels)))

    def test_profession_is_not_forged_and_farmer_returns_to_grind_after_real_promotion(self):
        w,q=self.quest();w.own.values.update({0:10,4:1});q.journal={62:0}
        self.assertFalse(q.tick(100,Mock()))
        q.send.assert_not_called()
        self.assertEqual(w.own.values[4],1)
        self.assertIsNone(q.farm())
        self.assertNotEqual(q.desired_models(),{237})


if __name__=='__main__':unittest.main()
