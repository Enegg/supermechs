from collections import abc
from typing import Final, TypeAlias
from typing_extensions import Self

from attrs import define, field

from .abc.stats import StatsMapping, StatType
from .enums.stats import Stat, Tier
from .exceptions import OutOfRangeError

__all__ = ("StatsDict", "TransformStage", "get_final_stage")

StatsDict: TypeAlias = dict[Stat, StatType]
"""Concrete mapping type of item stats to values."""


def lerp(lower: int, upper: int, weight: float) -> int:
    """Linear interpolation."""
    return lower + round((upper - lower) * weight)


@define(kw_only=True)
class TransformStage:
    """Stores item tier-dependent data."""

    tier: Final[Tier] = field()
    """The tier of the transform stage."""
    base_stats: Final[StatsMapping] = field()
    """Stats of the item at level 0."""
    max_changing_stats: Final[StatsMapping] = field()
    """Stats of the item that change as it levels up, at max level."""
    level_progression: Final[abc.Sequence[int]] = field()
    """Sequence of exp thresholds consecutive levels require to reach."""
    next: Final[Self | None] = field(default=None)
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

    def min(self) -> StatsDict:
        """Returns the base stats for the stage."""
        return self.at(0)

    def max(self) -> StatsDict:
        """Returns the max stats for the stage."""
        return self.at(self.max_level)


def get_final_stage(stage: TransformStage, /) -> TransformStage:
    """Traverse to the final stage and return it."""
    while stage.next is not None:
        stage = stage.next

    return stage
