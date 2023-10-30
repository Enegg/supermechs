import typing as t
from enum import auto

from attrs import Factory, define

from .utils import PartialEnum


@define
class ArenaShop:
    """Collection of arena shop upgrades."""

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

    levels: t.MutableMapping[Category, int] = Factory(lambda: dict.fromkeys(ArenaShop.Category, 0))

    def __getitem__(self, category: Category, /) -> int:
        return self.levels[category]

    def __setitem__(self, category: Category, level: int, /) -> None:
        # TODO: check boundaries
        self.levels[category] = level

    def are_levels_zero(self) -> bool:
        """Whether all categories are at level 0."""
        return not any(self.levels.values())


class CategoryData(t.NamedTuple):
    progression: t.Sequence[float]
    is_absolute: bool

    @property
    def max_level(self) -> int:
        return len(self.progression) - 1
