from collections import abc
from enum import auto, unique
from typing import NamedTuple

from ._base import PartialEnum

__all__ = ("Category",)


@unique
class Category(PartialEnum):
    """Enumeration of arena shop categories."""

    # fmt: off
    energy_capacity        = auto()
    energy_regeneration    = auto()
    energy_damage          = auto()
    heat_capacity          = auto()
    heat_cooling           = auto()
    heat_damage            = auto()
    physical_damage        = auto()
    explosive_damage       = auto()
    electric_damage        = auto()
    physical_resistance    = auto()
    explosive_resistance   = auto()
    electric_resistance    = auto()
    fuel_capacity          = auto()
    fuel_regeneration      = auto()
    total_hp               = auto()
    arena_gold_increase    = auto()
    campaign_gold_increase = auto()
    titan_damage           = auto()
    base_crafting_cost     = auto()
    base_crafting_speed    = auto()
    base_upgrade_speed     = auto()
    fortune_boxes          = auto()
    backfire_reduction     = auto()
    titan_reward           = auto()
    # fmt: on

    @property
    def data(self) -> "CategoryData":
        return _CATEGORIES_DATA[self]


class CategoryData(NamedTuple):
    progression: abc.Sequence[float]
    is_absolute: bool

    @property
    def max_level(self) -> int:
        return len(self.progression) - 1


_TYPICAL = (0, 1, 3, 5, 7, 9, 11, 13, 15, 17, 20)
_DOUBLED = tuple(x * 2 for x in _TYPICAL)
_NEGATIVE = tuple(-x for x in _TYPICAL)
_HP = (0, 10, 30, 60, 90, 120, 150, 180, 220, 260, 300, 350)
_CATEGORIES_DATA: abc.Mapping[Category, CategoryData] = {
    Category.energy_capacity:        CategoryData(_TYPICAL, False),
    Category.energy_regeneration:    CategoryData(_TYPICAL, False),
    Category.energy_damage:          CategoryData(_TYPICAL, False),
    Category.heat_capacity:          CategoryData(_TYPICAL, False),
    Category.heat_cooling:           CategoryData(_TYPICAL, False),
    Category.heat_damage:            CategoryData(_TYPICAL, False),
    Category.physical_damage:        CategoryData(_TYPICAL, False),
    Category.explosive_damage:       CategoryData(_TYPICAL, False),
    Category.electric_damage:        CategoryData(_TYPICAL, False),
    Category.physical_resistance:    CategoryData(_DOUBLED, False),
    Category.explosive_resistance:   CategoryData(_DOUBLED, False),
    Category.electric_resistance:    CategoryData(_DOUBLED, False),
    Category.fuel_capacity:          CategoryData((0,), True),
    Category.fuel_regeneration:      CategoryData((), False),
    Category.total_hp:               CategoryData(_HP, True),
    Category.arena_gold_increase:    CategoryData((), False),
    Category.campaign_gold_increase: CategoryData((), False),
    Category.titan_damage:           CategoryData((), False),
    Category.base_crafting_cost:     CategoryData((), False),
    Category.base_crafting_speed:    CategoryData((), False),
    Category.base_upgrade_speed:     CategoryData((), False),
    Category.fortune_boxes:          CategoryData((), True),
    Category.backfire_reduction:     CategoryData(_NEGATIVE, False),
    Category.titan_reward:           CategoryData((), False),
}  # fmt: skip
