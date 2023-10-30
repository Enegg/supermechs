import typing as t
import typing_extensions as tex

from attrs import define, field

from ..errors import OutOfRangeError
from .enums import Stat, Tier

__all__ = ("TransformStage", "StatsMapping", "MutableStatsMapping")


StatsMapping = t.Mapping[Stat, t.Any]
"""Mapping of item stats to values."""
MutableStatsMapping = t.MutableMapping[Stat, t.Any]
"""Mutable mapping of item stats to values."""


def lerp(lower: int, upper: int, weight: float) -> int:
    """Linear interpolation."""
    return lower + round((upper - lower) * weight)


@define(kw_only=True)
class TransformStage:
    """Dataclass collecting transformation tier dependent item data."""

    tier: Tier = field()
    """The tier of the transform stage."""
    base_stats: StatsMapping = field()
    """Stats of the item at level 0."""
    max_level_stats: StatsMapping = field()
    """Stats of the item that change as it levels up, at max level."""
    level_progression: t.Sequence[int] = field()
    """Sequence of exp thresholds consecutive levels require to reach."""
    next: tex.Self | None = field(default=None)
    """The next stage of transformation."""

    @property
    def max_level(self) -> int:
        """The maximum level this stage can reach, starting from 0."""
        return len(self.level_progression)

    def at(self, level: int, /) -> StatsMapping:
        """Returns the stats at given level."""

        max_level = self.max_level

        if not 0 <= level <= max_level:
            raise OutOfRangeError(level, 0, max_level)

        if level == 0:
            return self.base_stats

        if level == max_level:
            return {**self.base_stats, **self.max_level_stats}

        weight = level / max_level
        stats = dict(self.base_stats)

        for key, value in self.max_level_stats.items():
            stats[key] = lerp(stats[key], value, weight)

        return stats


def get_final_stage(stage: TransformStage, /) -> TransformStage:
    """Returns the final stage of transformation."""
    while stage.next is not None:
        stage = stage.next

    return stage
