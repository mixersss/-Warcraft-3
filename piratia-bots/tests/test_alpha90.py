import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from loot import QuestLoot
from market import Market, MarketCatalog
from world_drops import NPC_TROPHY_PRICES, STACK_GEM_PRICES
import test_alpha57


class WorldExpansionBotTests(unittest.TestCase):
    def test_earned_gem_joins_existing_stack_even_when_bag_is_full(self):
        world, policy = test_alpha57.magic.MagicTests().make()
        world.bag_ready, world.bag_capacity = True, 1
        world.bag = {0: test_alpha57.vendor.VendorTests().item(6400, 98)}
        world.own_hits = {123: (9, True)}
        world.items = {55: (6400, 55, world.own.position, 1, 123, 8)}
        loot = QuestLoot(world)
        loot.ground_gems.update(STACK_GEM_PRICES)
        loot.stackable_ground.update(STACK_GEM_PRICES)
        loot.fast_mode = True
        policy.emit = Mock()
        self.assertTrue(loot.tick(10, policy, {6400}))
        world.bag = {0: test_alpha57.vendor.VendorTests().item(6400, 99)}
        world.items = {}
        loot.tick(11, policy, {6400})
        self.assertEqual(loot.confirmed, 1)

    def test_stack_gems_are_priced_per_unit_and_parchment_goes_to_npc(self):
        assets = Path(__file__).resolve().parents[1]/'assets'
        overlay = {'prices': {}, 'catalog_revision': 60, 'world_expansion': True}
        with patch('owner_shops.read_overlay', return_value=overlay):
            catalog = MarketCatalog(assets)
        catalog.enable_curated_catalog()
        self.assertNotIn(684, catalog.items)
        market = Market(None, None, 'fixture', 1, catalog, None, None, None)
        for identity, price in STACK_GEM_PRICES.items():
            self.assertEqual(market.ask_price(identity), price)
        self.assertEqual(NPC_TROPHY_PRICES[684], 100_000)
