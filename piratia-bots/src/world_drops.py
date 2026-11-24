"""Inventory identities for the optional world expansion installed on GameServer."""

STACK_GEM_PRICES = dict(zip(range(6400, 6408), (
    100_000, 100_000, 110_000, 120_000, 150_000, 150_000, 140_000, 130_000,
)))
NPC_TROPHY_PRICES = {6409+level: level*1000 for level in range(1, 31)}
NPC_TROPHY_PRICES[684] = 100_000
