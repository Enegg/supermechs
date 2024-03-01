import typing
import typing_extensions as typing_
from collections import abc

from .errors import Catch, DataKeyError, DataPath, DataTypeError

from supermechs.enums._base import PartialEnum
from supermechs.typeshed import T

JSON_KT = typing_.TypeVar("JSON_KT", str, int, infer_variance=True)
E = typing_.TypeVar("E", bound=PartialEnum, infer_variance=True)
Ts = typing_.TypeVarTuple("Ts")


def js_format(string: str, /, **keys: object) -> str:
    """Format a JavaScript style string %template% using given keys and values."""
    # XXX: this will do as many passes as there are kwargs, maybe concatenate the pattern?
    import re

    for key, value in keys.items():
        string = re.sub(rf"%{re.escape(key)}%", str(value), string)

    return string


class _NullMeta(type):
    def __new__(cls, name: str, bases: tuple[type, ...], namespace: dict[str, typing.Any]):
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
class Null(int if typing.TYPE_CHECKING else object, metaclass=_NullMeta):
    __slots__ = ()

    def __str__(self) -> str:
        return "?"

    def __repr__(self) -> str:
        return "NaN"

    def __format__(self, _: str, /) -> str:
        return self.__str__()

    def __eq__(self, _: object) -> bool:
        return False

    def __round__(self, _: typing.SupportsIndex, /) -> typing_.Self:
        # round() on float("nan") raises ValueError and probably has a good reason to do so,
        # but for my purposes it is essential round() returns this object too
        return self


NULL: typing.Final = Null()


def maybe_null(value: int | None, /) -> int:
    return NULL if value is None else value


def assert_type(type_: type[T], obj: object, /, *, at: DataPath = ()) -> T:
    """Assert object is of given type."""
    if (base_type := typing.get_origin(type_)) is None:
        base_type = type_
        value_type: type | typing.Any = typing.Any

    else:
        value_type = typing.get_args(type_)[0]

    if typing_.is_typeddict(base_type):
        base_type = dict

    if issubclass(base_type, PartialEnum):
        return assert_enum(base_type, obj, at=at)

    if not isinstance(obj, base_type):
        raise DataTypeError(type(obj), base_type, at=at) from None

    if issubclass(base_type, abc.Sequence) and not issubclass(base_type, str):
        assert_iterable(value_type, typing.cast(abc.Sequence[object], obj), at=at)

    return typing.cast(T, obj)


def assert_iterable(type_: type[T], obj: abc.Iterable[object], /, *, at: DataPath = ()) -> None:
    """Assert members of an iterable are of given type."""
    if type_ is typing.Any:
        return

    catch = Catch()

    for i, val in enumerate(obj):
        with catch:
            assert_type(type_, val, at=(*at, i))

    catch.checkpoint()


def assert_enum(enum: type[E], obj: object, /, *, at: DataPath = ()) -> E:
    """Assert name is a valid enum member."""
    if isinstance(obj, str):
        obj = obj.upper()
        try:
            return enum.of_name(obj)

        except KeyError:
            pass
    else:
        obj = type(obj)

    raise DataTypeError(obj, enum, at=at) from None


def assert_key(
    type_: type[T],
    obj: abc.Mapping[JSON_KT, object],
    /,
    key: JSON_KT,
    *,
    at: DataPath = (),
) -> T:
    """Assert key exists in mapping and its value is of given type."""
    try:
        value = obj[key]

    except KeyError:
        raise DataKeyError(key, at=at) from None

    return assert_type(type_, value, at=(*at, key))


def assert_keys(
    types: type[tuple[typing_.Unpack[Ts]]],
    mapping: abc.Mapping[JSON_KT, object],
    /,
    *keys: JSON_KT,
    at: DataPath = (),
) -> tuple[typing_.Unpack[Ts]]:
    """Assert multiple keys exist in a mapping and their values are of correct type."""
    results: list[object] = []
    catch = Catch()

    for type_, key in zip(typing.get_args(types), keys, strict=True):
        with catch:
            value = assert_key(type_, mapping, key, at=at)
            if not catch.issues:
                results.append(value)

    catch.checkpoint()
    return tuple(results)  # pyright: ignore[reportReturnType]
