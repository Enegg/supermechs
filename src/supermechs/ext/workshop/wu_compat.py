import typing as t
import typing_extensions as tex

from attrs import asdict

from supermechs.arena_buffs import MAX_BUFFS
from supermechs.item import Item, ItemData, Stat, Type
from supermechs.mech import Mech, SlotType
from supermechs.platform import _set_in_use, json_decoder, json_encoder
from supermechs.stats import max_stats
from supermechs.typeshed import ID, Name

from supermechs.ext.deserializers.errors import (
    DataError,
    DataKeyError,
    DataTypeAtKeyError,
    DataVersionError,
)
from supermechs.ext.deserializers.utils import assert_type

if t.TYPE_CHECKING:
    from supermechs.item_pack import ItemPack

__all__ = ("load_mechs", "dump_mechs")

_set_in_use(__name__)

# fmt: off
_STAT_TO_WU_STAT: dict[Stat, tex.LiteralString] = {
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
}
_WU_SLOT_TO_SLOT: dict[tex.LiteralString, Mech.Slot] = {
    "torso":         Mech.Slot.TORSO,
    "legs":          Mech.Slot.LEGS,
    "sideWeapon1":   Mech.Slot.SIDE_WEAPON_1,
    "sideWeapon2":   Mech.Slot.SIDE_WEAPON_2,
    "sideWeapon3":   Mech.Slot.SIDE_WEAPON_3,
    "sideWeapon4":   Mech.Slot.SIDE_WEAPON_4,
    "topWeapon1":    Mech.Slot.TOP_WEAPON_1,
    "topWeapon2":    Mech.Slot.TOP_WEAPON_2,
    "drone":         Mech.Slot.DRONE,
    "chargeEngine":  Mech.Slot.CHARGE,
    "teleporter":    Mech.Slot.TELEPORTER,
    "grapplingHook": Mech.Slot.HOOK,
    "module1":       Mech.Slot.MODULE_1,
    "module2":       Mech.Slot.MODULE_2,
    "module3":       Mech.Slot.MODULE_3,
    "module4":       Mech.Slot.MODULE_4,
    "module5":       Mech.Slot.MODULE_5,
    "module6":       Mech.Slot.MODULE_6,
    "module7":       Mech.Slot.MODULE_7,
    "module8":       Mech.Slot.MODULE_8,
}
# fmt: on
_TYPE_TO_WU_TYPE: dict[Type, tex.LiteralString] = {type: type.name for type in Type}
_TYPE_TO_WU_TYPE[Type.CHARGE] = "CHARGE_ENGINE"
_TYPE_TO_WU_TYPE[Type.HOOK] = "GRAPPLING_HOOK"

# ------------------------------------------ typed dicts -------------------------------------------


class WUBattleItem(t.TypedDict):
    slotName: tex.LiteralString
    id: ID
    name: Name
    type: tex.LiteralString
    stats: dict[str, int | list[int]]
    tags: t.Mapping[str, bool]
    element: tex.LiteralString
    timesUsed: t.Literal[0]


class WUMech(t.TypedDict):
    name: str
    setup: t.Sequence[ID]


class WUPlayer(t.TypedDict):
    name: str
    itemsHash: str
    mech: WUMech


class ExportedMechsJSON(t.TypedDict):
    version: t.Literal[1]
    mechs: t.Mapping[str, t.Sequence[WUMech]]


# --------------------------------------------- WU2lib ---------------------------------------------


def import_mech(data: WUMech, pack: "ItemPack") -> Mech:
    """Imports a mech from WU mech."""
    setup = assert_type(list, data["setup"], cast=False)
    mech = Mech(name=assert_type(str, data["name"]))

    unknown = setup - pack.items.keys()
    unknown.discard(0)

    if unknown:
        msg = f"Mech setup contains unknown item IDs: {', '.join(map(str, sorted(unknown)))}"
        raise DataError(msg)

    for item_id, wu_slot in zip(setup, _WU_SLOT_NAMES):
        slot = _WU_SLOT_TO_SLOT[wu_slot]
        if item_id != 0:
            item_data = pack.get_item(item_id)
            mech[slot] = Item.from_data(item_data, maxed=True)

        else:
            mech[slot] = None

    return mech


def import_mechs(
    data: ExportedMechsJSON, pack: "ItemPack"
) -> tuple[t.Sequence[Mech], t.Sequence[tuple[int, Exception]]]:
    """Imports mechs from parsed .JSON file."""

    try:
        version = str(data["version"])
        mech_list = assert_type(list, data["mechs"][pack.key])
        # TODO: file can contain mechs from different pack than default

    except KeyError as err:
        raise DataKeyError(err) from None

    if version != "1":
        raise DataVersionError(version, "1")

    if not isinstance(mech_list, list):
        raise DataTypeAtKeyError(type(mech_list), list, "mechs")

    mechs: list[Mech] = []
    failed: list[tuple[int, Exception]] = []

    for i, wu_mech in enumerate(mech_list, 1):
        try:
            mechs.append(import_mech(wu_mech, pack))

        except Exception as err:
            failed.append((i, err))

    return mechs, failed


def load_mechs(
    data: bytes, pack: "ItemPack"
) -> tuple[t.Sequence[Mech], t.Sequence[tuple[int, Exception]]]:
    """Loads mechs from bytes object, representing a .JSON file."""
    return import_mechs(json_decoder(data), pack)


# --------------------------------------------- lib2WU ---------------------------------------------


_WU_SLOT_NAMES = tuple(_WU_SLOT_TO_SLOT)


def _mech_items_in_wu_order(mech: Mech, /) -> t.Iterator[SlotType]:
    """Yields mech items in the order expected by WU."""
    yield mech.torso
    yield mech.legs
    yield from mech.iter_items(Type.SIDE_WEAPON)
    yield from mech.iter_items(Type.TOP_WEAPON)
    yield mech.drone
    yield mech.charge
    yield mech.teleporter
    yield mech.hook
    yield from mech.iter_items(Type.MODULE)


def _mech_item_ids_in_wu_order(mech: Mech, /) -> t.Iterator[int]:
    """Yields mech item IDs in WU compatible order."""
    return (0 if item is None else item.data.id for item in _mech_items_in_wu_order(mech))


def is_exportable(mech: Mech, /) -> bool:
    """Whether mech's items come from at most one pack."""

    items = filter(None, mech.iter_items())
    try:
        first_key = next(items).data.pack_key

    except StopIteration:
        return True

    return all(item.data.pack_key == first_key for item in items)


def export_mech(mech: Mech, /) -> WUMech:
    """Exports a mech to WU mech."""
    return {"name": mech.name, "setup": list(_mech_item_ids_in_wu_order(mech))}


def export_mechs(mechs: t.Iterable[Mech], pack_key: str) -> ExportedMechsJSON:
    """Exports mechs to WU compatible format."""
    wu_mechs = list(map(export_mech, mechs))
    return {"version": 1, "mechs": {pack_key: wu_mechs}}


def dump_mechs(mechs: t.Iterable[Mech], pack_key: str) -> bytes:
    """Dumps mechs into bytes representing a .JSON file."""
    return json_encoder(export_mechs(mechs, pack_key), True)


def get_battle_item(item: ItemData, slot_name: tex.LiteralString) -> WUBattleItem:
    # the keys here are ordered in same fashion as in WU, to maximize
    # chances that the hashes will be same
    stats = {
        _STAT_TO_WU_STAT[key]: value if isinstance(value, int) else list(value)
        for key, value in MAX_BUFFS.buff_stats(max_stats(item.start_stage)).items()
    }
    return {
        "slotName": slot_name,
        "element": item.element.name,
        "id": item.id,
        "name": item.name,
        "stats": stats,
        "tags": asdict(item.tags),
        "timesUsed": 0,
        "type": _TYPE_TO_WU_TYPE[item.type],
    }


def get_player(mech: Mech, player_name: str) -> WUPlayer:
    serialized_items_without_modules = [
        None if item is None else get_battle_item(item.data, slot)
        for slot, item in zip(_WU_SLOT_NAMES[:-8], _mech_items_in_wu_order(mech))
    ]
    # lazy import
    import hashlib

    data = json_encoder(serialized_items_without_modules)
    hash = hashlib.sha256(data).hexdigest()

    return {"name": str(player_name), "itemsHash": hash, "mech": export_mech(mech)}
