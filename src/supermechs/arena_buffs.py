import typing as t
from typing_extensions import Self

from attrs import Factory, define

from ._internal import BASE_LVL_INCREASES, BUFFABLE_STATS, HIT_POINT_INCREASES, STATS
from .item_stats import AnyStatsMapping, ValueRange

__all__ = ("ArenaBuffs",)

ValueT = t.TypeVar("ValueT", int, "ValueRange")


def max_level_of(stat_key: str, /) -> int:
    """Get the maximum level for a given buff."""
    return len(HIT_POINT_INCREASES if STATS[stat_key].buff == "+HP" else BASE_LVL_INCREASES) - 1


def get_percent(stat_key: str, level: int, /) -> int:
    """Returns an int representing the precentage for the stat's modifier."""

    literal_buff = STATS[stat_key].buff

    if literal_buff == "+%":
        return BASE_LVL_INCREASES[level]

    if literal_buff == "resist%":
        return BASE_LVL_INCREASES[level] * 2

    if literal_buff == "-%":
        return -BASE_LVL_INCREASES[level]

    if literal_buff == "+HP":
        raise TypeError(f"Stat {stat_key!r} has absolute increase")

    raise ValueError(f"Stat {stat_key!r} has no buffs associated")


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


def modifier_at(stat_key: str, level: int, /) -> BuffModifier:
    """Returns an object interpretable as an int or the buff's str representation
    at given level.
    """
    if STATS[stat_key].buff == "+HP":
        return AbsoluteBuffModifier(HIT_POINT_INCREASES[level])

    return PercentageBuffModifier(get_percent(stat_key, level))


def iter_modifiers_of(stat_key: str, /) -> t.Iterator[BuffModifier]:
    """Iterator over the modifiers of a stat from 0 to its maximum level."""
    for level in range(max_level_of(stat_key) + 1):
        yield modifier_at(stat_key, level)


@define
class ArenaBuffs:
    levels: t.MutableMapping[str, int] = Factory(lambda: dict.fromkeys(BUFFABLE_STATS, 0))

    def __getitem__(self, stat_key: str, /) -> int:
        return self.levels[stat_key]

    def __setitem__(self, stat_key: str, level: int, /) -> None:
        if level > (max_lvl := max_level_of(stat_key)):
            raise ValueError(f"The max level for {stat_key!r} is {max_lvl}, got {level}")

        self.levels[stat_key] = level

    def is_at_zero(self) -> bool:
        """Whether all buffs are at level 0."""
        return all(v == 0 for v in self.levels.values())

    def buff(self, stat_key: str, value: int, /) -> int:
        """Buffs a value according to given stat."""
        if stat_key not in self.levels:
            return value

        level = self.levels[stat_key]
        return modifier_at(stat_key, level).apply(value)

    def buff_damage_range(self, stat_key: str, value: ValueRange, /) -> ValueRange:
        """Buff a value range according to given stat."""
        if stat_key not in self.levels:
            return value

        level = self.levels[stat_key]
        modifier = modifier_at(stat_key, level)
        return ValueRange(*map(modifier.apply, value))

    def buff_with_difference(self, stat_name: str, value: int, /) -> tuple[int, int]:
        """Returns buffed value and the difference between the result and the initial value."""
        buffed = self.buff(stat_name, value)
        return buffed, buffed - value

    # the overloads are redundant, but TypedDict fallbacks to object as their value type
    # and that doesn't play well with typing
    @t.overload
    def buff_stats(self, stats: AnyStatsMapping, /, *, buff_health: bool = ...) -> AnyStatsMapping:
        ...

    @t.overload
    def buff_stats(
        self, stats: t.Mapping[str, ValueT], /, *, buff_health: bool = ...
    ) -> dict[str, ValueT]:
        ...

    def buff_stats(
        self, stats: t.Mapping[str, ValueT] | AnyStatsMapping, /, *, buff_health: bool = False
    ) -> dict[str, ValueT] | AnyStatsMapping:
        """Returns the buffed stats."""
        buffed: dict[str, ValueT] = {}

        for key, value in t.cast(t.Mapping[str, ValueT], stats).items():
            if key == "health" and not buff_health:
                buffed[key] = value

            elif isinstance(value, ValueRange):
                buffed[key] = self.buff_damage_range(key, value)

            else:
                buffed[key] = self.buff(key, value)

        return buffed

    def modifier_of(self, stat_name: str, /) -> BuffModifier:
        """Returns an object that can be interpreted as an int or the buff's str representation."""
        return modifier_at(stat_name, self.levels[stat_name])

    @classmethod
    def maxed(cls) -> Self:
        """Factory method returning `ArenaBuffs` with all levels set to max."""

        self = cls()
        for key in self.levels:
            self.levels[key] = max_level_of(key)

        return self
