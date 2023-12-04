import typing as t
from enum import auto, unique

from .utils import PartialEnum

__all__ = ("MAX_SHOP", "ArenaShop", "Category", "is_shop_empty", "max_shop")


@unique
class Category(PartialEnum):
    """Enumeration of arena shop categories."""

    energy_capacity = auto()
    energy_regeneration = auto()
    energy_damage = auto()
    heat_capacity = auto()
    heat_cooling = auto()
    heat_damage = auto()
    physical_damage = auto()
    explosive_damage = auto()
    electric_damage = auto()
    physical_resistance = auto()
    explosive_resistance = auto()
    electric_resistance = auto()
    fuel_capacity = auto()
    fuel_regeneration = auto()
    total_hp = auto()
    arena_gold_increase = auto()
    campaign_gold_increase = auto()
    titan_damage = auto()
    base_crafting_cost = auto()
    base_crafting_speed = auto()
    base_upgrade_speed = auto()
    fortune_boxes = auto()
    backfire_reduction = auto()
    titan_reward = auto()


ArenaShop: t.TypeAlias = dict[Category, int]
"""Collection of arena shop upgrades."""
ArenaShopMapping: t.TypeAlias = t.Mapping[Category, int]
MutableArenaShopMapping: t.TypeAlias = t.MutableMapping[Category, int]


def arena_shop() -> ArenaShop:
    """Create an empty arena shop."""
    return dict.fromkeys(Category, 0)


def is_shop_empty(shop: ArenaShopMapping, /) -> bool:
    """Whether all categories are at level 0."""
    return not any(shop.values())


def max_shop(shop: MutableArenaShopMapping, /) -> None:
    """Maxes out levels of provided arena shop."""
    for category in Category:
        shop[category] = get_data(category).max_level


class CategoryData(t.NamedTuple):
    progression: t.Sequence[float]
    is_absolute: bool

    @property
    def max_level(self) -> int:
        return len(self.progression) - 1


_typical = (0, 1, 3, 5, 7, 9, 11, 13, 15, 17, 20)
_doubled = tuple(x * 2 for x in _typical)
_negative = tuple(-x for x in _typical)
_categories_data: t.Mapping[Category, CategoryData] = {
    Category.energy_capacity: CategoryData(_typical, False),
    Category.energy_regeneration: CategoryData(_typical, False),
    Category.energy_damage: CategoryData(_typical, False),
    Category.heat_capacity: CategoryData(_typical, False),
    Category.heat_cooling: CategoryData(_typical, False),
    Category.heat_damage: CategoryData(_typical, False),
    Category.physical_damage: CategoryData(_typical, False),
    Category.explosive_damage: CategoryData(_typical, False),
    Category.electric_damage: CategoryData(_typical, False),
    Category.physical_resistance: CategoryData(_doubled, False),
    Category.explosive_resistance: CategoryData(_doubled, False),
    Category.electric_resistance: CategoryData(_doubled, False),
    Category.fuel_capacity: CategoryData((0,), True),
    Category.fuel_regeneration: CategoryData((), False),
    Category.total_hp: CategoryData((0, 10, 30, 60, 90, 120, 150, 180, 220, 260, 300, 350), True),
    Category.arena_gold_increase: CategoryData((), False),
    Category.campaign_gold_increase: CategoryData((), False),
    Category.titan_damage: CategoryData((), False),
    Category.base_crafting_cost: CategoryData((), False),
    Category.base_crafting_speed: CategoryData((), False),
    Category.base_upgrade_speed: CategoryData((), False),
    Category.fortune_boxes: CategoryData((), True),
    Category.backfire_reduction: CategoryData(_negative, False),
    Category.titan_reward: CategoryData((), False),
}

get_data: t.Final = _categories_data.__getitem__
"""Get data about a category."""

MAX_SHOP: t.Final[ArenaShopMapping] = arena_shop()
max_shop(MAX_SHOP)
