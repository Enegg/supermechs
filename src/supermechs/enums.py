from __future__ import annotations

import typing as t
from enum import Enum, auto, IntEnum


__all__ = ("Tier", "Element", "Type")


class Tier(IntEnum):
    """Enumeration of item tiers."""

    _short_names2members: t.ClassVar[dict[str, Tier]]

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
    def from_letter(cls, letter: str) -> Tier:
        """Get enum member by the first letter of its name."""
        return cls._short_names2members[letter.upper()]


Tier._short_names2members = {tier.name[0]: tier for tier in Tier}


class Element(Enum):
    """Enumeration of item elements."""

    # fmt: off
    PHYSICAL  = auto()
    EXPLOSIVE = auto()
    ELECTRIC  = auto()
    COMBINED  = auto()
    UNKNOWN   = auto()
    # fmt: on


class Type(Enum):
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
    TELE = TELEPORTER
    # SHIELD, PERK, KIT?
    # fmt: on
