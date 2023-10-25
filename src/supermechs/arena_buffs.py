import typing as t
from typing_extensions import Self

from attrs import Factory, define

from ._internal import BASE_LVL_INCREASES, BUFFABLE_STATS, HIT_POINT_INCREASES, STATS
from .item.stats import MutableStatsMapping, Stat, StatsMapping, ValueRange

__all__ = ("MAX_BUFFS", "ArenaBuffs", "max_out")


def max_level_of(stat: Stat, /) -> int:
    """Get the maximum level for a given buff."""
    return len(HIT_POINT_INCREASES if STATS[stat].buff == "+HP" else BASE_LVL_INCREASES) - 1


def get_percent(stat: Stat, level: int, /) -> int:
    """Returns an int representing the precentage for the stat's modifier."""

    literal_buff = STATS[stat].buff

    if literal_buff == "+%":
        return BASE_LVL_INCREASES[level]

    if literal_buff == "resist%":
        return BASE_LVL_INCREASES[level] * 2

    if literal_buff == "-%":
        return -BASE_LVL_INCREASES[level]

    if literal_buff == "+HP":
        msg = f"Stat {stat} has absolute increase"
        raise TypeError(msg)

    msg = f"Stat {stat} has no buffs associated"
    raise ValueError(msg)


class BuffModifier(t.Protocol):
    @property
    def value(self) -> int:
        ...

    def apply(self, value: int, /) -> int:
        ...


class PercentageBuffModifier(t.NamedTuple):
    value: int

    def __str__(self) -> str:
        return f"{self.value:+}%"

    def __int__(self) -> int:
        return self.value

    def apply(self, value: int, /) -> int:
        return round(value * (1 + self.value / 100))


class AbsoluteBuffModifier(t.NamedTuple):
    value: int

    def __str__(self) -> str:
        return f"+{self.value}"

    def __int__(self) -> int:
        return self.value

    def apply(self, value: int, /) -> int:
        return value + self.value


def modifier_at(stat: Stat, level: int, /) -> BuffModifier:
    """Returns an object interpretable as an int or the buff's str representation
    at given level.
    """
    if STATS[stat].buff == "+HP":
        return AbsoluteBuffModifier(HIT_POINT_INCREASES[level])

    return PercentageBuffModifier(get_percent(stat, level))


def iter_modifiers_of(stat: Stat, /) -> t.Iterator[BuffModifier]:
    """Iterator over the modifiers of a stat from 0 to its maximum level."""
    for level in range(max_level_of(stat) + 1):
        yield modifier_at(stat, level)


@define
class ArenaBuffs:
    levels: t.MutableMapping[Stat, int] = Factory(lambda: dict.fromkeys(BUFFABLE_STATS, 0))

    def __getitem__(self, stat: Stat, /) -> int:
        return self.levels[stat]

    def __setitem__(self, stat: Stat, level: int, /) -> None:
        if not 0 <= level <= (max_lvl := max_level_of(stat)):
            msg = f"The max level for {stat!r} is {max_lvl}, got {level}"
            raise ValueError(msg)

        self.levels[stat] = level

    def is_at_zero(self) -> bool:
        """Whether all buffs are at level 0."""
        return all(v == 0 for v in self.levels.values())

    def buff(self, stat: Stat, value: int, /) -> int:
        """Buffs a value according to given stat."""
        if stat not in self.levels:
            return value

        level = self.levels[stat]
        return modifier_at(stat, level).apply(value)

    def buff_damage_range(self, stat: Stat, value: ValueRange, /) -> ValueRange:
        """Buff a value range according to given stat."""
        if stat not in self.levels:
            return value

        level = self.levels[stat]
        modifier = modifier_at(stat, level)
        return ValueRange(*map(modifier.apply, value))

    def buff_with_difference(self, stat: Stat, value: int, /) -> tuple[int, int]:
        """Returns buffed value and the difference between the result and the initial value."""
        buffed = self.buff(stat, value)
        return buffed, buffed - value

    def buff_stats(self, stats: StatsMapping, /, *, buff_health: bool = False) -> StatsMapping:
        """Returns the buffed stats."""
        buffed: MutableStatsMapping = {}

        for key, value in stats.items():
            if key is Stat.hit_points and not buff_health:
                buffed[key] = value

            elif isinstance(value, ValueRange):
                buffed[key] = self.buff_damage_range(key, value)

            else:
                buffed[key] = self.buff(key, value)

        return buffed

    def modifier_of(self, stat: Stat, /) -> BuffModifier:
        """Returns an object that can be interpreted as an int or the buff's str representation."""
        return modifier_at(stat, self.levels[stat])

    @classmethod
    def maxed(cls) -> Self:
        """Factory method returning `ArenaBuffs` with all levels set to max."""
        self = cls()
        max_out(self)
        return self


def max_out(buffs: ArenaBuffs, /) -> None:
    """Sets all levels of arena buffs to max."""

    for key in BUFFABLE_STATS:
        buffs.levels[key] = max_level_of(key)


MAX_BUFFS = ArenaBuffs()  # the buffs are populated by _internal
