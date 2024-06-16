from collections import abc
from typing import NamedTuple

from supermechs.abc.arenashop import Category
from supermechs.enums.arenashop import CategoryEnum

__all__ = ("CategoryData", "get_category_data")


class CategoryData(NamedTuple):
    progression: abc.Sequence[float]
    is_absolute: bool

    @property
    def max_level(self) -> int:
        return len(self.progression) - 1


def get_category_data(category: Category, /) -> CategoryData:
    return _CATEGORIES_DATA[category]


_TYPICAL = (0, 1, 3, 5, 7, 9, 11, 13, 15, 17, 20)
_DOUBLED = tuple(x * 2 for x in _TYPICAL)
_NEGATIVE = tuple(-x for x in _TYPICAL)
_HP = (0, 10, 30, 60, 90, 120, 150, 180, 220, 260, 300, 350)
_CATEGORIES_DATA: abc.Mapping[Category, CategoryData] = {
    CategoryEnum.mech_energy_capacity:        CategoryData(_TYPICAL, False),
    CategoryEnum.mech_energy_regeneration:    CategoryData(_TYPICAL, False),
    CategoryEnum.mech_energy_damage:          CategoryData(_TYPICAL, False),
    CategoryEnum.mech_heat_capacity:          CategoryData(_TYPICAL, False),
    CategoryEnum.mech_heat_cooling:           CategoryData(_TYPICAL, False),
    CategoryEnum.mech_heat_damage:            CategoryData(_TYPICAL, False),
    CategoryEnum.mech_physical_damage:        CategoryData(_TYPICAL, False),
    CategoryEnum.mech_explosive_damage:       CategoryData(_TYPICAL, False),
    CategoryEnum.mech_electric_damage:        CategoryData(_TYPICAL, False),
    CategoryEnum.mech_physical_resistance:    CategoryData(_DOUBLED, False),
    CategoryEnum.mech_explosive_resistance:   CategoryData(_DOUBLED, False),
    CategoryEnum.mech_electric_resistance:    CategoryData(_DOUBLED, False),
    CategoryEnum.campaign_fuel_capacity:          CategoryData((0,), True),
    CategoryEnum.campaign_fuel_regeneration:      CategoryData((), False),
    CategoryEnum.mech_hp_increase:               CategoryData(_HP, True),
    CategoryEnum.arena_gold_increase:    CategoryData((), False),
    CategoryEnum.campaign_gold_increase: CategoryData((), False),
    CategoryEnum.titan_damage:           CategoryData((), False),
    CategoryEnum.base_crafting_cost:     CategoryData((), False),
    CategoryEnum.base_crafting_speed:    CategoryData((), False),
    CategoryEnum.base_upgrade_speed:     CategoryData((), False),
    CategoryEnum.fortune_boxes:          CategoryData((), True),
    CategoryEnum.mech_backfire_reduction:     CategoryData(_NEGATIVE, False),
    CategoryEnum.titan_reward:           CategoryData((), False),
}  # fmt: skip
