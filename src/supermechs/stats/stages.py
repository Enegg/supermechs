from collections import abc
from typing import TypeAlias

from attrs import define, field
from typing_extensions import Self

from ..abc.stats import StatsMapping, StatType
from ..enums.stats import Stat, Tier
from ..errors import OutOfRangeError

__all__ = ("StatsDict", "TransformStage", "get_final_stage")

StatsDict: TypeAlias = dict[Stat, StatType]
"""Concrete mapping type of item stats to values."""


def lerp(lower: int, upper: int, weight: float) -> int:
    """Linear interpolation."""
    return lower + round((upper - lower) * weight)


@define(kw_only=True)
class TransformStage:
    """Stores item tier-dependent data."""

    tier: Tier = field()
    """The tier of the transform stage."""
    base_stats: StatsMapping = field()
    """Stats of the item at level 0."""
    max_changing_stats: StatsMapping = field()
    """Stats of the item that change as it levels up, at max level."""
    level_progression: abc.Sequence[int] = field()
    """Sequence of exp thresholds consecutive levels require to reach."""
    next: Self | None = field(default=None)
    """The next stage of transformation."""

    @property
    def max_level(self) -> int:
        """The maximum level this stage can reach, starting from 0."""
        return len(self.level_progression)

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


def get_final_stage(stage: TransformStage, /) -> TransformStage:
    """Traverse to the final stage and return it."""
    while stage.next is not None:
        stage = stage.next

    return stage
