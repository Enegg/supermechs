from __future__ import annotations

import logging
import typing as t

from attrs import define, field

from .errors import IDLookupError, PackKeyError
from .item import Item, ItemData, Tier
from .rendering.sprites import ItemSprite
from .typeshed import ID, T
from .utils import large_mapping_repr

__all__ = ("ItemPack",)

LOGGER = logging.getLogger(__name__)


@define(kw_only=True)
class ItemPack(t.Generic[T]):
    """Mapping-like container of items and their GFX."""

    key: str = field()
    name: str = field(default="<no name>")
    description: str = field(default="<no description>")

    items: t.Mapping[ID, ItemData] = field(repr=large_mapping_repr)
    sprites: t.Mapping[tuple[ID, Tier], ItemSprite[T]] = field(repr=large_mapping_repr)
    # personal packs
    custom: bool = field(default=False)

    def __contains__(self, value: ID | ItemData, /) -> bool:
        if isinstance(value, ID):
            return value in self.items

        if isinstance(value, ItemData):
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

    @t.overload
    def get_sprite(self, item: Item, /) -> ItemSprite[T]:
        ...

    @t.overload
    def get_sprite(self, item: ItemData, /, tier: Tier) -> ItemSprite[T]:
        ...

    def get_sprite(self, item: ItemData | Item, /, tier: Tier | None = None) -> ItemSprite[T]:
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
            tier = item.stage.tier
            item = item.data

        if item.pack_key != self.key:
            raise PackKeyError(item.pack_key)

        return self.sprites[item.id, tier]
