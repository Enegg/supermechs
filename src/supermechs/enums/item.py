from enum import auto, unique

from ._base import PartialEnum

__all__ = ("ElementEnum", "TypeEnum")


@unique
class ElementEnum(str, PartialEnum):
    """Enumeration of item elements."""

    # fmt: off
    PHYSICAL  = auto()
    EXPLOSIVE = auto()
    ELECTRIC  = auto()
    COMBINED  = auto()
    # fmt: on
    pass


class TypeEnum(str, PartialEnum):
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
    KIT         = auto()
    CHARGE_ENGINE = CHARGE
    # fmt: on
