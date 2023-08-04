import typing as t

from attrs import asdict

from supermechs.api import (
    MAX_BUFFS,
    AnyStatsMapping,
    DisplayItem,
    InvItem,
    ItemData,
    ItemPack,
    Mech,
    SlotType,
)
from supermechs.item_stats import get_final_stage
from supermechs.platform import json_decoder, json_encoder, json_indented_encoder
from supermechs.typedefs import ID, Name
from supermechs.user_input import sanitize_string

# ------------------------------------------ typed dicts -------------------------------------------


class WUBattleItem(t.TypedDict):
    slotName: str
    id: ID
    name: Name
    type: str
    stats: AnyStatsMapping
    tags: dict[str, bool]
    element: str
    timesUsed: t.Literal[0]


class PartialMechJSON(t.TypedDict):
    name: str
    setup: list[ID]


class MechJSON(t.TypedDict):
    id: str
    name: str
    pack_key: str
    setup: list[ID]


class WUMech(t.TypedDict):
    name: str
    setup: list[ID]


class WUPlayer(t.TypedDict):
    name: str
    itemsHash: str
    mech: WUMech


class ExportedMechsJSONv1(t.TypedDict):
    version: t.Literal[1]
    mechs: dict[str, list[WUMech]]


class ExportedMechsJSONv2(t.TypedDict):
    version: t.Literal[2]
    # a mapping of pack keys to array of [smallest, largest] IDs they hold,
    # offset by previous packs.
    packs: dict[str, list[int]]
    mechs: list[WUMech]


WU_SLOT_NAMES = (
    "torso",
    "legs",
    "sideWeapon1",
    "sideWeapon2",
    "sideWeapon3",
    "sideWeapon4",
    "topWeapon1",
    "topWeapon2",
    "drone",
    "chargeEngine",
    "teleporter",
    "grapplingHook",
)
WU_MODULE_SLOT_NAMES = (
    "module1",
    "module2",
    "module3",
    "module4",
    "module5",
    "module6",
    "module7",
    "module8",
)
_slot_for_slot = {"chargeEngine": "charge", "teleporter": "tele", "grapplingHook": "hook"}


def wu_to_mech_slot(slot: str) -> str:
    """Convert workshop's internal slot name to the app's slot name."""
    if slot.startswith("side"):
        return "side" + slot[-1]

    if slot.startswith("top"):
        return "top" + slot[-1]

    if slot.startswith("module"):
        return "mod" + slot[-1]

    return _slot_for_slot.get(slot, slot)


def _mech_items_in_wu_order(mech: Mech) -> t.Iterator[SlotType]:
    """Yields mech items in the order expected by WU."""
    yield mech.torso
    yield mech.legs
    yield from mech.iter_items(weapons=True)
    yield mech.drone
    yield mech.charge
    yield mech.tele
    yield mech.hook
    yield from mech.iter_items(modules=True)


def _mech_items_ids_in_wu_order(mech: Mech) -> t.Iterator[int]:
    """Yields mech item IDs in WU compatible order."""
    return (0 if item is None else item.item.data.id for item in _mech_items_in_wu_order(mech))


def mech_to_id_str(mech: Mech, sep: str = "_") -> str:
    """Helper function to serialize a mech into a string of item IDs."""
    return sep.join(map(str, _mech_items_ids_in_wu_order(mech)))


# -------------------------------------------- imports ---------------------------------------------


def import_mech(data: WUMech, pack: "ItemPack") -> Mech:
    """Imports a mech from WU mech."""
    mech = Mech(name=sanitize_string(data["name"]))

    for item_id, wu_slot in zip(data["setup"], WU_SLOT_NAMES + WU_MODULE_SLOT_NAMES):
        slot = wu_to_mech_slot(wu_slot)
        if item_id != 0:
            item_data = pack.get_item_by_id(item_id)
            item = DisplayItem.from_data(item_data, item_data.start_stage, maxed=True)
            mech[slot] = InvItem.from_item(item)

        else:
            mech[slot] = None

    return mech


def import_mechs(
    json: ExportedMechsJSONv1, pack: "ItemPack"
) -> tuple[list[Mech], list[tuple[int, str]]]:
    """Imports mechs from parsed .JSON file."""

    # TODO: in 3.11 consider using ExceptionGroups to catch all problems at once
    try:
        version = json["version"]
        mech_list = json["mechs"][pack.key]
        # TODO: file can contain mechs from different pack than default

    except KeyError as e:
        raise ValueError(f'Malformed data: key "{e}" not found.') from e

    if version != 1:
        raise ValueError(f"Expected version = 1, got {version}")

    if not isinstance(mech_list, list):
        raise TypeError('Expected a list under "mechs" key')

    mechs: list[Mech] = []
    failed: list[tuple[int, str]] = []

    for i, wu_mech in enumerate(mech_list, 1):
        try:
            mechs.append(import_mech(wu_mech, pack))

        except Exception as e:
            failed.append((i, str(e)))

    return mechs, failed


def load_mechs(data: bytes, pack: "ItemPack") -> tuple[list[Mech], list[tuple[int, str]]]:
    """Loads mechs from bytes object, representing a .JSON file."""
    return import_mechs(json_decoder(data), pack)


# -------------------------------------------- exports ---------------------------------------------


def is_exportable(mech: Mech) -> bool:
    """Whether mech's items come from at most one pack."""

    if not mech.custom:
        return True

    packs = set[str]()

    for inv_item in mech.iter_items():
        if inv_item is None:
            continue

        packs.add(inv_item.item.data.pack_key)

    return len(packs) < 2


def export_mech(mech: Mech) -> WUMech:
    """Exports a mech to WU mech."""
    return {"name": mech.name, "setup": list(_mech_items_ids_in_wu_order(mech))}


def export_mechs(mechs: t.Iterable[Mech], pack_key: str) -> ExportedMechsJSONv1:
    """Exports mechs to WU compatible format."""
    wu_mechs = list(map(export_mech, mechs))
    return {"version": 1, "mechs": {pack_key: wu_mechs}}


def dump_mechs(mechs: t.Iterable[Mech], pack_key: str) -> bytes:
    """Dumps mechs into bytes representing a .JSON file."""
    return json_indented_encoder(export_mechs(mechs, pack_key))


def get_battle_item(item: ItemData, slot_name: str) -> WUBattleItem:
    # the keys here are ordered in same fashion as in WU, to maximize
    # chances that the hashes will be same
    final_stage = get_final_stage(item.start_stage)
    return {
        "slotName": slot_name,
        "element": item.element.name,
        "id": item.id,
        "name": item.name,
        "stats": MAX_BUFFS.buff_stats(final_stage.at(final_stage.max_level + 1)),
        "tags": asdict(item.tags),
        "timesUsed": 0,
        "type": item.type.name,
    }


def wu_serialize_mech(mech: Mech, player_name: str) -> WUPlayer:
    if mech.custom:
        raise TypeError("Cannot serialize a custom mech into WU format")

    serialized_items_without_modules = [
        None if inv_item is None else get_battle_item(inv_item.item.data, slot)
        for slot, inv_item in zip(WU_SLOT_NAMES, _mech_items_in_wu_order(mech))
    ]
    # lazy import
    import hashlib

    data = json_encoder(serialized_items_without_modules)
    hash = hashlib.sha256(data).hexdigest()

    return {"name": str(player_name), "itemsHash": hash, "mech": export_mech(mech)}
