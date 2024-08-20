from typing import Final, TypeAlias

from .abc.arenashop import ArenaShopMapping, MutableArenaShopMapping
from .enums.arenashop import Category

__all__ = ("MAX_SHOP", "ArenaShop", "is_shop_empty", "max_shop")


ArenaShop: TypeAlias = dict[Category, int]
"""Collection of arena shop upgrades."""


def arena_shop() -> ArenaShop:
    """Create an empty arena shop."""
    return dict.fromkeys(Category, 0)


def is_shop_empty(shop: ArenaShopMapping, /) -> bool:
    """Whether all categories are at level 0."""
    return not any(shop.values())


def max_shop(shop: MutableArenaShopMapping, /) -> None:
    """Set categories of provided arena shop to their maximum level."""
    for category in Category:
        shop[category] = category.data.max_level


MAX_SHOP: Final[ArenaShopMapping] = {}
max_shop(MAX_SHOP)
