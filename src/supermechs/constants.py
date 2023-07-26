"""Game constants shared by the library files."""

import typing as t

from .typedefs import AnyMechStatKey

MAX_WEIGHT: int = 1000
OVERWEIGHT: int = 10
MAX_OVERWEIGHT = MAX_WEIGHT + OVERWEIGHT
HEALTH_PENALTY_PER_KG: int = 15

EXCLUSIVE_STATS: t.AbstractSet[AnyMechStatKey] = frozenset(("phyRes", "expRes", "eleRes"))
"""Stats which can be found at maximum of one module."""

WORKSHOP_STATS: t.Sequence[str] = t.get_args(AnyMechStatKey)
"""The stats that can appear in mech summary, in order."""
