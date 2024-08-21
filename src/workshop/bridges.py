from collections import abc
from typing import TYPE_CHECKING, Any, Literal, TypeAlias
from typing_extensions import LiteralString, TypedDict

import fileformats
from serial.exceptions import DataError, DataPath, DataValueError, DataVersionError
from serial.utils import assert_key

from supermechs.abc.item import ItemID, Name
from supermechs.abc.item_pack import PackKey
from supermechs.arenashop import MAX_SHOP
from supermechs.enums.item import Type
from supermechs.enums.stats import Stat
from supermechs.item import Item, ItemData
from supermechs.mech import Mech, SlotMemberType, SlotType
from supermechs.tools.stats import buff_stats, max_stats

if TYPE_CHECKING:
    from supermechs.item_pack import ItemPack

__all__ = ("dump_mechs", "load_mechs")

_STAT_TO_WU_STAT: abc.Mapping[Stat, LiteralString] = {
    Stat.weight:                      "weight",
    Stat.hit_points:                  "health",
    Stat.energy_capacity:             "eneCap",
    Stat.regeneration:                "eneReg",
    Stat.heat_capacity:               "heaCap",
    Stat.cooling:                     "heaCol",
    Stat.bullets_capacity:            "bulletsCap",
    Stat.rockets_capacity:            "rocketsCap",
    Stat.physical_resistance:         "phyRes",
    Stat.explosive_resistance:        "expRes",
    Stat.electric_resistance:         "eleRes",
    Stat.physical_damage:             "phyDmg",
    Stat.physical_resistance_damage:  "phyResDmg",
    Stat.electric_damage:             "eleDmg",
    Stat.energy_damage:               "eneDmg",
    Stat.energy_capacity_damage:      "eneCapDmg",
    Stat.regeneration_damage:         "eneRegDmg",
    Stat.electric_resistance_damage:  "eleResDmg",
    Stat.explosive_damage:            "expDmg",
    Stat.heat_damage:                 "heaDmg",
    Stat.heat_capacity_damage:        "heaCapDmg",
    Stat.cooling_damage:              "heaColDmg",
    Stat.explosive_resistance_damage: "expResDmg",
    Stat.walk:                        "walk",
    Stat.jump:                        "jump",
    Stat.range:                       "range",
    Stat.push:                        "push",
    Stat.pull:                        "pull",
    Stat.recoil:                      "recoil",
    Stat.advance:                     "advance",
    Stat.retreat:                     "retreat",
    Stat.uses:                        "uses",
    Stat.backfire:                    "backfire",
    Stat.heat_generation:             "heaCost",
    Stat.energy_cost:                 "eneCost",
    Stat.bullets_cost:                "bulletsCost",
    Stat.rockets_cost:                "rocketsCost",
}  # fmt: skip
_WU_SLOT_TO_SLOT: abc.Mapping[LiteralString, SlotType] = {
    "torso":         Type.TORSO,
    "legs":          Type.LEGS,
    "sideWeapon1":   (Type.SIDE_WEAPON, 0),
    "sideWeapon2":   (Type.SIDE_WEAPON, 1),
    "sideWeapon3":   (Type.SIDE_WEAPON, 2),
    "sideWeapon4":   (Type.SIDE_WEAPON, 3),
    "topWeapon1":    (Type.TOP_WEAPON, 0),
    "topWeapon2":    (Type.TOP_WEAPON, 1),
    "drone":         Type.DRONE,
    "chargeEngine":  Type.CHARGE,
    "teleporter":    Type.TELEPORTER,
    "grapplingHook": Type.HOOK,
    "module1":       (Type.MODULE, 0),
    "module2":       (Type.MODULE, 1),
    "module3":       (Type.MODULE, 2),
    "module4":       (Type.MODULE, 3),
    "module5":       (Type.MODULE, 4),
    "module6":       (Type.MODULE, 5),
    "module7":       (Type.MODULE, 6),
    "module8":       (Type.MODULE, 7),
}  # fmt: skip
_TYPE_TO_WU_TYPE: abc.Mapping[Type, str] = {type: type.name for type in Type}
_TYPE_TO_WU_TYPE[Type.CHARGE] = "CHARGE_ENGINE"
_TYPE_TO_WU_TYPE[Type.HOOK] = "GRAPPLING_HOOK"

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
    return import_mechs(fileformats.json_decoder(data), pack)


# --------------------------------------------- lib2WU ---------------------------------------------


def _mech_items_in_wu_order(mech: Mech, /) -> abc.Iterator[SlotMemberType]:
    """Yield mech items in the order expected by WU."""
    yield mech.torso
    yield mech.legs
    yield from mech.iter_items(Type.SIDE_WEAPON)
    yield from mech.iter_items(Type.TOP_WEAPON)
    yield mech.drone
    yield mech.charge
    yield mech.teleporter
    yield mech.hook
    yield from mech.iter_items(Type.MODULE)


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
    return fileformats.json_encoder(export_mechs(mechs, pack_key), indent=True)


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

    data = fileformats.json_encoder(battle_items_no_modules)
    hash_ = hashlib.sha256(data).hexdigest()

    return {"name": str(player_name), "itemsHash": hash_, "mech": export_mech(mech, mech_name)}
