from attrs import define

from .typeshed import ItemID, PackKey

__all__ = (
    "IDLookupError",
    "MaxPowerError",
    "MaxTierError",
    "NegativeValueError",
    "OutOfRangeError",
    "PackKeyError",
    "SMException",
)


class SMException(Exception):
    """Base class for library exceptions."""


@define
class OutOfRangeError(SMException, ValueError):
    """Value outside allowed range."""

    lower: float
    number: float
    upper: float

    def __str__(self) -> str:
        return f"Value {self.number} out of range; {self.lower} ≤ X ≤ {self.upper}"


@define
class NegativeValueError(SMException, ValueError):
    """Number cannot be negative."""

    number: float

    def __str__(self) -> str:
        return f"Number cannot be negative, got {self.number}"


@define
class IDLookupError(SMException, KeyError):
    """Unknown item ID."""

    id: ItemID

    def __str__(self) -> str:
        return f"Unknown item ID: {self.id}"


@define
class PackKeyError(SMException, KeyError):
    """Unknown pack key."""

    key: PackKey

    def __str__(self) -> str:
        return f"Unknown pack key: {self.key}"


class MaxPowerError(SMException):
    """Item at maximum power."""

    def __init__(self, arg: object = __doc__, *args: object) -> None:
        super().__init__(arg, *args)


class MaxTierError(SMException):
    """Attempted to transform an item at its maximum tier."""

    def __init__(self, /) -> None:
        super().__init__("Maximum item tier already reached")
