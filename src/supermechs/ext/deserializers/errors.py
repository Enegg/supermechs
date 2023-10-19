import typing as t

from supermechs.errors import SMException


class DataParseError(SMException):
    """Failed to parse data."""

    def __init__(self, arg: object = __doc__, *args: object) -> None:
        super().__init__(arg, *args)


class InvalidType(SMException):
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


class InvalidKeyValueType(InvalidType):
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


class MissingRequiredKey(MalformedData):
    """Mapping is missing required key: {key!r}."""

    def __init__(self, key: t.Any, /) -> None:
        super().__init__(t.cast(str, self.__doc__).format(key=key))


class UnknownDataVersion(SMException):
    """Data of version not parseable by the library."""

    msg: t.ClassVar[str] = "Unknown {obj} version: {ver!r}"

    def __init__(
        self, related_object: str | type, version: t.Any, expected: t.Any | None = None
    ) -> None:
        if isinstance(related_object, type):
            related_object = related_object.__name__

        msg = self.msg.format(obj=related_object, ver=version)

        if expected is not None:
            msg += f"\nExpected at most: {expected}"

        super().__init__(msg)
