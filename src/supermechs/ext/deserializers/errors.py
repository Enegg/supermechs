import typing
from collections import abc
from typing import Final, TypeAlias

from attrs import define

from supermechs.errors import SMException

Typeish: TypeAlias = type[object] | None | tuple[type[object] | None, ...]

_TYPE_TO_NAME: Final[abc.Mapping[type, str]] = {
    int: "an integer",
    float: "a floating point number",
    str: "a string",
    list: "an array",
    bool: "true/false",
    dict: "an object",
}


def jsonify_type(type_: Typeish, /) -> str:
    if isinstance(type_, tuple):
        return " | ".join(map(jsonify_type, typing.get_args(type_)))

    if type_ is None:
        return "null"

    return _TYPE_TO_NAME.get(type_, type_.__name__)


@define(kw_only=True)
class DataError(SMException):
    """Common class for data parsing errors."""

    at: tuple[object, ...] = ()

    @property
    def ats(self) -> str:
        return f'At {".".join(map(str, self.at))}: ' if self.at else ""


@define
class DataValueError(DataError):
    """Invalid value."""

    msg: str

    def __str__(self) -> str:
        return f"{self.ats}{self.msg}"


@define
class DataTypeError(DataError):
    """Value of incorrect type."""

    received: Typeish
    expected: Typeish

    def __str__(self) -> str:
        return (
            f"{self.ats}Expected {jsonify_type(self.expected)}, got {jsonify_type(self.received)}"
        )


@define
class DataKeyError(DataError):
    """Mapping missing a required key."""

    key: object

    def __str__(self) -> str:
        return f"{self.ats}Mapping is missing a required key: {self.key!r}"


@define
class DataVersionError(DataError):
    """Data of unknown version."""

    received: object
    expected: object | None = None

    def __str__(self) -> str:
        msg = f"{self.ats}Unknown version: {self.received!r}"

        if self.expected is not None:
            msg += f"; expected at most {self.expected!r}"

        return msg
