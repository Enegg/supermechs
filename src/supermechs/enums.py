from __future__ import annotations

import typing as t
from enum import Enum, auto
from typing_extensions import Self

__all__ = ("Tier", "Element", "Type")


class PartialEnum(Enum):
    def __repr__(self) -> str:
        return str(self)

    @classmethod
    def of_name(cls, name: str, /) -> Self:
        """Get enum member by name."""
        return cls[name]

    @classmethod
    def of_value(cls, value: t.Any, /) -> Self:
        """Get enum member by value."""
        return cls.__call__(value)


class TierData(t.NamedTuple):
    order: int
    max_level: int

    def __int__(self) -> int:
        return self.order


class Tier(TierData, PartialEnum):
    """Enumeration of item tiers."""

    _initials2members: t.ClassVar[t.Mapping[str, Tier]]

    def __new__(cls, order: int, max_level: int) -> Self:
        self = t.cast(Self, TierData.__new__(cls, order, max_level))
        self._value_ = order
        return self

    # fmt: off
    COMMON    = (0, 9)
    RARE      = (1, 19)
    EPIC      = (2, 29)
    LEGENDARY = (3, 39)
    MYTHICAL  = (4, 49)
    DIVINE    = (5, 0)
    PERK      = (6, 0)
    # fmt: on

    @classmethod
    def of_initial(cls, letter: str, /) -> Tier:
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
