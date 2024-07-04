from collections import abc
from typing import ClassVar, Protocol, TypeAlias
from typing_extensions import ParamSpec, Self, TypeVar

T = TypeVar("T", infer_variance=True)
T2 = TypeVar("T2", infer_variance=True)
KT = TypeVar("KT", bound=abc.Hashable, infer_variance=True)
"""Key-type of a mapping."""
VT = TypeVar("VT", infer_variance=True)
"""Value-type of a mapping."""
P = ParamSpec("P")

Factory: TypeAlias = abc.Callable[[], T]
"""0-argument callable returning an object of given type."""
LiteralURL: TypeAlias = str
"""String representing a URL."""


class RestrictedContainer(Protocol[T]):
    # abc.Container expects __contain__ to take any object
    def __contains__(self, value: T, /) -> bool: ...


class SupportsGetSetItem(Protocol[KT, VT]):
    # this sort of exists within _typeshed as SupportsItemAccess,
    # but it also expects class to define __contains__

    def __getitem__(self, key: KT, /) -> VT: ...

    def __setitem__(self, key: KT, value: VT, /) -> None: ...


class HasDefault(Protocol):
    default: ClassVar[Self]
