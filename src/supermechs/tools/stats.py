import attrs

from supermechs import abc
from supermechs.gamerules import BuildRules
from supermechs.mech import MechSummary

__all__ = (
    "apply_overload_penalty",
    "max_stats",
    "mech_summary",
    "mech_weight",
)


def mech_summary(mech: abc.Mech[abc.HasStats], /) -> abc.MechSummary:
    """Construct a dict of the mech's stats, in order as they appear in workshop."""
    summary = MechSummary()

    for item in mech.iter_items():
        stats = item.stats
        # fmt: off
        summary.weight               += stats.weight
        summary.hit_points           += stats.hit_points
        summary.energy_capacity      += stats.energy_capacity
        summary.regeneration         += stats.regeneration
        summary.heat_capacity        += stats.heat_capacity
        summary.cooling              += stats.cooling
        summary.physical_resistance  += stats.physical_resistance
        summary.explosive_resistance += stats.explosive_resistance
        summary.electric_resistance  += stats.electric_resistance
        summary.bullets_capacity     += stats.bullets_capacity
        summary.rockets_capacity     += stats.rockets_capacity
        # fmt: on

    if (legs := mech.legs) is not None:
        summary.walk += legs.stats.walk
        summary.jump += legs.stats.jump

    return summary


def mech_weight(mech: abc.Mech[abc.HasStats], /) -> float:
    """Total mech's weight."""
    return sum((item.stats.weight for item in mech.iter_items()), start=0.0)


def apply_overload_penalty(
    stats: abc.MechSummary, /, ruleset: BuildRules = BuildRules.default
) -> abc.MechSummary:
    """TODO: docstring."""
    overload = stats.weight - ruleset.safe_weight

    if overload <= 0:
        return stats

    penalty = overload * ruleset.hp_overload_penalty
    return attrs.evolve(stats, hit_points=stats.hit_points - penalty)


def max_stats(item: abc.HasStages, /) -> abc.ItemStats:
    """Return the max stats of an item."""
    return item.stages[-1].levels[-1].stats
