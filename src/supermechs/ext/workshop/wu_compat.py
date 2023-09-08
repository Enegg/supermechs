import typing as t

from attrs import asdict

from supermechs.arena_buffs import ArenaBuffs
from supermechs.enums import Type
from supermechs.errors import MalformedData, UnknownDataVersion
from supermechs.item_stats import AnyStatsMapping, max_stats
from supermechs.models.item import Item, ItemData
from supermechs.models.mech import Mech, SlotSelectorType, SlotType
from supermechs.platform import compact_json_encoder, indented_json_encoder, json_decoder
from supermechs.typedefs import ID, Name
from supermechs.utils import assert_type

if t.TYPE_CHECKING:
    from supermechs.item_pack import ItemPack

__all__ = ("load_mechs", "dump_mechs")

# ------------------------------------------ typed dicts -------------------------------------------


class WUBattleItem(t.TypedDict):
    slotName: str
    id: ID
    name: Name
    type: str
    stats: AnyStatsMapping
    tags: t.Mapping[str, bool]
    element: str
    timesUsed: t.Literal[0]


class WUMech(t.TypedDict):
    name: str
    setup: t.Sequence[ID]


class WUPlayer(t.TypedDict):
    name: str
    itemsHash: str
    mech: WUMech


class ExportedMechsJSONv1(t.TypedDict):
    version: t.Literal[1]
    mechs: t.Mapping[str, t.Sequence[WUMech]]


class ExportedMechsJSONv2(t.TypedDict):
    version: t.Literal[2]
    # a mapping of pack keys to array of [smallest, largest] IDs they hold,
    # offset by previous packs.
    packs: t.Mapping[str, t.Sequence[int]]
    mechs: t.Sequence[WUMech]


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
_slot_for_slot: t.Mapping[str, Type] = {
    "chargeEngine": Type.CHARGE, "teleporter": Type.TELEPORTER, "grapplingHook": Type.HOOK
}


def wu_to_mech_slot(slot: str, /) -> SlotSelectorType:
    """Convert workshop's internal slot name to the app's slot name."""
    if slot.startswith("side"):
        return Type.SIDE_WEAPON, int(slot[-1]) - 1

    if slot.startswith("top"):
        return Type.TOP_WEAPON, int(slot[-1]) - 1

    if slot.startswith("module"):
        return Type.MODULE, int(slot[-1]) - 1

    return _slot_for_slot.get(slot) or Type.of_name(slot)


def _mech_items_in_wu_order(mech: Mech) -> t.Iterator[SlotType]:
    """Yields mech items in the order expected by WU."""
    yield mech.torso
    yield mech.legs
    yield from mech.iter_items("weapons")
    yield mech.drone
    yield mech.charge
    yield mech.teleporter
    yield mech.hook
    yield from mech.iter_items(Type.MODULE)


def _mech_items_ids_in_wu_order(mech: Mech) -> t.Iterator[int]:
    """Yields mech item IDs in WU compatible order."""
    return (0 if item is None else item.data.id for item in _mech_items_in_wu_order(mech))


def mech_to_id_str(mech: Mech, sep: str = "_") -> str:
    """Helper function to serialize a mech into a string of item IDs."""
    return sep.join(map(str, _mech_items_ids_in_wu_order(mech)))


# -------------------------------------------- imports ---------------------------------------------


def import_mech(data: WUMech, pack: "ItemPack") -> Mech:
    """Imports a mech from WU mech."""
    setup = assert_type(list, data["setup"], cast=False)
    mech = Mech(name=assert_type(str, data["name"]))

    unknown = setup - pack.items.keys()
    unknown.discard(0)

    if unknown:
        raise MalformedData(
            f"Mech setup contains unknown item IDs: {', '.join(map(str, (sorted(unknown))))}",
            setup
        )

    for item_id, wu_slot in zip(setup, WU_SLOT_NAMES + WU_MODULE_SLOT_NAMES):
        slot = wu_to_mech_slot(wu_slot)
        if item_id != 0:
            item_data = pack.get_item_by_id(item_id)
            mech[slot] = Item.from_data(item_data, maxed=True)

        else:
            mech[slot] = None

    return mech


def import_mechs(
    data: ExportedMechsJSONv1, pack: "ItemPack"
) -> tuple[t.Sequence[Mech], t.Sequence[tuple[int, Exception]]]:
    """Imports mechs from parsed .JSON file."""

    try:
        version = str(data["version"])
        mech_list = assert_type(list, data["mechs"][pack.key])
        # TODO: file can contain mechs from different pack than default

    except KeyError as err:
        raise MalformedData(f'Malformed data: key "{err}" not found.') from err

    if version != "1":
        raise UnknownDataVersion("mech data", version, "1")

    if not isinstance(mech_list, list):
        raise MalformedData('Expected a list under "mechs" key', mech_list)

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


# -------------------------------------------- exports ---------------------------------------------


def is_exportable(mech: Mech) -> bool:
    """Whether mech's items come from at most one pack."""

    if not mech.custom:
        return True

    packs = set[str]()

    for item in mech.iter_items():
        if item is None:
            continue

        packs.add(item.data.pack_key)

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
    return indented_json_encoder(export_mechs(mechs, pack_key))


def get_battle_item(item: ItemData, slot_name: str) -> WUBattleItem:
    # the keys here are ordered in same fashion as in WU, to maximize
    # chances that the hashes will be same
    return {
        "slotName": slot_name,
        "element": item.element.name,
        "id": item.id,
        "name": item.name,
        "stats": ArenaBuffs.maxed().buff_stats(max_stats(item.start_stage)),
        "tags": asdict(item.tags),
        "timesUsed": 0,
        "type": item.type.name,
    }


def get_player(mech: Mech, player_name: str) -> WUPlayer:
    if mech.custom:
        raise TypeError("Cannot serialize a custom mech into WU format")

    serialized_items_without_modules = [
        None if item is None else get_battle_item(item.data, slot)
        for slot, item in zip(WU_SLOT_NAMES, _mech_items_in_wu_order(mech))
    ]
    # lazy import
    import hashlib

    data = compact_json_encoder(serialized_items_without_modules)
    hash = hashlib.sha256(data).hexdigest()

    return {"name": str(player_name), "itemsHash": hash, "mech": export_mech(mech)}
