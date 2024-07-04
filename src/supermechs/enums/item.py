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
    pass


# TODO: this belongs to ext
@unique
class TagEnum(str, PartialEnum):
    # fmt: off
    premium      = auto()
    """Whether the item is considered "premium"."""
    sword        = auto()
    """Whether the item "swings" in its animation."""
    melee        = auto()
    """Whether the item is a melee weapon."""
    roller       = auto()
    """Specific to legs, whether they roll or walk."""
    legacy       = auto()
    """Whether the item is considered legacy."""
    require_jump = auto()
    """Whether the item requires the ability to jump to be equipped."""
    custom       = auto()
    """Whether the item is not from the default item pack."""
    # fmt: on
    pass
