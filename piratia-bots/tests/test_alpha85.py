"""Level index, distinct camp choices and verified transport candidates."""
import unittest
from pathlib import Path

from coordination import Coordination
from mob_knowledge import MobKnowledge
import test_alpha76
import test_travel58


class HuntCatalogueTests(unittest.TestCase):
    def test_known_zero_xp_species_is_not_a_hunting_choice(self):
        world,policy=test_alpha76.Combat76Tests().policy()
        world.own.values.update({0:43,4:8,31:2700})
        farms={'farms':{
            '100':{'level':42,'hp':600,'base_xp':0,'points':[(100,0)]},
            '101':{'level':36,'hp':600,'base_xp':100,'points':[(200,0)]},
        }}
        self.assertEqual(policy.learning.admissible(farms,world.own,100),{101})
        self.assertEqual(policy.learning.choose(farms,world.own,100),{101})

    def test_all_catalogue_ground_models_are_indexed_at_their_actual_level(self):
        assets=Path(__file__).resolve().parents[1]/'assets'
        knowledge=MobKnowledge(assets/'world-mobs.json')
        for model,mob in knowledge.monsters.items():
            level=mob['level']
            self.assertEqual(model in knowledge.ground_models_in_band(level,level),
                             mob['territory']==0 and level>0)
        expected={m for m,r in knowledge.monsters.items()
                  if r['territory']==0 and 38<=r['level']<=46}
        self.assertEqual(set(knowledge.ground_models_in_band(38,46)),expected)
        self.assertNotIn(136,expected)

    def test_three_distinct_camps_do_not_send_everyone_to_the_first_cell(self):
        _,policy=test_alpha76.Combat76Tests().policy()
        coord=Coordination()
        origin=(0,0)
        points=[(4000,0),(4100,0),(7000,0),(10000,0),(13000,0)]
        options=policy.spread_camp_goals(points,origin)
        self.assertEqual(options,[(4000,0),(7000,0),(10000,0)])
        assigned={coord.choose_zone(str(i),'garner',options,100,origin) for i in range(12)}
        self.assertEqual(assigned,set(options))
        zone=coord.choose_zone('0','garner',options,100,origin)
        coord.renew_zone('0','garner',zone,140)
        self.assertEqual(coord.zones['0'][1],185)

    def test_transport_choices_exclude_duplicate_and_unverified_landings(self):
        world,travel,policy=test_travel58.Travel58Tests().make()
        routes=[]
        for name,x in (('A',1000),('A duplicate',1100),('B',4500),('C',8000),('Blocked',11500)):
            routes.append({'kind':'portal','map':'garner','to_map':'eastgoaf',
                           'name':name,'position':world.own.position,'arrival_cm':(x,2000),'fare':0})
        travel.routes=lambda *args:routes
        travel.rate=lambda *args:100
        travel.nearby=lambda name,point:[(243,0)] if name=='eastgoaf' else []
        travel.regions.hunting_arrival_camps=lambda name,p:{} if p[0]==11500 else {243:((0,p),)}
        chosen=set()
        for index in range(12):
            travel.name=f'bot-{index}'
            plan=travel.choose(100,policy)
            chosen.add(plan['name'])
            names={row['via'] for row in travel.hunt_options}
            self.assertEqual(names,{'A','B','C'})
        self.assertGreater(len(chosen),1)
