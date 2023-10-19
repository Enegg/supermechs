import typing as t

if t.TYPE_CHECKING:
    from .item import InvItem


class SMException(Exception):
    """Base class for library exceptions."""


class CantBeNegative(SMException):
    """{number} is negative"""

    def __init__(self, number: t.SupportsFloat, /) -> None:
        super().__init__(t.cast(str, self.__doc__).format(number=number))


class UnknownID(SMException):
    """Unknown item ID"""

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class MaxPowerError(SMException):
    """Item at maximum power"""

    def __init__(self, arg: object = __doc__, *args: object) -> None:
        super().__init__(arg, *args)


class MaxTierError(SMException):
    """Attempted to transform an item at its maximum tier."""

    def __init__(self, inv_item: "InvItem", /) -> None:
        super().__init__(f"Maximum tier for item {inv_item.item.data.name!r} already reached")
