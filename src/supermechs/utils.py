from collections import abc
from enum import Enum
from typing import Any, Final, Generic, Protocol, overload
from typing_extensions import Self

from attrs import define

from .typeshed import KT, VT


def search_for(
    phrase: str, iterable: abc.Iterable[str], *, case_sensitive: bool = False
) -> abc.Iterator[str]:
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


def has_any_of(mapping: abc.Mapping[Any, Any], /, *keys: abc.Hashable) -> bool:
    """Returns True if a mapping contains any of the specified keys."""
    return not mapping.keys().isdisjoint(keys)


def has_all_of(mapping: abc.Mapping[Any, Any], /, *keys: abc.Hashable) -> bool:
    """Returns True if a mapping contains all of the specified keys."""
    return frozenset(keys).issubset(mapping.keys())


def _get_brackets(cls: type, /) -> tuple[str, str]:
    if cls is tuple:
        return "(", ")"

    if cls is list:
        return "[", "]"

    if cls is set or cls is dict:
        return "{", "}"

    return f"{cls.__name__}<", ">"


def large_collection_repr(obj: abc.Collection[Any], /, threshold: int = 20) -> str:
    if len(obj) <= threshold:
        return repr(obj)

    import itertools

    items = ", ".join(map(repr, itertools.islice(obj, threshold)))
    left, right = _get_brackets(type(obj))
    return f"{left}{items}, +{len(obj) - threshold} more{right}"


def large_mapping_repr(mapping: abc.Mapping[Any, Any], /, threshold: int = 20) -> str:
    if len(mapping) <= threshold:
        return repr(mapping)

    import itertools

    items = ", ".join(f"{k!r}: {v!r}" for k, v in itertools.islice(mapping.items(), threshold))
    left, right = _get_brackets(type(mapping))
    return f"{left}{items}, +{len(mapping) - threshold} more{right}"


class PartialEnum(Enum):
    def __repr__(self) -> str:
        return str(self)

    @classmethod
    def of_name(cls, name: str, /) -> Self:
        """Get enum member by name."""
        return cls[name]

    @classmethod
    def of_value(cls, value: Any, /) -> Self:
        """Get enum member by value."""
        return cls.__call__(value)


class _SupportsGetSetItem(Protocol[KT, VT]):
    # this sort of exists within _typeshed as SupportsItemAccess,
    # but it also expects class to define __contains__

    def __getitem__(self, key: KT, /) -> VT:
        ...

    def __setitem__(self, key: KT, value: VT, /) -> None:
        ...


@define
class KeyAccessor(Generic[KT, VT]):
    """Data descriptor proxying read/write from/to a specified key of a mapping-like object."""

    key: Final[KT]

    @overload
    def __get__(self, obj: None, cls: type | None, /) -> Self:
        ...

    @overload
    def __get__(self, obj: _SupportsGetSetItem[KT, VT], cls: type | None, /) -> VT:
        ...

    def __get__(self, obj: _SupportsGetSetItem[KT, VT] | None, cls: type | None, /) -> VT | Self:
        del cls
        if obj is None:
            return self

        return obj[self.key]

    def __set__(self, obj: _SupportsGetSetItem[KT, VT], value: VT, /) -> None:
        obj[self.key] = value


@define
class SequenceView(Generic[KT, VT]):
    """A sequence-like object providing a view on a mapping."""

    _obj: Final[_SupportsGetSetItem[tuple[KT, int], VT]]
    _key: Final[KT]
    length: int

    def __len__(self) -> int:
        return self.length

    def __getitem__(self, index: int, /) -> VT:
        if index >= self.length:
            raise IndexError

        return self._obj[self._key, index]

    def __setitem__(self, index: int, item: VT, /) -> None:
        if index >= self.length:
            raise IndexError

        self._obj[self._key, index] = item

    def __iter__(self) -> abc.Iterator[VT]:
        for n in range(self.length):
            yield self._obj[self._key, n]
