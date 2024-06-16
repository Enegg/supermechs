from collections import abc
from typing import TYPE_CHECKING, Any, Literal, TypeAlias
from typing_extensions import LiteralString, TypedDict

import smjson
from serial.exceptions import DataError, DataPath, DataValueError, DataVersionError
from serial.utils import assert_key

from supermechs.abc.item import ItemID, Name
from supermechs.abc.item_pack import PackKey
from supermechs.arenashop import MAX_SHOP
from supermechs.enums.item import TypeEnum
from supermechs.enums.stats import StatEnum
from supermechs.item import Item, ItemData
from supermechs.mech import Mech, SlotMemberType, SlotType
from supermechs.tools.stats import buff_stats, max_stats

if TYPE_CHECKING:
    from supermechs.item_pack import ItemPack

__all__ = ("dump_mechs", "load_mechs")

_STAT_TO_WU_STAT: abc.Mapping[StatEnum, LiteralString] = {
    StatEnum.weight:                      "weight",
    StatEnum.hit_points:                  "health",
    StatEnum.energy_capacity:             "eneCap",
    StatEnum.regeneration:                "eneReg",
    StatEnum.heat_capacity:               "heaCap",
    StatEnum.cooling:                     "heaCol",
    StatEnum.bullets_capacity:            "bulletsCap",
    StatEnum.rockets_capacity:            "rocketsCap",
    StatEnum.physical_resistance:         "phyRes",
    StatEnum.explosive_resistance:        "expRes",
    StatEnum.electric_resistance:         "eleRes",
    StatEnum.physical_damage:             "phyDmg",
    StatEnum.physical_resistance_damage:  "phyResDmg",
    StatEnum.electric_damage:             "eleDmg",
    StatEnum.energy_damage:               "eneDmg",
    StatEnum.energy_capacity_damage:      "eneCapDmg",
    StatEnum.regeneration_damage:         "eneRegDmg",
    StatEnum.electric_resistance_damage:  "eleResDmg",
    StatEnum.explosive_damage:            "expDmg",
    StatEnum.heat_damage:                 "heaDmg",
    StatEnum.heat_capacity_damage:        "heaCapDmg",
    StatEnum.cooling_damage:              "heaColDmg",
    StatEnum.explosive_resistance_damage: "expResDmg",
    StatEnum.walk:                        "walk",
    StatEnum.jump:                        "jump",
    StatEnum.range:                       "range",
    StatEnum.push:                        "push",
    StatEnum.pull:                        "pull",
    StatEnum.recoil:                      "recoil",
    StatEnum.advance:                     "advance",
    StatEnum.retreat:                     "retreat",
    StatEnum.uses:                        "uses",
    StatEnum.backfire:                    "backfire",
    StatEnum.heat_generation:             "heaCost",
    StatEnum.energy_cost:                 "eneCost",
    StatEnum.bullets_cost:                "bulletsCost",
    StatEnum.rockets_cost:                "rocketsCost",
}  # fmt: skip
_WU_SLOT_TO_SLOT: abc.Mapping[LiteralString, SlotType] = {
    "torso":         TypeEnum.TORSO,
    "legs":          TypeEnum.LEGS,
    "sideWeapon1":   (TypeEnum.SIDE_WEAPON, 0),
    "sideWeapon2":   (TypeEnum.SIDE_WEAPON, 1),
    "sideWeapon3":   (TypeEnum.SIDE_WEAPON, 2),
    "sideWeapon4":   (TypeEnum.SIDE_WEAPON, 3),
    "topWeapon1":    (TypeEnum.TOP_WEAPON, 0),
    "topWeapon2":    (TypeEnum.TOP_WEAPON, 1),
    "drone":         TypeEnum.DRONE,
    "chargeEngine":  TypeEnum.CHARGE,
    "teleporter":    TypeEnum.TELEPORTER,
    "grapplingHook": TypeEnum.HOOK,
    "module1":       (TypeEnum.MODULE, 0),
    "module2":       (TypeEnum.MODULE, 1),
    "module3":       (TypeEnum.MODULE, 2),
    "module4":       (TypeEnum.MODULE, 3),
    "module5":       (TypeEnum.MODULE, 4),
    "module6":       (TypeEnum.MODULE, 5),
    "module7":       (TypeEnum.MODULE, 6),
    "module8":       (TypeEnum.MODULE, 7),
}  # fmt: skip
_TYPE_TO_WU_TYPE: abc.Mapping[TypeEnum, str] = {type: type.name for type in TypeEnum}
_TYPE_TO_WU_TYPE[TypeEnum.CHARGE] = "CHARGE_ENGINE"
_TYPE_TO_WU_TYPE[TypeEnum.HOOK] = "GRAPPLING_HOOK"

# ------------------------------------------ typed dicts -------------------------------------------
SetupID: TypeAlias = ItemID | Literal[0]


class WUBattleItem(TypedDict):
    slotName: str
    id: ItemID
    name: Name
    type: str
    stats: abc.Mapping[str, int | list[int]]
    tags: abc.Mapping[str, bool]
    element: str
    timesUsed: Literal[0]


class WUMech(TypedDict):
    name: str
    setup: abc.Sequence[SetupID]


class WUPlayer(TypedDict):
    name: str
    itemsHash: str
    mech: WUMech


class ExportedMechs(TypedDict):
    version: Literal[1]
    mechs: abc.Mapping[str, abc.Sequence[WUMech]]


# --------------------------------------------- WU2lib ---------------------------------------------
_WU_SLOT_NAMES = tuple(_WU_SLOT_TO_SLOT.keys())


def import_mech(data: WUMech, pack: "ItemPack", *, at: DataPath = ()) -> tuple[Mech, str]:
    """Import a mech from WU mech."""
    key = "setup"
    setup = assert_key(list[int], data, key, at=at)
    name = assert_key(str, data, "name", at=at)

    unknown = setup - pack.items.keys()
    unknown.discard(0)

    if unknown:
        msg = f"Unknown item IDs: {', '.join(map(str, sorted(unknown)))}"
        raise DataValueError(msg, at=(*at, key))

    mech = Mech()
    expected_len = len(_WU_SLOT_NAMES)
    received_len = len(setup)
    if received_len != expected_len:
        msg = f"Expected {expected_len} elements, got {received_len}"
        raise DataValueError(msg, at=(*at, key))

    for item_id, wu_slot in zip(setup, _WU_SLOT_NAMES, strict=True):
        slot = _WU_SLOT_TO_SLOT[wu_slot]
        if item_id != 0:
            item_data = pack.get_item(ItemID(item_id))
            mech[slot] = Item.maxed(item_data)

        else:
            mech[slot] = None

    return mech, name


def import_mechs(
    data: ExportedMechs, pack: "ItemPack"
) -> tuple[list[tuple[Mech, str]], list[DataError]]:
    """Import mechs from parsed .JSON file."""
    version = assert_key(str, data, "version")

    if version != "1":
        raise DataVersionError(version, "1")

    at = ("mechs",)
    all_mechs = assert_key(dict[PackKey, object], data, at[0])
    mech_list = assert_key(list[Any], all_mechs, pack.data.key, at=at)
    # TODO: file can contain mechs from different pack than default

    mechs: list[tuple[Mech, str]] = []
    failed: list[DataError] = []

    for i, wu_mech in enumerate(mech_list):
        try:
            mechs.append(import_mech(wu_mech, pack, at=(*at, pack.data.key, i)))

        except DataError as exc:
            failed.append(exc)

    return mechs, failed


def load_mechs(data: bytes, pack: "ItemPack") -> tuple[list[tuple[Mech, str]], list[DataError]]:
    """Load mechs from bytes object, representing a .JSON file."""
    return import_mechs(smjson.loads(data), pack)


# --------------------------------------------- lib2WU ---------------------------------------------


def _mech_items_in_wu_order(mech: Mech, /) -> abc.Iterator[SlotMemberType]:
    """Yield mech items in the order expected by WU."""
    yield mech.torso
    yield mech.legs
    yield from mech.iter_items(TypeEnum.SIDE_WEAPON)
    yield from mech.iter_items(TypeEnum.TOP_WEAPON)
    yield mech.drone
    yield mech.charge
    yield mech.teleporter
    yield mech.hook
    yield from mech.iter_items(TypeEnum.MODULE)


def _mech_item_ids_in_wu_order(mech: Mech, /) -> abc.Iterator[SetupID]:
    """Yield mech item IDs in WU compatible order."""
    return (0 if item is None else item.data.id for item in _mech_items_in_wu_order(mech))


def is_exportable(mech: Mech, /) -> bool:
    """Whether mech's items come from at most one pack."""
    items = filter(None, mech.iter_items())
    try:
        first_key = next(items).data.pack_key

    except StopIteration:
        return True

    return all(item.data.pack_key == first_key for item in items)


def export_mech(mech: Mech, /, name: str) -> WUMech:
    """Export a mech to WU mech."""
    return {"name": name, "setup": list(_mech_item_ids_in_wu_order(mech))}


def export_mechs(mechs: abc.Iterable[tuple[str, Mech]], pack_key: str) -> ExportedMechs:
    """Export mechs to WU compatible format."""
    wu_mechs = [export_mech(mech, name) for name, mech in mechs]
    return {"version": 1, "mechs": {pack_key: wu_mechs}}


def dump_mechs(mechs: abc.Iterable[tuple[str, Mech]], pack_key: str) -> bytes:
    """Dump mechs into bytes representing a .JSON file."""
    return smjson.dumps(export_mechs(mechs, pack_key), indent=True)


def get_battle_item(item: ItemData, slot_name: LiteralString) -> WUBattleItem:
    # the keys here are ordered in same fashion as in WU, to maximize
    # chances that the hashes will be same
    # FIXME: stats no longer contain lists
    stats = {
        _STAT_TO_WU_STAT[key]: value if isinstance(value, int) else list(value)
        for key, value in buff_stats(max_stats(item), MAX_SHOP).items()
    }
    return {
        "slotName": slot_name,
        "element": item.element.name,
        "id": item.id,
        "name": item.name,
        "stats": stats,
        "tags": item.tags._asdict(),
        "timesUsed": 0,
        "type": _TYPE_TO_WU_TYPE[item.type],
    }


def get_player(mech: Mech, mech_name: str, player_name: str) -> WUPlayer:
    battle_items_no_modules = [
        None if item is None else get_battle_item(item.data, slot)
        for slot, item in zip(_WU_SLOT_NAMES[:-8], _mech_items_in_wu_order(mech), strict=False)
    ]
    import hashlib

    data = smjson.dumps(battle_items_no_modules)
    hash_ = hashlib.sha256(data).hexdigest()

    return {"name": str(player_name), "itemsHash": hash_, "mech": export_mech(mech, mech_name)}
