from collections import abc
from typing import Any, Final, overload

from attrs import define, field

from .errors import IDLookupError, PackKeyError
from .item import Item, ItemData, Tier
from .typeshed import ItemID, PackKey
from .utils import large_mapping_repr

__all__ = ("ItemPack", "PackData")


@define
class PackData:
    key: Final[PackKey] = field()
    name: str = field(default="<no name>")
    description: str = field(default="<no description>")


@define(kw_only=True)
class ItemPack:
    """Mapping-like container of items and their graphics."""

    data: Final[PackData] = field()
    items: Final[abc.Mapping[ItemID, ItemData]] = field(repr=large_mapping_repr)
    sprites: Final[abc.Mapping[tuple[ItemID, Tier], Any]] = field(repr=large_mapping_repr)

    def __contains__(self, value: ItemID | ItemData, /) -> bool:
        if isinstance(value, int):
            return value in self.items

        if isinstance(value, ItemData):
            return value.pack_key == self.data.key and value.id in self.items

        return False

    def get_item(self, item_id: ItemID, /) -> ItemData:
        """Lookup an item by its ID.

        Raises
        ------
        IDLookupError: item not found.
        """
        try:
            return self.items[item_id]

        except KeyError:
            raise IDLookupError(item_id) from None

    @overload
    def get_sprite(self, item: Item, /) -> Any:
        ...

    @overload
    def get_sprite(self, item: ItemData, /, tier: Tier) -> Any:
        ...

    def get_sprite(self, item: ItemData | Item, /, tier: Tier | None = None) -> Any:
        """Lookup item's sprite.

        Raises
        ------
        PackKeyError: item comes from different pack.
        """
        if isinstance(item, ItemData):
            if tier is None:
                msg = "Tier not provided with ItemData"
                raise TypeError(msg)

        elif tier is not None:
            msg = "Tier provided for Item"
            raise TypeError(msg)

        else:
            tier = item.tier
            item = item.data

        if item.pack_key != self.data.key:
            raise PackKeyError(item.pack_key)

        return self.sprites[item.id, tier]
