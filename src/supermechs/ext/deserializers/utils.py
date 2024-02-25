import types
import typing
from collections import abc
from contextlib import suppress
from typing import TYPE_CHECKING, Any, Final, SupportsIndex

from typing_extensions import Self

from .errors import DataKeyError, DataTypeError

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

        # rich comparison is a bit finicky - neither returning True nor False makes full sense
        # so I'll just do what float("nan") does
        def rich_comp(self: object, _: int) -> bool:
            return False

        for lg in "lg":
            namespace[f"__{lg}t__"] = rich_comp
            namespace[f"__{lg}e__"] = rich_comp

        return super().__new__(cls, name, bases, namespace)


# we lie to type checker that the class is an int for ease of typing,
# but we don't want it to pass isinstance(obj, int) at runtime
# so that types like float don't take precedence with arithmetic operations
class Null(int if TYPE_CHECKING else object, metaclass=_NullMeta):
    __slots__ = ()

    def __str__(self) -> str:
        return "?"

    def __repr__(self) -> str:
        return "NaN"

    def __format__(self, _: str, /) -> str:
        return self.__str__()

    def __eq__(self, _: Any) -> bool:
        return False

    def __round__(self, _: SupportsIndex, /) -> Self:
        # round() on float("nan") raises ValueError and probably has a good reason to do so,
        # but for my purposes it is essential round() returns this object too
        return self


NULL: Final = Null()


def maybe_null(value: int | None, /) -> int:
    return NULL if value is None else value


def assert_type(
    type_: type[T],
    obj: object,
    /,
    *,
    at: tuple[Any, ...] = (),
    cast: bool = False,
) -> T:
    """Assert object is of given type.

    If cast is `True`, will attempt to cast to `type_` before failing.
    """
    if isinstance(type_, types.GenericAlias):
        type_ = typing.cast(type[T], typing.get_origin(type_))

    if isinstance(obj, type_):
        return obj

    if cast and not issubclass(type_, str):
        # we exclude string casting since anything can be casted to string
        with suppress(Exception):
            return type_(obj)

    raise DataTypeError(type(obj), type_, at=at)


def map_assert_type(
    type_: type[T],
    obj: abc.Iterable[object],
    /,
    *,
    at: tuple[Any, ...] = (),
    cast: bool = False,
) -> abc.Iterator[T]:
    """Lazily assert elements of an iterable are of given type."""
    for i, element in enumerate(obj):
        yield assert_type(type_, element, at=(*at, i), cast=cast)


@typing.overload
def assert_key(
    type_: type[str],
    obj: abc.Mapping[KT, object],
    /,
    key: KT,
    *,
    at: tuple[Any, ...] = (),
    cast: bool = False,
) -> str:
    ...


@typing.overload
def assert_key(
    type_: type[abc.Sequence[T]],
    obj: abc.Mapping[KT, object],
    /,
    key: KT,
    *,
    at: tuple[Any, ...] = (),
    cast: bool = False,
) -> abc.Sequence[T]:
    ...


@typing.overload
def assert_key(
    type_: type[T],
    obj: abc.Mapping[KT, object],
    /,
    key: KT,
    *,
    at: tuple[Any, ...] = (),
    cast: bool = False,
) -> T:
    ...


def assert_key(
    type_: type[T],
    obj: abc.Mapping[KT, object],
    /,
    key: KT,
    *,
    at: tuple[Any, ...] = (),
    cast: bool = False,
) -> T:
    """Assert key exists in mapping and its value is of given type."""
    try:
        value = obj[key]

    except KeyError:
        raise DataKeyError(key, at=at) from None

    if (
        (origin := typing.get_origin(type_)) is not None
        and issubclass(origin, abc.Sequence)
        and not issubclass(origin, str)
    ):
        value_type: type = typing.get_args(type_)[0]
        at = (*at, key)
        value = assert_type(typing.cast(type[abc.Sequence[Any]], origin), value, at=at, cast=cast)
        if value_type is Any:
            return typing.cast(T, value)
        return type_(map_assert_type(value_type, value, at=at, cast=cast))

    return assert_type(type_, value, at=(*at, key), cast=cast)


def wrap_unsafe(data: Any, /) -> abc.Mapping[str, Any]:
    # I type function's accepted data type properly, but want the type within its body
    # to be treated as unknown - various assertions should produce the concrete types
    return data
