from typing import Final, NewType, TypeAlias

Name: TypeAlias = str
"""String representing item name."""
ItemID: Final = NewType("ItemID", int)
"""Positive integer representing an item's ID."""
Paint: TypeAlias = str
"""The name of the paint, or a #-prefixed hex string as a color."""
