"""Game constants shared by the library files."""

import typing as t

from .enums import Tier
from .typedefs import AnyMechStatKey

MAX_WEIGHT: int = 1000
"""The maximum weight of a mech before overload."""
OVERLOAD: int = 10
"""The maximum extra weight allowed over the max weight."""
OVERLOADED_MAX_WEIGHT: int = MAX_WEIGHT + OVERLOAD
"""The absolute maximum weight of a mech before it is overweight."""
HP_PENALTY_PER_KG: int = 15
"""The ratio at which mech hit points drop for each kg of overload."""
EXCLUSIVE_STAT_KEYS: t.AbstractSet[AnyMechStatKey] = frozenset(("phyRes", "expRes", "eleRes"))
"""A set of stats of which each can be found at up to one module."""
SUMMARY_STAT_KEYS: t.Sequence[str] = t.get_args(AnyMechStatKey)
"""The order of stats which appear in mech summary."""

# the range() covers common-mythical
TIER_MAX_LEVELS: t.Mapping[Tier, int] = {tier: level for tier, level in zip(Tier, range(9, 50, 10))}
"""A mapping of a tier to maximum level an item at which can have.
    Note: in-game levels start at 1, whereas this honors 0-indexing.
"""
TIER_MAX_LEVELS[Tier.DIVINE] = 0
