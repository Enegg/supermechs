from collections import abc
from typing import Final, TypeAlias
from typing_extensions import Self

from attrs import define, field

from .abc.stats import StatsProvider, StatType
from .enums.stats import Stat, Tier

__all__ = ("StatsDict", "TransformStage", "get_final_stage")

StatsDict: TypeAlias = dict[Stat, StatType]
"""Concrete mapping type of item stats to values."""


@define(kw_only=True)
class TransformStage:
    """Stores item tier-dependent data."""

    tier: Final[Tier] = field()
    """The tier of the transform stage."""
    stats: Final[StatsProvider] = field()
    """Object relaying stats data."""
    level_progression: Final[abc.Sequence[int]] = field()
    """Sequence of exp thresholds consecutive levels require to reach."""
    next: Final[Self | None] = field(default=None)
    """The next stage of transformation."""

    @property
    def max_level(self) -> int:
        """The maximum level this stage can reach, starting from 0."""
        return len(self.level_progression)

    def at(self, level: int, /) -> StatsDict:
        """Return the stats at given level."""
        stats = self.stats.at(level)

        if not isinstance(stats, dict):
            stats = dict(stats)

        return stats

    def min(self) -> StatsDict:
        """Return the base stats for the stage."""
        return self.at(0)

    def max(self) -> StatsDict:
        """Return the max stats for the stage."""
        return self.at(self.max_level)


def get_final_stage(stage: TransformStage, /) -> TransformStage:
    """Traverse to the final stage and return it."""
    while stage.next is not None:
        stage = stage.next

    return stage
