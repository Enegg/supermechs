import typing as t

from .arenashop import ArenaShop
from .gamerules import DEFAULT_GAME_RULES, MechGameRules
from .item import Item, MutableStatsMapping, Stat, StatsMapping, TransformStage
from .item.stats import get_final_stage
from .mech import Mech

# fmt: off
STAT_TO_CATEGORY: t.Mapping[Stat, ArenaShop.Category] = {
    Stat.energy_capacity:      ArenaShop.Category.energy_capacity,
    Stat.regeneration:         ArenaShop.Category.energy_regeneration,
    Stat.energy_damage:        ArenaShop.Category.energy_damage,
    Stat.heat_capacity:        ArenaShop.Category.heat_capacity,
    Stat.cooling:              ArenaShop.Category.heat_cooling,
    Stat.heat_damage:          ArenaShop.Category.heat_damage,
    Stat.physical_damage:      ArenaShop.Category.physical_damage,
    Stat.explosive_damage:     ArenaShop.Category.explosive_damage,
    Stat.electric_damage:      ArenaShop.Category.electric_damage,
    Stat.physical_resistance:  ArenaShop.Category.physical_resistance,
    Stat.explosive_resistance: ArenaShop.Category.explosive_resistance,
    Stat.electric_resistance:  ArenaShop.Category.electric_resistance,
    Stat.hit_points:           ArenaShop.Category.total_hp,
    Stat.backfire:             ArenaShop.Category.backfire_reduction,
}
# fmt: on

MECH_SUMMARY_STATS: t.Sequence[Stat] = (
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


def mech_summary(mech: Mech, /) -> MutableStatsMapping:
    """A dict of the mech's stats, in order as they appear in workshop."""

    # inherits key order
    stats: MutableStatsMapping = dict.fromkeys(MECH_SUMMARY_STATS, 0)

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


def max_stats(stage: TransformStage, /) -> StatsMapping:
    """Return the max stats."""
    stage = get_final_stage(stage)
    return stage.at(stage.max_level)
