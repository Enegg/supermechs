from collections import abc
from typing import ClassVar, Final
from typing_extensions import Self

from attrs import define, field

from .abc.stats import Stat, StatValue
from .enums.stats import StatEnum
from .utils import init_default

__all__ = ("ArenaRules", "BuildRules", "GameRules")


@init_default
@define
class BuildRules:
    default: ClassVar[Self]

    MAX_WEIGHT: Final[int] = 1000
    """The maximum weight of a mech before overload."""
    OVERLOAD: Final[int] = 10
    """The maximum extra weight allowed over the max weight."""
    STAT_PENALTIES_PER_KG: Final[abc.Mapping[Stat, StatValue]] = {StatEnum.hit_points: 15}
    """The ratios at which mech stats are reduced for each kg of overload."""
    EXCLUSIVE_STATS: Final[abc.Set[Stat]] = {
        StatEnum.physical_resistance,
        StatEnum.explosive_resistance,
        StatEnum.electric_resistance,
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


@init_default
@define
class GameRules:
    default: ClassVar[Self]

    builds: Final[BuildRules] = field(default=BuildRules.default)
    arena: Final[ArenaRules] = field(factory=ArenaRules)
