from collections import abc
from typing import Generic

import attrs

from .typeshed import T, U


@attrs.define
class default(Generic[T]):  # noqa: N801
    """Class property initializing a default instance on access."""

    f: abc.Callable[[], T]
    name: str = attrs.field(init=False)

    def __set_name__(self, cls: type[T], name: str) -> None:
        self.name = name

    def __get__(self, _: None, cls: type[T], /) -> T:
        inst = self.f()
        setattr(cls, self.name, inst)
        return inst

    @staticmethod
    def mutable(f: abc.Callable[[], U], /) -> "default[U] | U":
        """Mark the type of decorated name as `default[T] | T`, allowing for direct write."""
        return default(f)
