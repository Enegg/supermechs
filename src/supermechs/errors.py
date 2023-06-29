from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    from .models.inv_item import InvItem


class SMException(Exception):
    """Base class for game exceptions."""


class MalformedData(SMException):
    """Data of invalid type or missing values."""

    data: t.Any

    def __init__(self, msg: str | None = None, data: t.Any = None) -> None:
        super().__init__(msg or self.__doc__)
        self.data = data


class UnknownDataVersion(SMException):
    """Data of version not parseable by the library."""

    msg: t.ClassVar[str] = "Unknown {obj} version: {ver!r}"

    def __init__(
        self, related_object: str | type, version: str | int, expected: str | int | None = None
    ) -> None:
        if isinstance(related_object, type):
            related_object = related_object.__name__

        msg = self.msg.format(obj=related_object, ver=version)

        if expected is not None:
            msg += f"\nExpected at most: {expected}"

        super().__init__(msg)


class MaxPowerError(SMException):
    """Attempted to add power to an already maxed item."""

    def __init__(self, item: InvItem) -> None:
        super().__init__(f"Maximum power for item {item.name!r} already reached")


class MaxTierError(SMException):
    """Attempted to transform an item at its maximum tier."""

    def __init__(self, item: InvItem) -> None:
        super().__init__(f"Maximum tier for item {item.name!r} already reached")
