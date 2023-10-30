import typing as t

from supermechs.errors import SMException


class DataError(SMException):
    """Common class for data parsing errors."""


class DataValueError(DataError):
    """Invalid value."""


class DataTypeError(DataError):
    """Value of incorrect type."""

    type_to_name: t.Final[t.Mapping[type, str]] = {
        int: "an integer",
        float: "a number",
        str: "a string",
        list: "an array",
        bool: "a boolean",
    }

    def __init__(self, value: type, expected: type, /, *args: t.Any) -> None:
        super().__init__(self.format_value(value, expected, *args))

    @classmethod
    def format_value(cls, *args: t.Any) -> str:
        expected, value, *_ = args
        return f"Expected {cls.name_of(expected)}, got {cls.name_of(type(value))}"

    @classmethod
    def name_of(cls, type_: type, /) -> str:
        return cls.type_to_name.get(type_, type_.__name__)


class DataTypeAtKeyError(DataTypeError):
    """Value in mapping of incorrect type."""

    if t.TYPE_CHECKING:
        def __init__(self, value: type, expected: type, key: str, /, *args: t.Any) -> None:
            ...

    @classmethod
    def format_value(cls, *args: t.Any) -> str:
        return super().format_value(args) + f" at key {args[2]!r}"


class DataKeyError(DataError):
    """Mapping is missing a required key: {key!r}."""

    def __init__(self, key_err: KeyError, /) -> None:
        """Mapping is missing a required key: {key!r}."""
        super().__init__(t.cast(str, self.__doc__).format(key=str(key_err)))


class DataVersionError(DataValueError):
    """Data of unknown version: {ver!r}"""

    def __init__(self, version: t.Any, expected: t.Any | None = None) -> None:
        """Data of unknown version: {ver!r}"""
        msg = t.cast(str, self.__doc__).format(ver=version)

        if expected is not None:
            msg += f"; expected at most {expected!r}"

        super().__init__(msg)
