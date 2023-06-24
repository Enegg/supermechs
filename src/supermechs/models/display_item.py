from attrs import define
from typing_extensions import Self

from ..enums import Tier
from .item_base import ItemBase


@define
class Color:
    """Represents a monolithic color of an item."""
    value: int

    @property
    def r(self) -> int:
        """Red channel of the color."""
        return self.value & 0b111

    @property
    def g(self) -> int:
        """Green channel of the color."""
        return self.value >> 3 & 0b111

    @property
    def b(self) -> int:
        """Blue channel of the color."""
        return self.value >> 6 & 0b111

    @classmethod
    def from_hex_str(cls, string: str) -> Self:
        value = int(string.removeprefix("#"), base=16)
        return cls(value)


@define
class Paint:
    """Represents a custom paint."""
    name: str


@define(kw_only=True)
class DisplayItem:
    """Represents unique properties of an item."""

    base: ItemBase

    tier: Tier
    paint: Color | Paint | None = None  # paint etc; might be an enum
    level: int = 0
    display_level: str = "1"

    @classmethod
    def from_item(cls, item: ItemBase, /, *, maxed: bool = False) -> Self:
        return cls(base=item, tier=item.transform_range.max if maxed else item.transform_range.min)
