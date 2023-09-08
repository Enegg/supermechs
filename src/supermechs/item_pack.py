from __future__ import annotations

import logging
import typing as t

from attrs import define, field

from .models.item import ItemData
from .typedefs import ID, Name
from .utils import large_mapping_repr

__all__ = ("ItemPack",)

LOGGER = logging.getLogger(__name__)


@define
class ItemPack:
    """Object representing an item pack."""

    key: str = field()
    items: t.Mapping[ID, ItemData] = field(repr=large_mapping_repr)
    name: str = field(default="<no name>")
    description: str = field(default="<no description>")
    # personal packs
    custom: bool = field(default=False)

    # Item name to item ID
    names_to_ids: t.Mapping[Name, ID] = field(init=False, repr=False)

    @property
    def item_names(self) -> t.KeysView[Name]:
        """Set-like view on items' names."""
        return self.names_to_ids.keys()

    def __attrs_post_init__(self) -> None:
        self.names_to_ids = {item.name: item.id for item in self.items.values()}

    def __contains__(self, value: Name | ID | ItemData, /) -> bool:
        if isinstance(value, Name):
            return value in self.names_to_ids

        if isinstance(value, ID):
            return value in self.items

        if isinstance(value, ItemData):
            return value.pack_key == self.key and value.id in self.items

        return False

    def get_item_by_name(self, name: Name, /) -> ItemData:
        """Lookup an item by its name.

        Raises
        ------
        LookupError: item not found.
        """
        try:
            id = self.names_to_ids[name]

        except KeyError as err:
            raise LookupError(f"No item named {name!r} in the pack") from err

        return self.items[id]

    def get_item_by_id(self, item_id: ID, /) -> ItemData:
        """Lookup an item by its ID.

        Raises
        ------
        LookupError: item not found.
        """
        try:
            return self.items[item_id]

        except KeyError as err:
            raise LookupError(f"No item with ID {item_id} in the pack") from err
