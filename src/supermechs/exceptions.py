from attrs import define

from .abc.item import ItemID
from .abc.item_pack import PackKey
from .enums.stats import Tier

__all__ = (
    "IDLookupError",
    "MaxPowerError",
    "MaxTierError",
    "NegativeValueError",
    "PackKeyError",
    "SMException",
    "TierUnreachableError",
)


class SMException(Exception):
    """Base class for library exceptions."""

    __slots__ = ()


@define(auto_exc=True)
class NegativeValueError(SMException, ValueError):
    """Number cannot be negative."""

    number: float

    def __str__(self) -> str:
        return f"Number cannot be negative, got {self.number}"


@define(auto_exc=True)
class IDLookupError(SMException, KeyError):
    """Unknown item ID."""

    id: ItemID

    def __str__(self) -> str:
        return f"Unknown item ID: {self.id}"


@define(auto_exc=True)
class PackKeyError(SMException, KeyError):
    """Unknown pack key."""

    key: PackKey

    def __str__(self) -> str:
        return f"Unknown pack key: {self.key}"


class MaxPowerError(SMException):
    """Item at maximum power."""

    __slots__ = ()

    def __init__(self, arg: object = __doc__, *args: object) -> None:
        super().__init__(arg, *args)


class MaxTierError(SMException):
    """Attempted to transform an item at its maximum tier."""

    __slots__ = ()

    def __init__(self) -> None:
        super().__init__("Maximum item tier already reached")


@define(auto_exc=True)
class TierUnreachableError(SMException):
    """Tier outside item transformation tiers."""

    tier: Tier

    def __str__(self) -> str:
        return f"Item has no {self.tier.name} tier"
