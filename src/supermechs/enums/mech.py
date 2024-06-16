from enum import auto

from ._base import PartialEnum

__all__ = ("ModuleEnum", "SideWeaponEnum", "TopWeaponEnum")


class SideWeaponEnum(str, PartialEnum):
    SIDE_WEAPON_1 = auto()
    SIDE_WEAPON_2 = auto()
    SIDE_WEAPON_3 = auto()
    SIDE_WEAPON_4 = auto()


class TopWeaponEnum(str, PartialEnum):
    TOP_WEAPON_1 = auto()
    TOP_WEAPON_2 = auto()


class ModuleEnum(str, PartialEnum):
    MODULE_1 = auto()
    MODULE_2 = auto()
    MODULE_3 = auto()
    MODULE_4 = auto()
    MODULE_5 = auto()
    MODULE_6 = auto()
    MODULE_7 = auto()
    MODULE_8 = auto()
