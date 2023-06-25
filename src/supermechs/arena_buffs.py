import typing as t

from attrs import Factory, define
from typing_extensions import Self

from .core import STATS
from .item_stats import AnyStatsMapping, ValueRange

__all__ = ("ArenaBuffs", "MAX_BUFFS")

ValueT = t.TypeVar("ValueT", int, "ValueRange")


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


@define
class ArenaBuffs:
    BASE_PERCENT: t.ClassVar = (0, 1, 3, 5, 7, 9, 11, 13, 15, 17, 20)
    HP_INCREASES: t.ClassVar = (0, +10, +30, +60, 90, 120, 150, 180, +220, +260, 300, 350)
    # fmt: off
    BUFFABLE_STATS: t.ClassVar = (
        "eneCap", "eneReg", "eneDmg", "heaCap", "heaCol", "heaDmg", "phyDmg",
        "expDmg", "eleDmg", "phyRes", "expRes", "eleRes", "health", "backfire"
    )
    # TODO: perhaps include +% titan damage?
    # fmt: on
    levels: dict[str, int] = Factory(lambda: dict.fromkeys(ArenaBuffs.BUFFABLE_STATS, 0))

    def __getitem__(self, stat_name: str) -> int:
        return self.levels[stat_name]

    def __setitem__(self, stat_name: str, level: int) -> None:
        if level > (max_lvl := self.max_level_of(stat_name)):
            raise ValueError(f"The max level for {stat_name!r} is {max_lvl}, got {level}")

        self.levels[stat_name] = level

    def is_at_zero(self) -> bool:
        """Whether all buffs are at level 0."""
        return all(v == 0 for v in self.levels.values())

    def buff(self, stat_name: str, value: int, /) -> int:
        """Buffs a value according to given stat."""
        if stat_name not in self.levels:
            return value

        level = self.levels[stat_name]
        return self.modifier_at(stat_name, level).apply(value)

    def buff_damage_range(self, stat_name: str, value: ValueRange, /) -> ValueRange:
        """Buff a value range according to given stat."""
        if stat_name not in self.levels:
            return value

        level = self.levels[stat_name]
        modifier = self.modifier_at(stat_name, level)
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

    @classmethod
    def modifier_at(cls, stat_name: str, level: int, /) -> BuffModifier:
        """Returns an object interpretable as an int or the buff's str representation
        at given level.
        """
        if STATS[stat_name].buff == "+":
            return AbsoluteBuffModifier(cls.HP_INCREASES[level])

        return PercentageBuffModifier(cls.get_percent(stat_name, level))

    def modifier_of(self, stat_name: str, /) -> BuffModifier:
        """Returns an object that can be interpreted as an int or the buff's str representation."""
        return self.modifier_at(stat_name, self.levels[stat_name])

    @classmethod
    def get_percent(cls, stat_name: str, level: int) -> int:
        """Returns an int representing the precentage for the stat's modifier."""

        literal_buff = STATS[stat_name].buff

        if literal_buff == "+%":
            return cls.BASE_PERCENT[level]

        if literal_buff == "+2%":
            return cls.BASE_PERCENT[level] * 2

        if literal_buff == "-%":
            return -cls.BASE_PERCENT[level]

        if literal_buff == "+":
            raise TypeError(f"Stat {stat_name!r} has absolute increase")

        raise ValueError(f"Stat {stat_name!r} has no buffs associated")

    @classmethod
    def iter_modifiers_of(cls, stat_name: str) -> t.Iterator[BuffModifier]:
        """Iterator over the modifiers of a stat from 0 to its maximum level."""
        for level in range(cls.max_level_of(stat_name) + 1):
            yield cls.modifier_at(stat_name, level)

    @classmethod
    def max_level_of(cls, stat_name: str) -> int:
        """Get the maximum level for a given buff."""
        if STATS[stat_name].buff == "+":
            return len(cls.HP_INCREASES) - 1

        return len(cls.BASE_PERCENT) - 1

    @classmethod
    def maxed(cls) -> Self:
        """Factory method returning `ArenaBuffs` with all levels set to max."""

        max_buffs = cls()
        levels = max_buffs.levels
        for key in levels:
            levels[key] = cls.max_level_of(key)

        return max_buffs


MAX_BUFFS = ArenaBuffs.maxed()
