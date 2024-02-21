from collections import abc
from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    from ..enums.arenashop import Category

__all__ = ("ArenaShopMapping", "MutableArenaShopMapping")

ArenaShopMapping: TypeAlias = abc.Mapping["Category", int]
"""Generic mapping of arena shop categories to their levels."""
MutableArenaShopMapping: TypeAlias = abc.MutableMapping["Category", int]
"""Generic mutable mapping of arena shop categories to their levels."""
