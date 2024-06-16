from collections import abc
from typing import TypeAlias

__all__ = ("ArenaShopMapping", "Category", "MutableArenaShopMapping")

Category: TypeAlias = str
"""Arena shop category."""
ArenaShopMapping: TypeAlias = abc.Mapping[Category, int]
"""Generic mapping of arena shop categories to their levels."""
MutableArenaShopMapping: TypeAlias = abc.MutableMapping[Category, int]
"""Generic mutable mapping of arena shop categories to their levels."""
