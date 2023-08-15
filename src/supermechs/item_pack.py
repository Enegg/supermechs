from __future__ import annotations

import logging
import typing as t

from attrs import define, field

from .errors import UnknownDataVersion
from .models.item_data import ItemData
from .typedefs import ID, AnyItemPack, Name
from .utils import assert_type, large_mapping_repr

__all__ = ("ItemPack", "extract_key")

LOGGER = logging.getLogger(__name__)


# TODO: use match case and/or custom exception for input validation
def extract_key(pack: AnyItemPack, /) -> str:
    """Extract the key of an item pack.

    Raises
    ------
    TypeError on unknown version.
    """
    if "version" not in pack or pack["version"] == "1":
        key = pack["config"]["key"]

    elif pack["version"] in ("2", "3"):
        key = pack["key"]

    else:
        raise UnknownDataVersion("pack", pack["version"], 3)

    return assert_type(str, key)


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
    names_to_ids: t.MutableMapping[Name, ID] = field(factory=dict, init=False, repr=False)
    # Abbrev to a set of names the abbrev matches
    name_abbrevs: t.MutableMapping[str, t.AbstractSet[Name]] = field(factory=dict, init=False, repr=False)

    def __contains__(self, value: Name | ID | ItemData) -> bool:
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
        LookupError: name not found.
        """
        try:
            id = self.names_to_ids[name]

        except KeyError as err:
            raise LookupError(f"No item named {name!r} in the pack") from err

        return self.items[id]

    def get_item_by_id(self, item_id: ID, /) -> ItemData:
        try:
            return self.items[item_id]

        except KeyError as err:
            raise LookupError(f"No item with ID {item_id} in the pack") from err

    @t.overload
    def get_item(self, name: Name, /) -> ItemData:
        ...

    @t.overload
    def get_item(self, item_id: ID, /) -> ItemData:
        ...

    def get_item(self, item: Name | ID, /) -> ItemData:
        """Lookup an item by its name or ID.

        Raises
        ------
        LookupError: name or ID not found.
        """
        if isinstance(item, ID):
            return self.get_item_by_id(item)

        return self.get_item_by_name(item)

    def iter_item_names(self) -> t.Iterator[Name]:
        return iter(self.names_to_ids)
