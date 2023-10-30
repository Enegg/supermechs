import typing as t
import typing_extensions as tex
from enum import auto

from ..utils import PartialEnum

__all__ = ("Tier", "Element", "Type", "Stat")


class Tier(int, PartialEnum):
    """Enumeration of item tiers."""

    # fmt: off
    COMMON    = auto()
    RARE      = auto()
    EPIC      = auto()
    LEGENDARY = auto()
    MYTHICAL  = auto()
    DIVINE    = auto()
    PERK      = auto()
    # fmt: on

    _initials2members: t.ClassVar[t.Mapping[str, tex.Self]]

    @classmethod
    def of_initial(cls, letter: str, /) -> tex.Self:
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
    SHIELD      = auto()
    PERK        = auto()
    CHARGE_ENGINE = CHARGE
    GRAPPLING_HOOK = HOOK
    TELEPORT = TELEPORTER
    # fmt: on


class Stat(int, PartialEnum):
    """Enumeration of item stats."""

    # fmt: off
    # summary stats
    weight                      = auto()
    hit_points                  = auto()
    energy_capacity             = auto()
    regeneration                = auto()
    heat_capacity               = auto()
    cooling                     = auto()
    bullets_capacity            = auto()
    rockets_capacity            = auto()
    physical_resistance         = auto()
    explosive_resistance        = auto()
    electric_resistance         = auto()
    # physical weapons
    physical_damage             = auto()
    physical_damage_addon       = auto()
    physical_resistance_damage  = auto()
    # energy weapons
    electric_damage             = auto()
    electric_damage_addon       = auto()
    energy_damage               = auto()
    energy_capacity_damage      = auto()
    regeneration_damage         = auto()
    electric_resistance_damage  = auto()
    # heat weapons
    explosive_damage            = auto()
    explosive_damage_addon      = auto()
    heat_damage                 = auto()
    heat_capacity_damage        = auto()
    cooling_damage              = auto()
    explosive_resistance_damage = auto()
    # mobility
    walk                        = auto()
    jump                        = auto()
    range                       = auto()
    range_addon                 = auto()
    push                        = auto()
    pull                        = auto()
    recoil                      = auto()
    advance                     = auto()
    retreat                     = auto()
    # costs
    uses                        = auto()
    backfire                    = auto()
    heat_generation             = auto()
    energy_cost                 = auto()
    bullets_cost                = auto()
    rockets_cost                = auto()
    # fmt: on
