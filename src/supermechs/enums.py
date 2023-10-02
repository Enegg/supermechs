
import typing as t
import typing_extensions as tex
from enum import Enum


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
