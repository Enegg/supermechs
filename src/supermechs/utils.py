import typing as t
import typing_extensions as tex
from contextlib import suppress
from enum import Enum

from .typeshed import T


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


# the urge to name this function in pascal case
def _is_pascal(string: str, /) -> bool:
    """Returns True if the string is pascal-cased, False otherwise.

    A string is pascal-cased if it contains no whitespace, begins with an uppercase letter,
    and all following uppercase letters are separated by at least a single lowercase letter.
        >>> is_pascal("fooBar")
        False
        >>> is_pascal("FooBar")
        True
        >>> is_pascal("Foo Bar")
        False
    """
    # use not .isupper() to have it True on whitespace too
    if not string[:1].isupper():
        return False

    prev_is_upper = False

    for char in string:
        if char.isspace():
            return False

        if prev_is_upper and char.isupper():
            return False

        prev_is_upper = char.isupper()

    return True


def acronym_of(name: str, /) -> str | None:
    """Returns an acronym of the name, or None if one cannot (shouldn't) be made.

    The acronym consists of capital letters in item's name;
    it will not be made for non-PascalCase single-word names, or names which themselves
    are an acronym for something (like EMP).
    """
    if _is_pascal(name) and name[1:].islower():
        # cannot make an acronym from a single capital letter
        return None
    # filter out already-acronym names, like "EMP"
    if name.isupper():
        return None
    # Overloaded EMP is fine to make an abbreviation for though
    return "".join(filter(str.isupper, name)).lower()


class cached_slot_property(t.Generic[T]):
    """Descriptor similar to functools.cached_property, but for slotted classes.

    Caches the value to an attribute of the same name as the decorated function, prepended with _.
    """

    __slots__ = ("func", "slot")

    def __init__(self, func: t.Callable[[t.Any], T]) -> None:
        self.func: t.Final = func
        self.slot: t.Final[str] = "_" + func.__name__

    def __repr__(self) -> str:
        return f"<{type(self).__name__} of slot {self.slot!r}>"

    @t.overload
    def __get__(self, obj: None, cls: t.Any, /) -> tex.Self:
        ...

    @t.overload
    def __get__(self, obj: t.Any, cls: t.Any, /) -> T:
        ...

    def __get__(self, obj: t.Any | None, cls: t.Any, /) -> T | tex.Self:
        del cls

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
        try:  # noqa: SIM105
            delattr(obj, self.slot)

        except AttributeError:
            pass


def has_any_of(mapping: t.Mapping[t.Any, t.Any], /, *keys: t.Any) -> bool:
    """Returns True if a mapping contains any of the specified keys."""
    return not mapping.keys().isdisjoint(keys)


def has_all_of(mapping: t.Mapping[t.Any, t.Any], /, *keys: t.Any) -> bool:
    """Returns True if a mapping contains all of the specified keys."""
    return set(keys).issubset(mapping.keys())


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

    msg = f"Expected {type_.__name__}, got {type(value).__name__}"
    raise TypeError(msg) from None


def _get_brackets(cls: type, /) -> tuple[str, str]:
    if cls is tuple:
        return "(", ")"

    if cls is list:
        return "[", "]"

    if cls is set or cls is dict:
        return "{", "}"

    return f"{cls.__name__}<", ">"


def large_collection_repr(obj: t.Collection[t.Any], /, threshold: int = 20) -> str:
    if len(obj) <= threshold:
        return repr(obj)

    left, right = _get_brackets(type(obj))

    import itertools

    items = ", ".join(map(repr, itertools.islice(obj, threshold)))
    return f"{left}{items}, +{len(obj) - threshold} more{right}"


def large_mapping_repr(mapping: t.Mapping[t.Any, t.Any], /, threshold: int = 20) -> str:
    if len(mapping) <= threshold:
        return repr(mapping)

    left, right = _get_brackets(type(mapping))

    import itertools

    items = ", ".join(f"{k!r}: {v!r}" for k, v in itertools.islice(mapping.items(), threshold))
    return f"{left}{items}, +{len(mapping) - threshold} more{right}"


class PartialEnum(Enum):
    def __repr__(self) -> str:
        return str(self)

    @classmethod
    def of_name(cls, name: str, /) -> tex.Self:
        """Get enum member by name."""
        return cls[name]

    @classmethod
    def of_value(cls, value: t.Any, /) -> tex.Self:
        """Get enum member by value."""
        return cls.__call__(value)
