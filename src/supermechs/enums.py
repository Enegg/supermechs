from enum import Enum, auto

__all__ = ("ItemElementName", "ItemTagName", "ItemTypeName", "StageTierName", "StatName")


class ItemTypeName(str, Enum):
    __slots__ = ()

    TORSO = auto()
    LEGS = auto()
    DRONE = auto()
    SIDE_WEAPON = auto()
    TOP_WEAPON = auto()
    CHARGE = auto()
    TELEPORT = auto()
    HOOK = auto()
    SHIELD = auto()
    MODULE = auto()
    PERK = auto()
    KIT = auto()


class ItemElementName(str, Enum):
    __slots__ = ()

    PHYSICAL = auto()
    EXPLOSIVE = auto()
    ELECTRIC = auto()


class ItemTagName(str, Enum):
    __slots__ = ()

    roller = auto()
    melee = auto()
    sword = auto()
    legacy = auto()
    premium = auto()


class StageTierName(str, Enum):
    __slots__ = ()

    COMMON = auto()
    RARE = auto()
    EPIC = auto()
    LEGENDARY = auto()
    MYTHICAL = auto()
    DIVINE = auto()
    PERK = auto()


class SlotName(str, Enum):
    __slots__ = ()

    torso = auto()
    legs = auto()
    drone = auto()
    charge = auto()
    teleport = auto()
    hook = auto()
    shield = auto()
    perk = auto()


class SideWeaponSlotName(str, Enum):
    __slots__ = ()

    side_weapon_1 = auto()
    side_weapon_2 = auto()
    side_weapon_3 = auto()
    side_weapon_4 = auto()


class TopWeaponSlotName(str, Enum):
    __slots__ = ()

    top_weapon_1 = auto()
    top_weapon_2 = auto()


class ModuleSlotName(str, Enum):
    __slots__ = ()

    module_1 = auto()
    module_2 = auto()
    module_3 = auto()
    module_4 = auto()
    module_5 = auto()
    module_6 = auto()
    module_7 = auto()
    module_8 = auto()


class StatName(str, Enum):
    __slots__ = ()
    # summary stats
    weight = auto()
    hit_points = auto()
    energy_capacity = auto()
    regeneration = auto()
    heat_capacity = auto()
    cooling = auto()
    bullets_capacity = auto()
    rockets_capacity = auto()
    physical_resistance = auto()
    explosive_resistance = auto()
    electric_resistance = auto()
    # physical weapons
    physical_damage = auto()
    physical_damage_addon = auto()
    physical_resistance_damage = auto()
    # energy weapons
    electric_damage = auto()
    electric_damage_addon = auto()
    energy_damage = auto()
    energy_capacity_damage = auto()
    regeneration_damage = auto()
    electric_resistance_damage = auto()
    # heat weapons
    explosive_damage = auto()
    explosive_damage_addon = auto()
    heat_damage = auto()
    heat_capacity_damage = auto()
    cooling_damage = auto()
    explosive_resistance_damage = auto()
    # mobility
    walk = auto()
    jump = auto()
    range = auto()
    range_addon = auto()
    push = auto()
    pull = auto()
    recoil = auto()
    advance = auto()
    retreat = auto()
    # costs
    uses = auto()
    backfire = auto()
    heat_generation = auto()
    energy_cost = auto()
    bullets_cost = auto()
    rockets_cost = auto()
