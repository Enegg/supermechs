from collections import abc
from contextlib import suppress
from typing import TYPE_CHECKING, Any, Final, SupportsIndex
from typing_extensions import Self

from .errors import DataKeyError, DataTypeAtKeyError, DataTypeError

from supermechs.typeshed import KT, T


def js_format(string: str, /, **keys: object) -> str:
    """Format a JavaScript style string %template% using given keys and values."""
    # XXX: this will do as many passes as there are kwargs, maybe concatenate the pattern?
    import re

    for key, value in keys.items():
        string = re.sub(rf"%{re.escape(key)}%", str(value), string)

    return string


class _NullMeta(type):
    def __new__(cls, name: str, bases: tuple[type, ...], namespace: dict[str, Any]):
        def func(self: T, _: int) -> T:
            return self

        for dunder in ("add", "sub", "mul", "truediv", "floordiv", "mod", "pow"):
            namespace[f"__{dunder}__"] = func
            namespace[f"__r{dunder}__"] = func

        return super().__new__(cls, name, bases, namespace)


class Null(int if TYPE_CHECKING else object, metaclass=_NullMeta):
    __slots__ = ()

    def __str__(self) -> str:
        return "?"

    def __repr__(self) -> str:
        return "NaN"

    def __format__(self, _: str, /) -> str:
        return "?"

    def __eq__(self, _: Any) -> bool:
        return False

    def __lt__(self, _: Any) -> bool:
        return False

    def __round__(self, _: SupportsIndex, /) -> Self:
        # round() on float("nan") raises ValueError and probably has a good reason to do so,
        # but for my purposes it is essential round() returns this object too
        return self


NULL: Final = Null()


def maybe_null(value: int | None, /) -> int:
    return NULL if value is None else value


def assert_type(type_: type[T], value: object, /, *, cast: bool = True) -> T:
    """Assert value is of given type.

    If cast is `True`, will attempt to cast to `type_` before failing.
    """
    if isinstance(value, type_):
        return value

    if cast and not issubclass(type_, str):
        # we exclude string casting since anything can be casted to string
        with suppress(Exception):
            return type_(value)

    raise DataTypeError(type(value), type_)
