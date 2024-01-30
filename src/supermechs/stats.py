from collections import abc
from typing import Any, TypeAlias

from .arenashop import ArenaShopMapping, Category, get_data
from .gamerules import DEFAULT_GAME_RULES, MechGameRules
from .item import Item, MutableStatsMapping, Stat, StatsMapping, TransformStage
from .item.stats import get_final_stage
from .mech import Mech

StatsDict: TypeAlias = dict[Stat, Any]
"""Concrete mapping type of item stats to values."""
# fmt: off
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
}
# fmt: on
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


def get_item_stats(item: Item, /) -> StatsMapping:
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


def apply_overload_penalties(
    stats: MutableStatsMapping, /, ruleset: MechGameRules = DEFAULT_GAME_RULES.mech
) -> None:
    if (overload := stats[Stat.weight] - ruleset.MAX_WEIGHT) > 0:
        for stat, penalty in ruleset.STAT_PENALTIES_PER_KG.items():
            stats[stat] -= overload * penalty


def _apply_absolute(value: Any, addon: Any) -> Any:
    return value + addon


def _apply_percent(value: Any, percent: Any) -> Any:
    return round(value * (1 + percent / 100))


def buff_stats(
    stats: StatsMapping, /, buff_levels: ArenaShopMapping, *, skip_hp: bool = True
) -> StatsMapping:
    """Returns stats buffed according to buff levels."""
    mutable_stats = dict(stats)

    for stat, value in mutable_stats.items():
        if (category := STAT_TO_CATEGORY.get(stat)) is None:
            continue

        if category is Category.total_hp and skip_hp:
            continue

        data = get_data(category)
        level = buff_levels[category]
        addon = data.progression[level]
        method = _apply_absolute if data.is_absolute else _apply_percent
        mutable_stats[stat] = method(value, addon)

    return mutable_stats


def max_stats(stage: TransformStage, /) -> StatsMapping:
    """Return the max stats."""
    stage = get_final_stage(stage)
    return stage.at(stage.max_level)
