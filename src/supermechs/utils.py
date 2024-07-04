from collections import abc
from typing import Final, Generic, overload
from typing_extensions import Self, TypeVar

from attrs import define

from .typeshed import KT, VT, HasDefault, RestrictedContainer, SupportsGetSetItem, T


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

    _obj: Final[SupportsGetSetItem[KT, VT]]
    _keys: abc.Sequence[KT]

    def __len__(self) -> int:
        return len(self._keys)

    def __getitem__(self, index: int, /) -> VT:
        key = self._keys[index]
        return self._obj[key]

    def __setitem__(self, index: int, item: VT, /) -> None:
        key = self._keys[index]
        self._obj[key] = item

    def __iter__(self) -> abc.Iterator[VT]:
        return (self._obj[key] for key in self._keys)


HasDefaultT = TypeVar("HasDefaultT", bound=HasDefault, infer_variance=True)


def init_default(cls: type[HasDefaultT], /) -> type[HasDefaultT]:
    cls.default = cls()
    return cls
