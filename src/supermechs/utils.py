from collections import abc
from typing import Any, Final, Generic, Protocol, overload

from attrs import define
from typing_extensions import Self

from .typeshed import KT, VT


def has_any_of(mapping: abc.Mapping[Any, object], /, *keys: abc.Hashable) -> bool:
    """Returns True if a mapping contains any of the specified keys."""
    return not mapping.keys().isdisjoint(keys)


def has_all_of(mapping: abc.Mapping[Any, object], /, *keys: abc.Hashable) -> bool:
    """Returns True if a mapping contains all of the specified keys."""
    return frozenset(keys).issubset(mapping.keys())


def _get_display_brackets(cls: type, /) -> tuple[str, str]:
    if cls is tuple:
        return "(", ")"

    if cls is list:
        return "[", "]"

    if cls is set or cls is dict:
        return "{", "}"

    return f"{cls.__name__}<", ">"


def large_collection_repr(obj: abc.Collection[object], /, threshold: int = 20) -> str:
    if len(obj) <= threshold:
        return repr(obj)

    import itertools

    items = ", ".join(map(repr, itertools.islice(obj, threshold)))
    left, right = _get_display_brackets(type(obj))
    return f"{left}{items}, +{len(obj) - threshold} more{right}"


def large_mapping_repr(mapping: abc.Mapping[Any, object], /, threshold: int = 20) -> str:
    if len(mapping) <= threshold:
        return repr(mapping)

    import itertools

    items = ", ".join(f"{k!r}: {v!r}" for k, v in itertools.islice(mapping.items(), threshold))
    left, right = _get_display_brackets(type(mapping))
    return f"{left}{items}, +{len(mapping) - threshold} more{right}"


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
