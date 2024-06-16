from typing import Final, NewType, TypeAlias

__all__ = ("Element", "ItemID", "Paint", "Tag", "Type")

ItemID: Final = NewType("ItemID", str)
"""Unique identifier of an item."""
Paint: TypeAlias = str
"""The name of the paint, or a #-prefixed hex string as a color."""
Element: TypeAlias = str
"""Element of an item."""
Type: TypeAlias = str
"""Type denoting the function of the item."""
Tag: TypeAlias = str
"""Miscellaneous identifier."""
