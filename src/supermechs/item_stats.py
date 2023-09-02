import typing as t
import typing_extensions as tex

from attrs import define, field

from .enums import Tier
from .typeshed import dict_items_as

__all__ = (
    "ValueRange", "TransformStage",
    "AnyMechStatsMapping", "AnyStatsMapping",
    "AnyMechStatKey", "AnyStatKey"
)

# fmt: off
AnyMechStatKey = t.Literal[
    "weight", "health",
    "eneCap", "eneReg",
    "heaCap", "heaCol",
    "phyRes", "expRes", "eleRes",
    "bulletsCap", "rocketsCap",
    "walk", "jump"
]
AnyStatKey = AnyMechStatKey | t.Literal[
    "phyDmg", "phyResDmg",
    "expDmg", "heaDmg", "heaCapDmg", "heaColDmg", "expResDmg",
    "eleDmg", "eneDmg", "eneCapDmg", "eneRegDmg", "eleResDmg",
    "range", "push", "pull", "recoil", "retreat", "advance",
    "uses", "backfire", "heaCost", "eneCost", "bulletsCost", "rocketsCost"
]
# fmt: on


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


class AnyMechStatsMapping(t.TypedDict, total=False):
    """Mapping of keys representing overall mech stats."""
    weight: int
    health: int
    eneCap: int
    eneReg: int
    heaCap: int
    heaCol: int
    phyRes: int
    expRes: int
    eleRes: int
    bulletsCap: int
    rocketsCap: int
    walk: int
    jump: int


class AnyStatsMapping(AnyMechStatsMapping, total=False):
    """Mapping of all possible stat keys findable on an item."""
    # stats sorted in order they appear in-game
    phyDmg: ValueRange
    phyResDmg: int
    eleDmg: ValueRange
    eneDmg: int
    eneCapDmg: int
    eneRegDmg: int
    eleResDmg: int
    expDmg: ValueRange
    heaDmg: int
    heaCapDmg: int
    heaColDmg: int
    expResDmg: int
    # walk, jump
    range: ValueRange
    push: int
    pull: int
    recoil: int
    advance: int
    retreat: int
    uses: int
    backfire: int
    heaCost: int
    eneCost: int
    bulletsCost: int
    rocketsCost: int


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
    base_stats: AnyStatsMapping = field()
    """Stats of the item at level 1."""
    max_level_stats: AnyStatsMapping = field()
    """Stats of the item that change as it levels up, at max level."""
    next: tex.Self | None = field(default=None)
    """The next stage the item can transform into."""

    _last: tuple[int, AnyStatsMapping] = field(default=(-1, {}), init=False, repr=False)

    @property
    def max_level(self) -> int:
        """The maximum level this stage can reach, starting from 0."""
        return self.tier.max_level

    def at(self, level: int, /) -> AnyStatsMapping:
        """Returns the stats at given level.

        For convenience, levels follow the game logic; the lowest level is 1
        and the maximum is a multiple of 10 depending on tier.
        """
        level -= 1

        if level == self._last[0]:
            return self._last[1]

        max_level = self.tier.max_level

        if not 0 <= level <= max_level:
            raise ValueError(f"Level {level} outside range 1-{max_level+1}")

        if level == 0:
            return self.base_stats.copy()

        if level == max_level:
            return self.base_stats | self.max_level_stats

        weight = level / max_level
        stats = self.base_stats.copy()

        for key, value in dict_items_as(int | ValueRange, self.max_level_stats):
            base_value: int | ValueRange = stats[key]

            if isinstance(value, ValueRange):
                assert isinstance(base_value, ValueRange)
                stats[key] = lerp_vector(base_value, value, weight)

            else:
                assert not isinstance(base_value, ValueRange)
                stats[key] = lerp(base_value, value, weight)

        self._last = (level, stats.copy())
        return stats


def get_final_stage(stage: "TransformStage", /) -> "TransformStage":
    """Returns the final stage of transformation."""
    while stage.next is not None:
        stage = stage.next

    return stage


def max_stats(stage: "TransformStage", /) -> AnyStatsMapping:
    """Return the max stats."""
    stage = get_final_stage(stage)
    return stage.at(stage.max_level)
