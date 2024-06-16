from enum import auto, unique

from ._base import PartialEnum

__all__ = ("CategoryEnum",)


@unique
class CategoryEnum(str, PartialEnum):
    """Enumeration of arena shop categories."""

    # fmt: off
    mech_energy_capacity       = auto()
    mech_energy_regeneration   = auto()
    mech_energy_damage         = auto()
    mech_heat_capacity         = auto()
    mech_heat_cooling          = auto()
    mech_heat_damage           = auto()
    mech_physical_damage       = auto()
    mech_explosive_damage      = auto()
    mech_electric_damage       = auto()
    mech_physical_resistance   = auto()
    mech_explosive_resistance  = auto()
    mech_electric_resistance   = auto()
    campaign_fuel_capacity     = auto()
    campaign_fuel_regeneration = auto()
    mech_hp_increase           = auto()
    arena_gold_increase        = auto()
    campaign_gold_increase     = auto()
    titan_damage               = auto()
    base_crafting_cost         = auto()
    base_crafting_speed        = auto()
    base_upgrade_speed         = auto()
    fortune_boxes              = auto()
    mech_backfire_reduction    = auto()
    titan_reward               = auto()
    # fmt: on
