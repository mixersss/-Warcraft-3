"""Keep ordinary hunting in the character's current level band."""
import dataclasses
import unittest

from hunter import normal_attack
import test_alpha76


class HuntingLevelTests(unittest.TestCase):
    def scene(self, better_camp=True):
        world,policy=test_alpha76.Combat76Tests().policy(monsters=1)
        world.own.values.update({0:43,4:10,31:1500,1:1500})
        wolf=world.entities[1000]
        wolf.values[0]=32
        wolf.model=136
        policy.camp_scouting=True
        policy.clock=300
        policy.learning.last_progress_at=30
        policy.region={'farms':{str(wolf.model):{
            'territory':0,'level':32,'base_xp':300,'hp':200,'points':[wolf.position]}}}
        if better_camp:
            policy.region['farms']['271']={
                'territory':0,'level':42,'base_xp':600,'hp':500,'points':[wolf.position]}
        policy.mob_knowledge={int(k):v for k,v in policy.region['farms'].items()}
        return world,policy,wolf

    def test_level43_cannot_seek_level32_even_after_long_xp_gap(self):
        _,policy,wolf=self.scene(better_camp=False)
        self.assertEqual(policy.minimum_xp_mob_level(300),34)
        self.assertFalse(policy.visible_ground_opportunities(300,policy.position(300)))
        self.assertFalse(policy.eligible(wolf,300,{wolf.model}))
        self.assertFalse(policy.farm_models())

    def test_known_suitable_camp_overrules_weaker_visible_target(self):
        _,policy,wolf=self.scene()
        wolf.values[0]=36
        self.assertEqual(policy.minimum_xp_mob_level(300),38)
        self.assertFalse(policy.eligible(wolf,300,{wolf.model}))
        self.assertEqual(policy.farm_models(),{271})

    def test_ordinary_hunt_attacks_level42_instead_of_level32(self):
        world,policy,wolf=self.scene()
        other=dataclasses.replace(wolf,identity=1001,handle=wolf.handle+1,
                                  model=271,values=dict(wolf.values))
        other.values[0]=42
        world.entities[other.identity]=other
        policy.tick(300)
        self.assertEqual(policy.attacks,1)
        self.assertEqual(policy.last_attack_target,(other.identity,other.handle))

    def test_safe_recovery_target_still_possible_without_better_camp(self):
        _,policy,wolf=self.scene(better_camp=False)
        wolf.values[0]=34
        self.assertEqual(policy.visible_ground_opportunities(300,policy.position(300)),{wolf.identity})
        self.assertTrue(policy.eligible(wolf,300,{wolf.model}))

    def test_defence_and_essential_funding_allow_weak_mob(self):
        world,policy,wolf=self.scene()
        world.own_attackers[wolf.identity]=(wolf.handle,299)
        self.assertEqual(policy.weak_target_exception(wolf,300),'self_defence')
        self.assertIs(policy.nearby_attacker(300),wolf)
        self.assertFalse(policy.eligible(wolf,308,{wolf.model}))
        policy.supply_funding_models={wolf.model}
        self.assertTrue(policy.eligible(wolf,308,{wolf.model}))
        self.assertEqual(policy.weak_target_exception(wolf,308),'essential_supply_funding')

    def test_queued_wolf_attack_rechecked_after_level_up(self):
        world,policy,wolf=self.scene()
        world.own.values[0]=37
        self.assertTrue(policy.eligible(wolf,300,{wolf.model}))
        body=normal_attack(world.own_id,policy.sequence,1,world.default_skill,
                           wolf.identity,wolf.handle,policy.position(300))
        policy.pending_action=(body,300,301,world.stop_revision)
        world.own.values[0]=43
        self.assertTrue(policy.flush_action(301))
        self.assertIsNone(policy.pending_action)
        self.assertEqual(policy.attacks,0)

    def test_active_wolf_attack_is_stopped_after_level_up(self):
        world,policy,wolf=self.scene()
        world.own.values[0]=37
        policy.target=wolf.identity
        policy.target_key=(world.map,wolf.identity,wolf.handle)
        policy.send_action(normal_attack(world.own_id,policy.sequence,1,world.default_skill,
                                         wolf.identity,wolf.handle,policy.position(300)))
        world.own.values[0]=43
        policy.tick(301)
        self.assertIsNone(policy.target)
        self.assertEqual(policy.attacks,1)
        policy.send.assert_called_with(7,b'')
