from collections import abc
from typing import Any, overload

from attrs import define, field

from .errors import IDLookupError, PackKeyError
from .item import Item, ItemData, Tier
from .typeshed import ID
from .utils import large_mapping_repr

__all__ = ("ItemPack",)


@define(kw_only=True)
class ItemPack:
    """Mapping-like container of items and their graphics."""

    key: str = field()
    name: str = field(default="<no name>")
    description: str = field(default="<no description>")

    items: abc.Mapping[ID, ItemData] = field(repr=large_mapping_repr)
    sprites: abc.Mapping[tuple[ID, Tier], Any] = field(repr=large_mapping_repr)
    # personal packs
    custom: bool = field(default=False)

    def __contains__(self, value: ID | ItemData, /) -> bool:
        if isinstance(value, ID):
            return value in self.items

        if isinstance(value, ItemData):  # pyright: ignore[reportUnnecessaryIsInstance]
            return value.pack_key == self.key and value.id in self.items

        return False

    def get_item(self, item_id: ID, /) -> ItemData:
        """Lookup an item by its ID.

        Raises
        ------
        IDLookupError: item not found.
        """
        try:
            return self.items[item_id]

        except KeyError as err:
            raise IDLookupError(item_id) from err

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

        if item.pack_key != self.key:
            raise PackKeyError(item.pack_key)

        return self.sprites[item.id, tier]
