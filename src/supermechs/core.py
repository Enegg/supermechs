from __future__ import annotations

import typing as t
from pathlib import Path
from types import MappingProxyType

from attrs import frozen
from typing_extensions import Self

from .enums import Tier
from .platform import json_decoder
from .typedefs import AnyMechStatKey, AnyStatKey, Name, StatData
from .utils import MISSING, is_pascal

__all__ = ("WORKSHOP_STATS", "STATS", "TransformRange", "Stat")


WORKSHOP_STATS: tuple[str, ...] = t.get_args(AnyMechStatKey)
"""The stats that can appear in mech summary, in order."""

MAX_LVL_FOR_TIER = {tier: level for tier, level in zip(Tier, range(9, 50, 10))} | {Tier.DIVINE: 0}
"""A mapping of a tier to the maximum level an item can have at this tier.
    Note that in game levels start at 1.
"""


class Names(t.NamedTuple):
    default: str
    in_game: str = MISSING
    short: str = MISSING

    def __str__(self) -> str:
        return self.default

    def __format__(self, __format_spec: str, /) -> str:
        return self.default.__format__(__format_spec)

    @property
    def game_name(self) -> str:
        return self.default if self.in_game is MISSING else self.in_game

    @property
    def short_name(self) -> str:
        if self.short is not MISSING:
            return self.short

        return self.default if len(self.default) <= len(self.game_name) else self.game_name


# TODO: make this locale aware
class Stat(t.NamedTuple):
    key: str
    beneficial: bool = True
    buff: t.Literal["+", "+%", "-%", "+2%"] | None = None

    def __str__(self) -> str:
        return self.key

    def __hash__(self) -> int:
        return hash((self.key, type(self)))

    @classmethod
    def from_dict(cls, json: StatData, key: str) -> Self:
        return cls(
            key=key,
            beneficial=json.get("beneficial", True),
            buff=json.get("buff", None),
        )


def _load_stats():
    with (Path(__file__).parent / "static/StatData.json").open() as file:
        json: dict[AnyStatKey, StatData] = json_decoder(file.read())

    return {stat_key: Stat.from_dict(value, stat_key) for stat_key, value in json.items()}


STATS: t.Mapping[str, Stat] = MappingProxyType(_load_stats())


@frozen
class TransformRange:
    """Represents a range of transformation tiers an item can have."""

    range: range

    def __str__(self) -> str:
        return f"{self.min.name[0]}-{self.max.name[0]}"

    def __iter__(self) -> t.Iterator[Tier]:
        return map(Tier.get_by_value, self.range)

    def __len__(self) -> int:
        return len(self.range)

    def __contains__(self, item: Tier) -> bool:
        if isinstance(item, Tier):
            return item.value in self.range

        return NotImplemented

    @property
    def min(self) -> Tier:
        """Lower range bound."""
        return Tier.get_by_value(self.range.start)

    @property
    def max(self) -> Tier:
        """Upper range bound."""
        return Tier.get_by_value(self.range.stop - 1)

    @classmethod
    def from_tiers(cls, lower: Tier | int, upper: Tier | int | None = None) -> Self:
        """Construct a TransformRange object from upper and lower bounds.
        Unlike `range` object, upper bound is inclusive."""

        if isinstance(lower, int):
            lower = Tier.get_by_value(lower)

        if upper is None:
            upper = lower

        elif isinstance(upper, int):
            upper = Tier.get_by_value(upper)

        if lower > upper:
            raise ValueError("Upper tier below lower tier")

        return cls(range(lower.value, upper.value + 1))

    @classmethod
    def from_string(cls, string: str, /) -> Self:
        """Construct a TransformRange object from a string like "C-E" or "M"."""
        up, _, down = string.strip().partition("-")

        if down:
            return cls.from_tiers(Tier.by_initial(up), Tier.by_initial(down))

        return cls.from_tiers(Tier.by_initial(up))


def abbreviate_name(name: Name, /) -> str | None:
    """Returns an acronym of the name, or None if one cannot (shouldn't) be made.

    The acronym consists of capital letters in item's name;
    it will not be made for non-PascalCase single-word names, or names which themselves
    are an acronym for something (like EMP).
    """
    if is_pascal(name):
        # check if there is at least one more capital letter aside from first one
        if name[1:].islower():
            return None
    # at this point, we still need to filter out names like "EMP"
    if name.isupper():
        return None
    # Overloaded EMP is fine to make an abbreviation for though
    return "".join(filter(str.isupper, name)).lower()


def abbreviate_names(names: t.Iterable[Name], /) -> dict[str, set[Name]]:
    """Returns dict of abbrevs: EFA => Energy Free Armor"""
    abbreviations_to_names: dict[str, set[Name]] = {}

    for name in names:
        if len(name) < 8:
            continue

        is_single_word = " " not in name

        if (IsNotPascal := not name.isupper() and name[1:].islower()) and is_single_word:
            continue

        abbreviations = {"".join(a for a in name if a.isupper()).lower()}

        if not is_single_word:
            abbreviations.add(name.replace(" ", "").lower())  # Fire Fly => firefly

        if not IsNotPascal and is_single_word:  # takes care of PascalCase names
            last = 0
            for i, a in enumerate(name):
                if a.isupper():
                    if string := name[last:i].lower():
                        abbreviations.add(string)

                    last = i

            abbreviations.add(name[last:].lower())

        for abbreviation in abbreviations:
            if (bucket := abbreviations_to_names.get(abbreviation)) is not None:
                bucket.add(name)

            else:
                abbreviations_to_names[abbreviation] = {name}

    return abbreviations_to_names


def next_tier(current: Tier, /) -> Tier:
    """Returns the next tier in line."""
    return Tier.get_by_value(current.value + 1)
