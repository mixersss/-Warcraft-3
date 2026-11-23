import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from economy import Economy
from hunt_observations import HuntObservations
from regions import Regions
from spawn_sources import compile_spawns, refresh_local_spawns
import test_coordination
import test_pet_economy
import test_travel58


class SpawnAndCombat74Tests(unittest.TestCase):
    def test_startup_placements_open_lone_tower_floors(self):
        regions = Regions(ROOT/'assets',400)
        regions.full_regions=True
        first=regions.hunting_arrival_sites('lonetower',(35178,37078))
        second=regions.hunting_arrival_sites('lonetower',(3500,2100))
        self.assertIn(523,first)
        self.assertIn(526,second)
        self.assertNotIn(526,first)
        self.assertGreaterEqual(sum(bool(m['locations']) for m in regions.mob_knowledge.monsters.values()
                                    if m['territory']==0),350)

    def test_local_import_uses_only_proven_map_bindings_and_keeps_last_good_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            scripts=root/'script'/'monster'
            scripts.mkdir(parents=True)
            (scripts/'mlist.lua').write_text(
                'local m = SetCurMap("garner")\nif m==1 then\n PM("Active")\n'
                ' -- PM("Unused")\n PM("Conditional")\nend\n')
            (scripts/'Active.lua').write_text('CreateCha(523, 21000, 22000, 0, 60)\n')
            (scripts/'Unused.lua').write_text('CreateCha(524, 21000, 22000, 0, 60)\n')
            (scripts/'Conditional.lua').write_text('if open then\n CreateCha(525, 21000, 22000, 0, 60)\nend\n')
            (root/'garner').mkdir()
            (root/'garner'/'garnerChaSpn.txt').write_text('1\t22000,24000\t22500,24400\t-1\t526\t2\t0\t45\n')
            self.assertEqual([row[0] for row in compile_spawns(root,ROOT/'assets')['maps']['garner']],[523,526])
            self.assertEqual(refresh_local_spawns(ROOT/'assets',root,root)['mode'],'server')
            output=root/'server-spawns.json'
            self.assertEqual(len(json.loads(output.read_text())['maps']['garner']),2)
            first=output.read_bytes()
            self.assertEqual(refresh_local_spawns(ROOT/'assets',root,root/'missing')['mode'],'last_saved_or_bundled')
            self.assertEqual(output.read_bytes(),first)

    def test_shared_observations_require_distinct_kills_and_persist(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'observations.json'
            atlas=HuntObservations(path)
            atlas.record('garner',523,(223100,278800),(700,701))
            atlas.record('garner',523,(223100,278800),(700,701))
            self.assertFalse(atlas.points('garner'))
            atlas.record('garner',523,(223110,278800),(702,703))
            self.assertEqual(atlas.points('garner'),{523:((223100,278800),)})
            self.assertFalse(atlas.points('darkblue'))
            atlas.save(1)
            self.assertEqual(HuntObservations(path).points('garner'),atlas.points('garner'))

    def test_food_already_in_bag_is_used_in_place_without_shopping(self):
        w,care,policy=test_pet_economy.FairyTests().make()
        w.bag={1:test_pet_economy.item(232,endurance=49),8:test_pet_economy.item(2312,2)}
        self.assertFalse(care.needs_food_visit())
        self.assertTrue(care.tick(1,policy))
        self.assertEqual((care.pending['kind'],care.pending['source']),('feed',8))

    def test_funding_can_farm_local_mobs_above_level12_and_keep_trip(self):
        fixture=test_travel58.Travel58Tests()
        w,travel,policy=fixture.make()
        w.own.values.update({8:0,33:100,34:100,35:35})
        travel.plan=fixture.plan(w,'event')
        w.bag={}
        travel.life=SimpleNamespace(prices={4602:1000})
        self.assertEqual(travel.funding_target(),1100)
        policy.supply_funding_goal=1100
        self.assertFalse(travel.tick(140,policy,True))
        self.assertIsNotNone(travel.plan)
        self.assertEqual(travel.target_started,140)
        economy=Economy('funding',ROOT/'assets')
        farm={'level':25,'hp':100,'territory':0,'points':[w.own.position],'attack_max':15}
        learning=SimpleNamespace(blocked=lambda *a:False,dangerous=lambda *a:False)
        self.assertEqual(economy.weak_funding_models(w,{'farms':{'100':farm}},learning,140),{100})

    def test_vendor_detour_preserves_outbound_hunting_intent(self):
        fixture=test_travel58.Travel58Tests()
        w,travel,policy=fixture.make()
        saved=dict(fixture.plan(w,'portal'),model=523)
        travel.plan=saved
        travel.needs_town=lambda *args:True
        travel.choose=Mock(return_value=None)
        self.assertFalse(travel.tick(100,policy,True))
        self.assertEqual(travel.outbound_resume,(saved,1000))
        travel.needs_town=lambda *args:False
        self.assertFalse(travel.tick(250,policy,True))
        travel.choose.assert_called_with(250,policy,resume=saved)

    def test_conditional_zephyr_is_scouted_once_with_owned_return(self):
        fixture=test_travel58.Travel58Tests()
        w,travel,policy=fixture.make()
        regions=Regions(ROOT/'assets',400)
        travel.regions=regions
        travel.knowledge=regions.mob_knowledge
        w.own.values[0]=52
        policy.learning.last_progress_at=10
        route=dict(fixture.plan(w,'portal'),island=True)
        travel.rate=Mock(return_value=25)
        self.assertFalse(regions.hunting_arrival_sites('garner',(326000,328000)))
        self.assertIsNone(travel.choose_island_scout(300,policy,[route]))
        chosen=travel.choose_island_scout(350,policy,[route])
        nav=regions.nav('garner')
        self.assertEqual(nav.land_component(chosen['scout_point']),nav.land_component((326000,328000)))
        self.assertEqual(travel.knowledge.get(chosen['model'])['level'],51)
        self.assertIsNone(travel.choose_island_scout(351,policy,[route]))
        travel.island_scout=('garner',chosen['scout_point'],360,52,0)
        self.assertEqual(travel.scout_goal(500),chosen['scout_point'])
        w.own.values[15]=15
        self.assertIsNone(travel.scout_goal(501))
        self.assertFalse(travel.scout_return)
        travel.island_scout=('garner',chosen['scout_point'],360,52,15)
        self.assertEqual(travel.scout_goal(500),chosen['scout_point'])
        self.assertIsNone(travel.scout_goal(540))
        self.assertTrue(travel.scout_return)

    def test_confirmed_death_releases_previous_attack_delay(self):
        fixture=test_coordination.CohortCombatTests()
        fixture.setUpClass()
        w,policy=fixture.policy(monsters=2)
        policy.tick(100)
        first=policy.target
        w.entities[first].values[1]=0
        w.stop_packet_number=policy.last_sent_sequence
        w.stop_packet_kind=3
        w.stop_revision+=1
        policy.next_action=110
        policy.tick(100.25)
        self.assertEqual(policy.kills,1)
        self.assertNotEqual(policy.target,first)
        self.assertEqual(policy.attacks,2)
