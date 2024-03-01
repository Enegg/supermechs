from typing import Final

from attrs import define, field

from supermechs.abc.stats import StatsMapping
from supermechs.enums.stats import Stat
from supermechs.exceptions import OutOfRangeError
from supermechs.stats import StatsDict


def lerp(lower: int, upper: int, weight: float) -> int:
    """Linear interpolation."""
    return lower + round((upper - lower) * weight)


@define
class InterpolatedStats:
    base_stats: Final[StatsMapping] = field()
    """Stats of the item at level 0."""
    max_changing_stats: Final[StatsMapping] = field()
    """Stats of the item that change as it levels up, at max level."""
    max_level: Final[int] = field()

    def __contains__(self, stat: Stat, /) -> bool:
        return stat in self.base_stats

    def at(self, level: int, /) -> StatsDict:
        """Returns the stats at given level."""

        max_level = self.max_level

        if not 0 <= level <= max_level:
            raise OutOfRangeError(0, level, max_level)

        if level == 0:
            return dict(self.base_stats)

        if level == max_level:
            return {**self.base_stats, **self.max_changing_stats}

        weight = level / max_level
        stats = dict(self.base_stats)

        for key, value in self.max_changing_stats.items():
            stats[key] = lerp(stats[key], value, weight)

        return stats


@define
class StaticStats:
    base_stats: Final[StatsMapping] = field()
    """Stats of the item at max level."""

    def __contains__(self, stat: Stat, /) -> bool:
        return stat in self.base_stats

    def at(self, level: int, /) -> StatsDict:
        del level
        return dict(self.base_stats)
