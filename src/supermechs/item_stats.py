import logging
import typing as t
from itertools import chain

from attrs import define
from typing_extensions import Self

from .core import MAX_LVL_FOR_TIER, TransformRange
from .enums import Tier
from .typedefs import ItemDictVer1, ItemDictVer2, ItemDictVer3, RawMechStatsMapping, RawStatsMapping
from .typeshed import dict_items_as
from .utils import NaN

__all__ = ("ValueRange", "AnyMechStatsMapping", "AnyStatsMapping", "TierStats", "ItemStats")

LOGGER = logging.getLogger(__name__)


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

    @property
    def average(self) -> float:
        """Average of the value range."""
        if self.is_single:
            return self.lower
        return (self.lower + self.upper) / 2

    def __add__(self, value: tuple[int, int]) -> Self:
        return type(self)(self.lower + value[0], self.upper + value[1])

    def __mul__(self, value: int) -> Self:
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


def lerp_range(minor: ValueRange, major: ValueRange, weight: float) -> ValueRange:
    """Linear interpolation of two vector-like objects."""
    return ValueRange(*map(lerp, minor, major, (weight, weight)))


def iter_stat_keys_and_types() -> t.Iterator[tuple[str, type]]:
    import types

    for key, data_type in chain(
        t.get_type_hints(RawMechStatsMapping).items(), t.get_type_hints(RawStatsMapping).items()
    ):
        origin, args = t.get_origin(data_type), t.get_args(data_type)

        if origin is int:
            yield key, int

        elif origin in (types.UnionType, t.Union) and set(args).issubset((int, type(None))):
            yield key, int

        elif origin is list:
            yield key, list

        else:
            raise ValueError(f"Unexpected type for key {key!r} found: {data_type!r} ({origin})")


def transform_raw_stats(data: RawStatsMapping, *, strict: bool = False) -> AnyStatsMapping:
    """Ensures the data is valid by grabbing factual keys and type checking values.
    Transforms None values into NaNs."""
    final_stats: AnyStatsMapping = {}

    # TODO: implement extrapolation of missing data

    for key, data_type in iter_stat_keys_and_types():
        if key not in data:
            continue

        match data[key]:
            case int() | None as value if data_type is int:
                final_stats[key] = NaN if value is None else value

            case [int() | None as x, int() | None as y] if data_type is list:
                final_stats[key] = ValueRange(
                    NaN if x is None else x,
                    NaN if y is None else y,
                )

            case unknown:
                msg = f"Expected {data_type.__name__} on key '{key}', got {type(unknown)}"
                if strict:
                    raise TypeError(msg)

                LOGGER.warning(msg)

    return final_stats


@define
class TierStats:
    """Object representing stats of an item at particular tier."""

    tier: Tier
    base_stats: AnyStatsMapping
    max_level_stats: AnyStatsMapping

    def at(self, level: int) -> AnyStatsMapping:
        """Returns the stats at given level.

        For convenience, levels follow the game logic; the lowest level is 1
        and the maximum is a multiple of 10 depending on tier.
        """
        level -= 1
        max_level = MAX_LVL_FOR_TIER[self.tier]

        if not 0 <= level <= max_level:
            raise ValueError(f"Level {level} outside range 1-{max_level+1}")

        if level == 0:
            return self.base_stats.copy()

        if level == max_level:
            return self.max

        fraction = level / max_level

        stats: AnyStatsMapping = self.base_stats.copy()

        for key, value in dict_items_as(int | ValueRange, self.max_level_stats):
            base_value: int | ValueRange = stats[key]

            if isinstance(value, ValueRange):
                assert isinstance(base_value, ValueRange)
                stats[key] = lerp_range(base_value, value, fraction)

            else:
                assert not isinstance(base_value, ValueRange)
                stats[key] = lerp(base_value, value, fraction)

        return stats

    @property
    def max(self) -> AnyStatsMapping:
        """Return the max stats of the item."""
        return self.base_stats | self.max_level_stats


@define
class ItemStats:
    tier_bases: t.Mapping[Tier, AnyStatsMapping]
    max_stats: t.Mapping[Tier, AnyStatsMapping]

    def __getitem__(self, key: Tier) -> TierStats:
        base = AnyStatsMapping()

        for tier, tier_base in self.tier_bases.items():
            base |= tier_base

            if tier == key:
                break

            base |= self.max_stats.get(tier, {})

        return TierStats(
            tier=key,
            base_stats=base,
            max_level_stats=self.max_stats.get(key, {})
        )

    def __contains__(self, value: str | Tier | TransformRange) -> bool:
        # literal stat key
        if isinstance(value, str):
            for mapping in self.tier_bases.values():
                if value in mapping:
                    return True

            return False

        if isinstance(value, Tier):
            return value in self.tier_bases

        if isinstance(value, TransformRange):
            return value.min in self.tier_bases and value.max in self.tier_bases

        return False

    def has_any_of_stats(self, *stats: str, tier: Tier | None = None) -> bool:
        """Check if any of the stat keys appear in the item's stats.

        tier: if specified, checks only at that tier. Otherwise, checks all tiers.
        """
        if tier is not None:
            return not self.tier_bases[tier].keys().isdisjoint(stats)

        for mapping in self.tier_bases.values():
            if not mapping.keys().isdisjoint(stats):
                return True

        return False

    @classmethod
    def from_json_v1_v2(cls, data: ItemDictVer1 | ItemDictVer2, *, strict: bool = False) -> Self:
        tier = Tier.by_initial(data["transform_range"][-1])
        bases = {tier: transform_raw_stats(data["stats"], strict=strict)}
        max_stats = {}
        return cls(bases, max_stats)

    @classmethod
    def from_json_v3(cls, data: ItemDictVer3, *, strict: bool = False) -> Self:
        tier_bases = dict[Tier, AnyStatsMapping]()
        max_stats = dict[Tier, AnyStatsMapping]()
        hit = False

        for rarity in Tier:
            key = t.cast(str, rarity.name.lower())

            if key not in data:
                # if we already populated the dict with stats,
                # missing key means we should break as there will be no further stats
                if hit:
                    break

                # otherwise, we haven't yet got to the starting tier, so continue
                continue

            hit = True
            tier_bases[rarity] = transform_raw_stats(data[key], strict=strict)

            try:
                max_level_data = data["max_" + key]

            except KeyError:
                if rarity is not Tier.DIVINE:
                    if strict:
                        raise

                    LOGGER.warning(f"max_{key} key not found for item {data['name']}")

                max_stats[rarity] = {}

            else:
                max_stats[rarity] = transform_raw_stats(max_level_data, strict=strict)

        return cls(tier_bases, max_stats)
