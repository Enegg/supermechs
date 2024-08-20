from enum import Enum
from typing_extensions import Self


class PartialEnum(Enum):
    def __repr__(self) -> str:
        return str(self)

    @classmethod
    def of_name(cls, name: str, /) -> Self:
        """Get enum member by name."""
        return cls[name]

    @classmethod
    def of_value(cls, value: object, /) -> Self:
        """Get enum member by value."""
        return cls.__call__(value)
