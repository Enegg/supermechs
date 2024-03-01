from collections import abc

from ..abc.arenashop import ArenaShopMapping
from ..abc.stats import MutableStatsMapping, StatsMapping
from ..enums.arenashop import Category
from ..enums.stats import Stat
from ..gamerules import DEFAULT_GAME_RULES, BuildRules
from ..item import Item, ItemData
from ..mech import Mech
from ..stats import StatsDict, get_final_stage

__all__ = (
    "apply_overload_penalties",
    "buff_stats",
    "get_item_stats",
    "max_stats",
    "mech_summary",
    "mech_weight",
)

STAT_TO_CATEGORY: abc.Mapping[Stat, Category] = {
    Stat.energy_capacity:      Category.energy_capacity,
    Stat.regeneration:         Category.energy_regeneration,
    Stat.energy_damage:        Category.energy_damage,
    Stat.heat_capacity:        Category.heat_capacity,
    Stat.cooling:              Category.heat_cooling,
    Stat.heat_damage:          Category.heat_damage,
    Stat.physical_damage:      Category.physical_damage,
    Stat.explosive_damage:     Category.explosive_damage,
    Stat.electric_damage:      Category.electric_damage,
    Stat.physical_resistance:  Category.physical_resistance,
    Stat.explosive_resistance: Category.explosive_resistance,
    Stat.electric_resistance:  Category.electric_resistance,
    Stat.hit_points:           Category.total_hp,
    Stat.backfire:             Category.backfire_reduction,
}  # fmt: skip
MECH_SUMMARY_STATS: abc.Sequence[Stat] = (
    Stat.weight,
    Stat.hit_points,
    Stat.energy_capacity,
    Stat.regeneration,
    Stat.heat_capacity,
    Stat.cooling,
    Stat.physical_resistance,
    Stat.explosive_resistance,
    Stat.electric_resistance,
    Stat.bullets_capacity,
    Stat.rockets_capacity,
    Stat.walk,
    Stat.jump,
)


def get_item_stats(item: Item, /) -> StatsDict:
    """The stats of the item at its particular tier and level."""
    return item.stage.at(item.level)


def mech_summary(mech: Mech, /) -> StatsDict:
    """A dict of the mech's stats, in order as they appear in workshop."""
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
        mass += get_item_stats(item).get(Stat.weight, 0)

    return mass


def apply_overload_penalties(
    stats: MutableStatsMapping, /, ruleset: BuildRules = DEFAULT_GAME_RULES.builds
) -> None:
    """TODO: docstring"""
    if (overload := stats.get(Stat.weight, 0) - ruleset.MAX_WEIGHT) > 0:
        for stat, penalty in ruleset.STAT_PENALTIES_PER_KG.items():
            stats[stat] -= overload * penalty


def buff_stats(
    stats: StatsMapping, /, buff_levels: ArenaShopMapping, *, skip_hp: bool = True
) -> StatsDict:
    """Returns stats buffed according to buff levels."""
    mutable_stats = dict(stats)

    for stat, value in mutable_stats.items():
        if (category := STAT_TO_CATEGORY.get(stat)) is None:
            continue

        if category is Category.total_hp and skip_hp:
            continue

        data = category.data
        level = buff_levels[category]
        addon = int(data.progression[level])
        buffed_value = value + addon if data.is_absolute else round(value * (1 + addon / 100))
        mutable_stats[stat] = buffed_value

    return mutable_stats


def max_stats(item: ItemData, /) -> StatsDict:
    """Return the max stats of an item."""
    stage = get_final_stage(item.start_stage)
    return stage.max()
