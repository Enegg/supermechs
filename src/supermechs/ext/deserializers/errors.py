import types
import typing
from collections import abc
from enum import Enum

from attrs import define, field
from exceptiongroup import ExceptionGroup

from supermechs.errors import SMException

DataPath: typing.TypeAlias = abc.Sequence[str | int]  # keys or indices
Typeish: typing.TypeAlias = type[object] | None
DataErrorGroup: typing.TypeAlias = "DataError | ExceptionGroup[DataErrorGroup]"


_TYPE_TO_NAME: abc.Mapping[type, str] = {
    int: "an integer",
    float: "a floating point number",
    str: "a string",
    list: "an array",
    bool: "true/false",
    dict: "an object",
}


def jsonify_type(type_: Typeish, /) -> str:
    if type_ is None:
        return "null"

    if issubclass(type_, Enum):
        return f"one of {', '.join(e.name for e in type_)}"

    return _TYPE_TO_NAME.get(type_, type_.__name__)


@define
class Catch:
    issues: abc.MutableSequence[DataErrorGroup] = field(factory=list)

    def add(self, exc: DataErrorGroup, /) -> None:
        self.issues.append(exc)

    def checkpoint(self, msg: str = "") -> None:
        if self.issues:
            raise ExceptionGroup[DataErrorGroup](msg, self.issues) from None

    def __enter__(self) -> None:
        pass

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        tb: types.TracebackType | None,
        /,
    ) -> bool | None:
        if isinstance(exc_value, DataError | ExceptionGroup):
            self.add(exc_value)  # type: ignore[reportUnknownArgumentType]
            return True


@define
class DataError(SMException):
    """Common class for data parsing errors."""

    at: DataPath = field(default=(), kw_only=True)

    @property
    def path(self) -> str:
        if not self.at:
            return ""
        at = iter(self.at)
        path0 = next(at)
        path = "".join(f"[{i}]" if isinstance(i, int) else f".{i}" for i in at)
        return f"{path0}{path}: "


@define
class DataValueError(DataError):
    """Invalid value."""

    msg: str

    def __str__(self) -> str:
        return f"{self.path}{self.msg}"


@define
class DataTypeError(DataError):
    """Value of incorrect type."""

    received: Typeish | str
    expected: Typeish

    def __str__(self) -> str:
        received = (
            repr(self.received) if isinstance(self.received, str) else jsonify_type(self.received)
        )
        return f"{self.path}Expected {jsonify_type(self.expected)}, got {received}"


@define
class DataKeyError(DataError):
    """Mapping missing a required key."""

    key: object

    def __str__(self) -> str:
        return f"{self.path}Mapping is missing a required key: {self.key!r}"


@define
class DataVersionError(DataError):
    """Data of unknown version."""

    received: object
    expected: object | None = None

    def __str__(self) -> str:
        msg = f"{self.path}Unknown version: {self.received!r}"

        if self.expected is not None:
            msg += f"; expected at most {self.expected!r}"

        return msg
