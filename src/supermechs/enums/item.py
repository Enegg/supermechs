from enum import auto, unique

from ._base import PartialEnum

__all__ = ("Element", "Type")


@unique
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
    SHIELD      = auto()
    PERK        = auto()
    MODULE      = auto()
    CHARGE_ENGINE = CHARGE
    GRAPPLING_HOOK = HOOK
    TELEPORT = TELEPORTER
    # fmt: on
