import types
import typing
from collections import abc
from enum import Enum

from attrs import define, field

from ._compat import DataErrorGroup

from supermechs.exceptions import SMException

if typing.TYPE_CHECKING:
    from exceptiongroup import ExceptionGroup

DataPath: typing.TypeAlias = abc.Sequence[str | int]  # keys or indices
Typeish: typing.TypeAlias = type[object] | None
DataErrorType: typing.TypeAlias = "DataError | ExceptionGroup[DataErrorType]"

_TYPE_TO_NAME: abc.Mapping[type, str] = {
    int: "an integer",
    float: "a number",
    str: 'a string "…"',
    list: "an array […]",
    bool: "true/false",
    dict: "an object {…}",
}


def jsonify_type(type_: Typeish, /) -> str:
    if type_ is None:
        return "null"

    if issubclass(type_, Enum):
        return f"one of {', '.join(e.name for e in type_)}"

    return _TYPE_TO_NAME.get(type_, type_.__name__)


@define
class Catch:
    issues: abc.MutableSequence[DataErrorType] = field(factory=list)

    def add(self, exc: DataErrorType, /) -> None:
        self.issues.append(exc)

    def checkpoint(self, msg: str = "") -> None:
        if self.issues:
            raise DataErrorGroup(msg, self.issues) from None

    def __enter__(self) -> None:
        pass

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        tb: types.TracebackType | None,
        /,
    ) -> bool | None:
        if isinstance(exc_value, DataError | DataErrorGroup):
            self.add(exc_value)
            return True


@define
class OutOfRangeError(SMException, IndexError):
    """Value outside allowed range.

    Note: both lower and upper bounds are inclusive.
    """

    lower: float
    number: float
    upper: float

    def __str__(self) -> str:
        return f"Value {self.number} outside range {self.lower}…{self.upper}"

    @classmethod
    def check(cls, lower: float, number: float, upper: float) -> None:
        if not lower <= number <= upper:
            raise cls(lower, number, upper) from None


@define
class DataError(SMException):
    """Common class for data parsing errors."""

    at: DataPath = field(default=(), kw_only=True)
    msg: str = field(default="", init=False)

    @property
    def path(self) -> str:
        if not self.at:
            return ""
        at = iter(self.at)
        path0 = next(at)
        path = "".join(f"[{i}]" if isinstance(i, int) else f".{i}" for i in at)
        return f"At {path0}{path}: "

    def __str__(self) -> str:
        return f"{self.path}{self.msg}"


@define
class DataValueError(DataError):
    """Invalid value."""

    msg: str


@define
class DataTypeError(DataError):
    """Value of incorrect type."""

    received: Typeish | str
    expected: Typeish

    def __attrs_post_init__(self) -> None:
        received = (
            repr(self.received) if isinstance(self.received, str) else jsonify_type(self.received)
        )
        self.msg = f"Expected {jsonify_type(self.expected)}, got {received}"


@define
class DataKeyError(DataError):
    """Mapping missing a required key."""

    key: object

    def __attrs_post_init__(self) -> None:
        self.msg = f"Mapping is missing a required key: {self.key!r}"


@define
class DataVersionError(DataError):
    """Data of unknown version."""

    received: object
    expected: object | None = None

    def __attrs_post_init__(self) -> None:
        self.msg = f"Unknown version: {self.received!r}"

        if self.expected is not None:
            self.msg += f"; expected at most {self.expected!r}"
