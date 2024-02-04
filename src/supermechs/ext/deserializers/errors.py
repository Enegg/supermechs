import typing
from collections import abc
from typing import Final, TypeAlias

from attrs import define

from supermechs.errors import SMException

Typeish: TypeAlias = type[object] | None | tuple[type[object] | None, ...]

_TYPE_TO_NAME: Final[abc.Mapping[type | None, str]] = {
    int: "an integer",
    float: "a number",
    str: "a string",
    list: "an array",
    bool: "true/false",
    dict: "an object",
    None: "null",
}


def jsonify_type(type_: Typeish, /) -> str:
    if isinstance(type_, tuple):
        return " | ".join(map(jsonify_type, typing.get_args(type_)))

    return _TYPE_TO_NAME.get(type_, type_.__name__)


class DataError(SMException):
    """Common class for data parsing errors."""


class DataValueError(DataError):
    """Invalid value."""


@define
class DataTypeError(DataError):
    """Value of incorrect type."""

    received: Typeish
    expected: Typeish

    def __str__(self) -> str:
        return f"Expected {jsonify_type(self.expected)}, got {jsonify_type(self.received)}"


@define
class DataTypeAtKeyError(DataError):
    """Value in mapping of incorrect type."""

    parent: DataTypeError
    key: object

    def __str__(self) -> str:
        return f"{self.parent} at key {self.key!r}"


@define
class DataKeyError(DataError):
    """Mapping missing a required key."""

    key: object

    def __str__(self) -> str:
        return f"Mapping is missing a required key: {self.key!r}"


@define
class DataVersionError(DataValueError):
    """Data of unknown version."""

    received: object
    expected: object | None = None

    def __str__(self) -> str:
        msg = f"Data of unknown version: {self.received!r}"

        if self.expected is not None:
            msg += f"; expected at most {self.expected!r}"

        return msg
