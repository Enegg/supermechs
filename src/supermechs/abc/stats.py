from collections import abc
from typing import Protocol, TypeAlias

__all__ = ("MutableStatsMapping", "Stat", "StatValue", "StatsMapping", "Tier")

Stat: TypeAlias = str
Tier: TypeAlias = str

StatValue: TypeAlias = float  # TODO: concrete stat type
StatsMapping: TypeAlias = abc.Mapping[Stat, StatValue]
"""Generic mapping of item stats to their values."""
MutableStatsMapping: TypeAlias = abc.MutableMapping[Stat, StatValue]
"""Generic mutable mapping of item stats to their values."""


class TransformStage(Protocol):
    @property
    def tier(self) -> Tier:
        """The tier of the transform stage."""
        ...

    @property
    def max_level(self) -> int:
        """The maximum level this stage can reach, starting from 0."""
        ...

    def __contains__(self, stat: Stat, /) -> bool: ...

    def power_at(self, level: int, /) -> int:
        """Return the total power necessary to reach given level."""
        ...

    def level_at(self, power: int, /) -> int:
        """Return the level reached with given power."""
        ...

    def stats_at(self, level: int, /) -> StatsMapping:
        """Return the stats at given level."""
        ...

    def min_stats(self) -> StatsMapping:
        """Return the base stats for the stage."""
        return self.stats_at(0)

    def max_stats(self) -> StatsMapping:
        """Return the max level stats for the stage."""
        return self.stats_at(self.max_level)

    def max_power(self) -> int:
        """Return the total power needed to max the stage."""
        return self.power_at(self.max_level)

    def clamp_power(self, power: int, /) -> int:
        """Clamp the power to the maximum."""
        return min(self.max_power(), power)
