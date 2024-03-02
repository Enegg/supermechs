from collections import abc
from typing import Final

from attrs import define, field

from supermechs.abc.stats import StatsMapping, StatType
from supermechs.enums.stats import Stat
from supermechs.exceptions import OutOfRangeError
from supermechs.stats import StatsDict

__all__ = ("InterpolatedStats", "LinearStats", "StaticStats")


def lerp(lower: StatType, upper: StatType, weight: float) -> int:
    """Linear interpolation."""
    return lower + round((upper - lower) * weight)


@define
class InterpolatedStats:
    """Stats interpolated between base (minimum) and difference (maximum)."""

    base_stats: Final[StatsMapping] = field()
    """Stats of the item at level 0."""
    difference: Final[StatsMapping] = field()
    """The difference between max stats and base stats."""
    max_level: Final[int] = field()

    def __contains__(self, stat: Stat, /) -> bool:
        return stat in self.base_stats

    def at(self, level: int, /) -> StatsDict:
        """Returns the stats at given level."""

        if level == 0:
            return dict(self.base_stats)

        if level == self.max_level:
            return {**self.base_stats, **self.difference}

        OutOfRangeError.check(0, level, self.max_level)

        weight = level / self.max_level
        stats = dict(self.base_stats)

        for key, value in self.difference.items():
            stats[key] = lerp(stats[key], value, weight)

        return stats


@define
class StaticStats:
    """Static stats that do not change with level."""

    base_stats: Final[StatsMapping] = field()
    """Stats of the item at max level."""

    def __contains__(self, stat: Stat, /) -> bool:
        return stat in self.base_stats

    def at(self, level: int, /) -> StatsDict:
        if level != 0:
            raise OutOfRangeError(0, level, 0) from None
        return dict(self.base_stats)


@define
class LinearStats:
    """Stats provider listing stats at every level."""

    stats: abc.Sequence[StatsMapping] = field()

    def __contains__(self, stat: Stat, /) -> bool:
        return stat in self.stats[0]

    def at(self, level: int, /) -> StatsDict:
        try:
            stats = self.stats[level]

        except IndexError:
            span = len(self.stats)
            raise OutOfRangeError(-span, level, span - 1) from None

        return dict(stats)
