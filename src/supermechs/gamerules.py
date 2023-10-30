import typing as t

from attrs import define, field

from .item import Stat


@define
class MechGameRules:
    MAX_WEIGHT: t.Final[int] = 1000
    """The maximum weight of a mech before overload."""
    OVERLOAD: t.Final[int] = 10
    """The maximum extra weight allowed over the max weight."""
    STAT_PENALTIES_PER_KG: t.Final[t.Mapping[Stat, int]] = {Stat.hit_points: 15}
    """The ratios at which mech summary stats are altered for each kg of overload."""
    EXCLUSIVE_STAT_KEYS: t.AbstractSet[Stat] = {
        Stat.physical_resistance,
        Stat.explosive_resistance,
        Stat.electric_resistance,
    }
    """A set of stats of which each can be found at most on one module per mech."""

    @property
    def OVERLOADED_MAX_WEIGHT(self) -> int:
        """The absolute maximum weight of a mech before it is overweight."""
        return self.MAX_WEIGHT + self.OVERLOAD


@define
class GameRules:
    mech: MechGameRules = field(factory=MechGameRules)


DEFAULT_GAME_RULES: t.Final[GameRules] = GameRules()
