from __future__ import annotations

import typing as t
from enum import Enum, auto

from typing_extensions import Self

__all__ = ("Tier", "Element", "Type")


class PartialEnum(Enum):
    @classmethod
    def get_by_name(cls, name: str, /) -> Self:
        """Get enum member by name."""
        return cls[name]

    @classmethod
    def get_by_value(cls, value: t.Any, /) -> Self:
        """Get enum member by value."""
        return cls.__call__(value)


class Tier(int, PartialEnum):
    """Enumeration of item tiers."""

    _initials2members: t.ClassVar[t.Mapping[str, Tier]]

    # fmt: off
    COMMON    = auto()
    RARE      = auto()
    EPIC      = auto()
    LEGENDARY = auto()
    MYTHICAL  = auto()
    DIVINE    = auto()
    PERK      = auto()
    # fmt: on

    @classmethod
    def by_initial(cls, letter: str, /) -> Tier:
        """Get enum member by the first letter of its name."""
        return cls._initials2members[letter.upper()]


Tier._initials2members = {tier.name[0]: tier for tier in Tier}


class Element(PartialEnum):
    """Enumeration of item elements."""

    # fmt: off
    PHYSICAL  = auto()
    EXPLOSIVE = auto()
    ELECTRIC  = auto()
    COMBINED  = auto()
    UNKNOWN   = auto()
    # fmt: on


class Type(PartialEnum):
    """Enumeration of item types."""

    # fmt: off
    TORSO       = auto()
    LEGS        = auto()
    DRONE       = auto()
    SIDE_WEAPON = auto()
    TOP_WEAPON  = auto()
    TELEPORTER  = auto()
    CHARGE      = auto()
    HOOK        = auto()
    MODULE      = auto()
    CHARGE_ENGINE = CHARGE
    GRAPPLING_HOOK = HOOK
    TELEPORT = TELEPORTER
    # SHIELD, PERK, KIT?
    # fmt: on
