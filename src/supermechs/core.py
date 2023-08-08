from __future__ import annotations

import typing as t
from types import MappingProxyType

from typing_extensions import Self

from . import _internal
from .utils import is_pascal

if t.TYPE_CHECKING:
    from .typedefs import Name, StatData

__all__ = ("STATS", "Stat")


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


STATS: t.Mapping[str, Stat] = MappingProxyType(_internal.STATS)


def abbreviate_name(name: Name, /) -> str | None:
    """Returns an acronym of the name, or None if one cannot (shouldn't) be made.

    The acronym consists of capital letters in item's name;
    it will not be made for non-PascalCase single-word names, or names which themselves
    are an acronym for something (like EMP).
    """
    if is_pascal(name):
        # cannot make an abbrev from a single capital letter
        if name[1:].islower():
            return None
    # filter out already-acronym names, like "EMP"
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
