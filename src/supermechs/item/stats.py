import typing as t
import typing_extensions as tex

from attrs import define, field

from ..typeshed import dict_items_as
from .enums import Stat, Tier

__all__ = ("ValueRange", "TransformStage", "StatsMapping", "MutableStatsMapping")


class ValueRange(t.NamedTuple):
    """Lightweight tuple to represent a range of values."""

    lower: int
    upper: int

    def __str__(self) -> str:
        if self.is_single:  # this is false if either is NaN
            return str(self.lower)
        return f"{self.lower}-{self.upper}"

    def __format__(self, format_spec: str, /) -> str:
        # the general format to expect is "number_spec:separator"
        val_fmt, colon, sep = format_spec.partition(":")

        if not colon:
            sep = "-"

        if self.is_single:
            return format(self.lower, val_fmt)

        return f"{self.lower:{val_fmt}}{sep}{self.upper:{val_fmt}}"

    @property
    def is_single(self) -> bool:
        """Whether the range bounds are equal value."""
        return self.lower == self.upper

    def __add__(self, value: tuple[int, int]) -> tex.Self:
        return type(self)(self.lower + value[0], self.upper + value[1])

    def __mul__(self, value: int) -> tex.Self:
        return type(self)(self.lower * value, self.upper * value)


StatsMapping = t.Mapping[Stat, t.Any]
"""Mapping of item stats to values."""
MutableStatsMapping = t.MutableMapping[Stat, t.Any]
"""Mutable mapping of item stats to values."""

SUMMARY_STATS: t.Sequence[Stat] = (
    Stat.weight,
    Stat.hit_points,
    Stat.energy_capacity,
    Stat.regeneration,
    Stat.heat_capacity,
    Stat.cooling,
    Stat.physical_resistance,
    Stat.explosive_resistance,
    Stat.electric_resistance,
    Stat.bullets_capacity,
    Stat.rockets_capacity,
    Stat.walk,
    Stat.jump,
)


def lerp(lower: int, upper: int, weight: float) -> int:
    """Linear interpolation."""
    return lower + round((upper - lower) * weight)


def lerp_vector(minor: ValueRange, major: ValueRange, weight: float) -> ValueRange:
    """Linear interpolation of two vector-like objects."""
    return ValueRange(*map(lerp, minor, major, (weight, weight)))


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
            raise ValueError(level)

        if level == 0:
            return self.base_stats

        if level == max_level:
            return {**self.base_stats, **self.max_level_stats}

        weight = level / max_level
        stats = dict(self.base_stats)

        for key, value in dict_items_as(int | ValueRange, self.max_level_stats):
            base_value: int | ValueRange = stats[key]

            if isinstance(value, ValueRange):
                assert isinstance(base_value, ValueRange)
                stats[key] = lerp_vector(base_value, value, weight)

            else:
                assert not isinstance(base_value, ValueRange)
                stats[key] = lerp(base_value, value, weight)

        return stats


def get_final_stage(stage: TransformStage, /) -> TransformStage:
    """Returns the final stage of transformation."""
    while stage.next is not None:
        stage = stage.next

    return stage


def max_stats(stage: TransformStage, /) -> StatsMapping:
    """Return the max stats."""
    stage = get_final_stage(stage)
    return stage.at(stage.max_level)
