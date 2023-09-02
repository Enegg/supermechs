import typing as t

if t.TYPE_CHECKING:
    from .models.item import InvItem


class SMException(Exception):
    """Base class for game exceptions."""


class InvalidValue(SMException):
    """Value of incorrect type."""

    type_to_name: t.ClassVar[t.Mapping[type, str]] = {
        int: "an integer", float: "a number", str: "a string", list: "an array", bool: "a boolean"
    }

    def __init__(self, value: object, expected: type) -> None:
        fmt = f"Expected {self.name_of(expected)}, got {self.name_of(type(value))}"
        super().__init__(fmt)

    @classmethod
    def name_of(cls, type_: type) -> str:
        return cls.type_to_name.get(type_, type_.__name__)


class InvalidKeyValue(InvalidValue):
    """Invalid value at key."""

    def __init__(self, value: object, expected: type, key: str) -> None:
        super().__init__(value, expected)
        self.args = (f"{self.args[0]} at key {key!r}",)


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

    def __init__(self, inv_item: "InvItem", /) -> None:
        super().__init__(f"Maximum power for item {inv_item.item.data.name!r} already reached")


class MaxTierError(SMException):
    """Attempted to transform an item at its maximum tier."""

    def __init__(self, inv_item: "InvItem", /) -> None:
        super().__init__(f"Maximum tier for item {inv_item.item.data.name!r} already reached")
