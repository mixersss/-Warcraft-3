"""Level limits hold from a known mine camp to native attack dispatch."""
import dataclasses
import unittest
from unittest.mock import Mock

from hunter import normal_attack
from regions import Regions
import test_alpha80
import test_travel58


class MineHuntingTierTests(unittest.TestCase):
    def scene(self):
        world,policy,pumpkin=test_alpha80.HuntingLevelTests().scene()
        world.map='eastgoaf'
        policy.nav.map='eastgoaf'
        world.own.values[0]=36
        pumpkin.model=37
        pumpkin.values[0]=46
        weaker=dataclasses.replace(pumpkin,identity=1001,handle=pumpkin.handle+1,
                                  model=243,values=dict(pumpkin.values))
        weaker.values[0]=38
        world.entities[weaker.identity]=weaker
        policy.region={'farms':{
            '37':{'territory':0,'level':46,'base_xp':1000,'hp':500,'points':[pumpkin.position]},
            '243':{'territory':0,'level':38,'base_xp':600,'hp':300,'points':[weaker.position]}}}
        policy.mob_knowledge={int(model):record for model,record in policy.region['farms'].items()}
        return world,policy,pumpkin,weaker

    def test_bot_36_chooses_mob_38_even_after_pumpkin_aggro(self):
        world,policy,pumpkin,weaker=self.scene()
        world.own_attackers[pumpkin.identity]=(pumpkin.handle,299)
        self.assertFalse(policy.eligible(pumpkin,300,{37}))
        self.assertIsNone(policy.nearby_attacker(300))
        policy.tick(300)
        self.assertEqual(policy.attacks,1)
        self.assertEqual(policy.last_attack_target,(weaker.identity,weaker.handle))

    def test_quest_and_previous_wins_cannot_send_bot_to_pumpkin_camp(self):
        world,policy,pumpkin,_=self.scene()
        world.own.values[0]=39
        policy.learning.rows['37']={'wins':20,'hp_cost':0}
        policy.learning.selected={37}
        policy.story=Mock()
        policy.story.desired_models.return_value={37}
        self.assertEqual(policy.quest_models(),set())
        self.assertNotIn(37,policy.learning.admissible(policy.region,world.own,300))
        self.assertNotIn(37,policy.farm_models())
        self.assertFalse(policy.eligible(pumpkin,300,{37}))

    def test_native_mob_level_is_rechecked_on_queued_attack(self):
        world,policy,pumpkin,_=self.scene()
        pumpkin.values[0]=39
        self.assertTrue(policy.eligible(pumpkin,300,{37}))
        body=normal_attack(world.own_id,policy.sequence,1,world.default_skill,
                           pumpkin.identity,pumpkin.handle,policy.position(300))
        policy.pending_action=(body,300,301,world.stop_revision)
        pumpkin.values[0]=46
        self.assertTrue(policy.flush_action(301))
        self.assertEqual(policy.attacks,0)
        self.assertIsNone(policy.pending_action)

    def test_mine_with_only_overlevel_camps_uses_known_exit(self):
        _,policy,_,_=self.scene()
        _,travel,_=test_travel58.Travel58Tests().make()
        world=policy.world
        travel.regions=Regions(test_travel58.ROOT/'assets')
        travel.data=travel.regions.hunting_travel_data
        travel.world=world
        world.bag_ready=True
        entry=next(row for row in travel.data['entrances'] if row['name']=='Silver Mine 2 - Silver Mine 3')
        world.own.x,world.own.y=entry['arrival_cm']
        policy.nav=travel.regions.nav('eastgoaf')
        farm=policy.region['farms']
        farm['37']['points']=[world.own.position]
        farm['243']['points']=[world.own.position]
        self.assertTrue(policy.mine_has_level_camp(300))
        del farm['243']
        policy.local_region_key=None
        policy.move_to=Mock(return_value=True)
        self.assertTrue(travel.tick(301,policy,True))
        self.assertEqual(travel.plan['name'],'Silver Mine 3 - Silver Mine 2')
        self.assertTrue(travel.plan['mine_exit'])
        policy.move_to.assert_called_once()
