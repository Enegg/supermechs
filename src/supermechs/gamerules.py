from collections import abc
from typing import Final

from attrs import define, field, validators

from .item import Stat


@define
class BuildRules:
    MAX_WEIGHT: Final[int] = field(default=int(1000), validator=validators.ge(0))
    """The maximum weight of a mech before overload."""
    OVERLOAD: Final[int] = field(default=int(10), validator=validators.ge(0))
    """The maximum extra weight allowed over the max weight."""
    STAT_PENALTIES_PER_KG: Final[abc.Mapping[Stat, int]] = {Stat.hit_points: 15}
    """The ratios at which mech stats are reduced for each kg of overload."""
    EXCLUSIVE_STATS: Final[abc.Set[Stat]] = {
        Stat.physical_resistance,
        Stat.explosive_resistance,
        Stat.electric_resistance,
    }
    """A set of stats which can occur at most once among all modules of a mech."""

    @property
    def OVERLOADED_MAX_WEIGHT(self) -> int:
        """The absolute maximum weight of a mech before it is overweight."""
        return self.MAX_WEIGHT + self.OVERLOAD


@define
class ArenaRules:
    SIZE: Final[int] = 10
    """The length of the arena."""
    START_POSITIONS: Final[abc.Sequence[tuple[int, int]]] = ((4, 5), (3, 6), (2, 8))
    """Sequence of start positions to choose from."""


@define
class GameRules:
    builds: Final[BuildRules] = field(factory=BuildRules)
    arena: Final[ArenaRules] = field(factory=ArenaRules)


DEFAULT_GAME_RULES: Final[GameRules] = GameRules()
