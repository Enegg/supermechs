import random
import re
import statistics
import typing as t
from collections import Counter
from contextlib import suppress
from string import ascii_letters

from typing_extensions import Self, override

from .typeshed import T, twotuple


def search_for(
    phrase: str, iterable: t.Iterable[str], *, case_sensitive: bool = False
) -> t.Iterator[str]:
    """
    Helper func capable of finding a specific string(s) in iterable.
    It is considered a match if every word in phrase appears in the name
    and in the same order. For example, both `burn scop` & `half scop`
    would match name `Half Burn Scope`, but not `burn half scop`.

    Parameters
    ----------
    phrase:
        String of whitespace-separated words.
    iterable:
        Iterable of strings to match against.
    case_sensitive:
        Whether the search should be case sensitive.
    """
    parts = (phrase if case_sensitive else phrase.lower()).split()

    for name in iterable:
        words = iter((name if case_sensitive else name.lower()).split())

        if all(any(word.startswith(prefix) for word in words) for prefix in parts):
            yield name


def js_format(string: str, /, **kwargs: t.Any) -> str:
    """Format a JavaScript style string using given keys and values."""
    # XXX: this will do as many passes as there are kwargs, maybe concatenate the pattern?
    for key, value in kwargs.items():
        string = re.sub(rf"%{re.escape(key)}%", str(value), string)

    return string


def format_count(it: t.Iterable[t.Any], /) -> t.Iterator[str]:
    return (
        f'{item}{f" x{count}" * (count > 1)}' for item, count in Counter(filter(None, it)).items()
    )


def random_str(length: int, /, charset: str = ascii_letters) -> str:
    """Generates a random string of given length from ascii letters."""
    return "".join(random.sample(charset, length))


def mean_and_deviation(*numbers: float) -> twotuple[float]:
    """Returns the arithmetric mean and the standard deviation of a sequence of numbers."""
    mean = statistics.fmean(numbers)
    return mean, statistics.pstdev(numbers, mean)


class NanMeta(type):
    @override
    def __new__(cls, name: str, bases: tuple[type, ...], namespace: dict[str, t.Any]) -> Self:
        def func(self: T, __value: int) -> T:
            return self

        for dunder in ("add", "sub", "mul", "truediv", "floordiv", "mod", "pow"):
            namespace[f"__{dunder}__"] = func
            namespace[f"__r{dunder}__"] = func

        return super().__new__(cls, name, bases, namespace)


class Nan(int, metaclass=NanMeta):
    @override
    def __str__(self) -> str:
        return "?"

    @override
    def __repr__(self) -> str:
        return "NaN"

    @override
    def __format__(self, _: str, /) -> str:
        return "?"

    @override
    def __eq__(self, _: t.Any) -> bool:
        return False

    @override
    def __lt__(self, _: t.Any) -> bool:
        return False

    @override
    def __round__(self, ndigits: int = 0, /) -> Self:
        # round() on float("nan") raises ValueError and probably has a good reason to do so,
        # but for my purposes it is essential round() returns this object too
        return self


NaN: t.Final = Nan()


# the urge to name this function in pascal case
def is_pascal(string: str) -> bool:
    """Returns True if the string is pascal-cased string, False otherwise.

    A string is pascal-cased if it is a single word, begins with a capitalized letter,
    and has at least a single lowercase letter.
        >>> is_pascal("fooBar")
        False
        >>> is_pascal("FooBar")
        True
        >>> is_pascal("Foo Bar")
        False
    """
    return string[:1].isupper() and " " not in string


class cached_slot_property(t.Generic[T]):
    """Descriptor similar to functools.cached_property, but designed for slotted classes.
    Caches the value to an attribute of the same name as the decorated function, prepended with _.
    """

    __slots__ = ("func",)

    def __init__(self, func: t.Callable[[t.Any], T]) -> None:
        self.func = func

    @property
    def slot(self) -> str:
        return "_" + self.func.__name__

    def __repr__(self) -> str:
        return f"<{type(self).__name__} of slot {self.slot!r}>"

    @t.overload
    def __get__(self, obj: None, owner: t.Any, /) -> Self:
        ...

    @t.overload
    def __get__(self, obj: t.Any, owner: t.Any, /) -> T:
        ...

    def __get__(self, obj: t.Any | None, owner: t.Any, /) -> T | Self:
        del owner

        if obj is None:
            return self

        try:
            return getattr(obj, self.slot)

        except AttributeError:
            value = self.func(obj)
            setattr(obj, self.slot, value)
            return value

    def __delete__(self, obj: t.Any) -> None:
        """Deletes the cached value."""
        try:
            delattr(obj, self.slot)

        except AttributeError:
            pass


def has_any_of_keys(mapping: t.Mapping[t.Any, t.Any], /, *keys: t.Any) -> bool:
    """Returns True if a mapping contains any of the specified keys."""
    return not mapping.keys().isdisjoint(keys)


def assert_type(type_: type[T], value: T, /, *, cast: bool = True) -> T:
    """Assert value is of given type.

    If cast is `True`, will attempt to cast to `type_` before failing.
    """
    if isinstance(value, type_):
        return value

    if cast and not issubclass(type_, str):
        # we exclude string casting since anything can be casted to string
        with suppress(Exception):
            return type_(value)

    raise TypeError(f"Expected {type_.__name__}, got {type(value).__name__}") from None


def large_sequence_repr(
    obj: t.Sequence[t.Any] | t.AbstractSet[t.Any], /, threshold: int = 20
) -> str:
    if len(obj) <= threshold:
        return repr(obj)

    if type(obj) is tuple:
        left, right = "()"

    elif type(obj) is list:
        left, right = "[]"

    elif type(obj) is set:
        left, right = "{}"

    else:
        left, right = f"{type(obj).__name__}<", ">"

    import itertools

    items = ", ".join(map(repr, itertools.islice(obj, threshold)))
    return f"{left}{items}, +{len(obj) - threshold} more{right}"


def large_mapping_repr(mapping: t.Mapping[t.Any, t.Any], /, threshold: int = 20) -> str:
    if len(mapping) <= threshold:
        return repr(mapping)

    if type(mapping) is dict:
        left, right = "{}"

    else:
        left, right = f"{type(mapping).__name__}<", ">"

    import itertools

    items = ", ".join(f"{k!r}: {v!r}" for k, v in itertools.islice(mapping.items(), threshold))
    return f"{left}{items}, +{len(mapping) - threshold} more{right}"
