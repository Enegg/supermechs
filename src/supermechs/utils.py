from collections import abc
from typing import Final, Generic, overload
from typing_extensions import Self

from attrs import define

from .typeshed import KT, VT, RestrictedContainer, SupportsGetSetItem, T


def contains_any_of(obj: RestrictedContainer[T], /, *values: T) -> bool:
    """Return True if a container has any of the specified values."""
    return any(v in obj for v in values)


@define
class KeyAccessor(Generic[KT, VT]):
    """Data descriptor proxying read/write from/to a specified key of a mapping-like object."""

    key: Final[KT]

    @overload
    def __get__(self, obj: None, cls: type | None, /) -> Self: ...

    @overload
    def __get__(self, obj: SupportsGetSetItem[KT, VT], cls: type | None, /) -> VT: ...

    def __get__(self, obj: SupportsGetSetItem[KT, VT] | None, cls: type | None, /) -> VT | Self:
        del cls
        if obj is None:
            return self

        return obj[self.key]

    def __set__(self, obj: SupportsGetSetItem[KT, VT], value: VT, /) -> None:
        obj[self.key] = value


@define
class SequenceView(Generic[KT, VT]):
    """A sequence-like object providing a view on a mapping."""

    _obj: Final[SupportsGetSetItem[tuple[KT, int], VT]]
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
