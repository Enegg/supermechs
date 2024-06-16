from collections import abc

from supermechs.abc.arenashop import ArenaShopMapping, Category
from supermechs.abc.stats import MutableStatsMapping, Stat, StatsMapping
from supermechs.enums.arenashop import CategoryEnum
from supermechs.enums.stats import StatEnum
from supermechs.gamerules import BuildRules
from supermechs.item import Item, ItemData
from supermechs.mech import Mech
from supermechs.stats import StatsDict, get_final_stage
from supermechs.tools.arenashop import get_category_data

__all__ = (
    "apply_overload_penalties",
    "buff_stats",
    "get_item_stats",
    "max_stats",
    "mech_summary",
    "mech_weight",
)

STAT_TO_CATEGORY: abc.Mapping[Stat, Category] = {
    StatEnum.energy_capacity:      CategoryEnum.mech_energy_capacity,
    StatEnum.regeneration:         CategoryEnum.mech_energy_regeneration,
    StatEnum.energy_damage:        CategoryEnum.mech_energy_damage,
    StatEnum.heat_capacity:        CategoryEnum.mech_heat_capacity,
    StatEnum.cooling:              CategoryEnum.mech_heat_cooling,
    StatEnum.heat_damage:          CategoryEnum.mech_heat_damage,
    StatEnum.physical_damage:      CategoryEnum.mech_physical_damage,
    StatEnum.explosive_damage:     CategoryEnum.mech_explosive_damage,
    StatEnum.electric_damage:      CategoryEnum.mech_electric_damage,
    StatEnum.physical_resistance:  CategoryEnum.mech_physical_resistance,
    StatEnum.explosive_resistance: CategoryEnum.mech_explosive_resistance,
    StatEnum.electric_resistance:  CategoryEnum.mech_electric_resistance,
    StatEnum.hit_points:           CategoryEnum.mech_hp_increase,
    StatEnum.backfire:             CategoryEnum.mech_backfire_reduction,
}  # fmt: skip
MECH_SUMMARY_STATS: abc.Sequence[Stat] = (
    StatEnum.weight,
    StatEnum.hit_points,
    StatEnum.energy_capacity,
    StatEnum.regeneration,
    StatEnum.heat_capacity,
    StatEnum.cooling,
    StatEnum.physical_resistance,
    StatEnum.explosive_resistance,
    StatEnum.electric_resistance,
    StatEnum.bullets_capacity,
    StatEnum.rockets_capacity,
    StatEnum.walk,
    StatEnum.jump,
)


def get_item_stats(item: Item, /) -> StatsDict:
    """Get the stats of the item at its particular tier and level."""
    return item.stage.at(item.level)


def mech_summary(mech: Mech, /) -> StatsDict:
    """Construct a dict of the mech's stats, in order as they appear in workshop."""
    # inherits key order
    stats: StatsDict = dict.fromkeys(MECH_SUMMARY_STATS, 0)

    for item in filter(None, mech.iter_items()):
        item_stats = get_item_stats(item)

        for stat in MECH_SUMMARY_STATS:
            stats[stat] += item_stats.get(stat, 0)

    return stats


def mech_weight(mech: Mech, /) -> int:
    """Total mech's weight."""
    mass = 0

    for item in filter(None, mech.iter_items()):
        mass += get_item_stats(item).get(StatEnum.weight, 0)

    return mass


def apply_overload_penalties(
    stats: MutableStatsMapping, /, ruleset: BuildRules = DEFAULT_GAME_RULES.builds
) -> None:
    """TODO: docstring"""
    if (overload := stats.get(StatEnum.weight, 0) - ruleset.MAX_WEIGHT) > 0:
        for stat, penalty in ruleset.STAT_PENALTIES_PER_KG.items():
            stats[stat] -= overload * penalty


def buff_stats(
    stats: StatsMapping, /, buff_levels: ArenaShopMapping, *, skip_hp: bool = True
) -> StatsDict:
    """Return stats buffed according to the arena shop buff levels."""
    mutable_stats = dict(stats)

    for stat, value in mutable_stats.items():
        if (category := STAT_TO_CATEGORY.get(stat)) is None:
            continue

        if category == CategoryEnum.mech_hp_increase and skip_hp:
            continue

        data = get_category_data(category)
        level = buff_levels[category]
        addon = int(data.progression[level])
        buffed_value = value + addon if data.is_absolute else round(value * (1 + addon / 100))
        mutable_stats[stat] = buffed_value

    return mutable_stats


def max_stats(item: ItemData, /) -> StatsDict:
    """Return the max stats of an item."""
    stage = get_final_stage(item.start_stage)
    return stage.max()
