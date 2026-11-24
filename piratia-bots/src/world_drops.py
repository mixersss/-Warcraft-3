"""Inventory identities for the optional world expansion installed on GameServer."""

STACK_GEM_PRICES = dict(zip(range(5609, 5617), (
    100_000, 100_000, 110_000, 120_000, 150_000, 150_000, 140_000, 130_000,
)))
STACK_GEM_PRICES.update({old: STACK_GEM_PRICES[5609+offset] for offset,old in enumerate(range(6400,6408))})
NPC_TROPHY_PRICES = {first+offset: (offset+1)*1000
                     for first in (5618, 6410) for offset in range(30)}
NPC_TROPHY_PRICES[684] = 100_000
