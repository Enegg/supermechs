"""Game constants shared by the library files."""

import typing as t
import typing_extensions as tex

from .item_stats import AnyMechStatKey

MAX_WEIGHT: int = 1000
"""The maximum weight of a mech before overload."""
OVERLOAD: int = 10
"""The maximum extra weight allowed over the max weight."""
OVERLOADED_MAX_WEIGHT: int = MAX_WEIGHT + OVERLOAD
"""The absolute maximum weight of a mech before it is overweight."""
HP_PENALTY_PER_KG: int = 15
"""The ratio at which mech hit points drop for each kg of overload."""
EXCLUSIVE_STAT_KEYS: t.AbstractSet[AnyMechStatKey] = frozenset(("phyRes", "expRes", "eleRes"))
"""A set of stats of which each can be found at most on one module per mech."""
SUMMARY_STAT_KEYS: t.Sequence[tex.LiteralString] = t.get_args(AnyMechStatKey)
"""The order of stats which appear in mech summary."""
