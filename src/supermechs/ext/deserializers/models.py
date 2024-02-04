import types
import typing
from collections import abc
from typing import Any, NoReturn, TypeAlias

from exceptiongroup import ExceptionGroup

from .errors import DataError, DataKeyError, DataTypeAtKeyError, DataTypeError, DataVersionError
from .graphic import to_sprite_mapping
from .typedefs import AnyItemDict, AnyItemPack, RawStatsMapping
from .utils import assert_key, assert_type, maybe_null, wrap_unsafe

from supermechs.item import Element, ItemData, Stat, StatsMapping, Tags, Tier, TransformStage, Type
from supermechs.item_pack import ItemPack, PackData
from supermechs.typeshed import ItemID, PackKey
from supermechs.utils import has_any_of

ErrorCallbackType: TypeAlias = abc.Callable[[Exception], None]

# fmt: off
_WU_STAT_TO_STAT = {
    "weight":      Stat.weight,
    "health":      Stat.hit_points,
    "eneCap":      Stat.energy_capacity,
    "eneReg":      Stat.regeneration,
    "heaCap":      Stat.heat_capacity,
    "heaCol":      Stat.cooling,
    "bulletsCap":  Stat.bullets_capacity,
    "rocketsCap":  Stat.rockets_capacity,
    "phyRes":      Stat.physical_resistance,
    "expRes":      Stat.explosive_resistance,
    "eleRes":      Stat.electric_resistance,
    "phyResDmg":   Stat.physical_resistance_damage,
    "eneDmg":      Stat.energy_damage,
    "eneCapDmg":   Stat.energy_capacity_damage,
    "eneRegDmg":   Stat.regeneration_damage,
    "eleResDmg":   Stat.electric_resistance_damage,
    "heaDmg":      Stat.heat_damage,
    "heaCapDmg":   Stat.heat_capacity_damage,
    "heaColDmg":   Stat.cooling_damage,
    "expResDmg":   Stat.explosive_resistance_damage,
    "walk":        Stat.walk,
    "jump":        Stat.jump,
    "push":        Stat.push,
    "pull":        Stat.pull,
    "recoil":      Stat.recoil,
    "advance":     Stat.advance,
    "retreat":     Stat.retreat,
    "uses":        Stat.uses,
    "backfire":    Stat.backfire,
    "heaCost":     Stat.heat_generation,
    "eneCost":     Stat.energy_cost,
    "bulletsCost": Stat.bullets_cost,
    "rocketsCost": Stat.rockets_cost,
}
_WU_STAT_LIST_TO_STATS = {
    "phyDmg": (Stat.physical_damage, Stat.physical_damage_addon),
    "eleDmg": (Stat.electric_damage, Stat.electric_damage_addon),
    "expDmg": (Stat.explosive_damage, Stat.explosive_damage_addon),
    "range":  (Stat.range, Stat.range_addon),
}
# fmt: on


def raises(exc: BaseException, /) -> NoReturn:
    """Simply raises passed exception."""
    raise exc from None


def to_tags(
    tags: abc.Iterable[str],
    start_stage: TransformStage,
) -> Tags:
    literal_tags = set[str]()

    for element in tags:
        if not isinstance(element, str):
            raise DataTypeError(type(element), str) from None

        literal_tags.add(element)

    if "legacy" in literal_tags:
        if start_stage.tier is Tier.MYTHICAL:
            literal_tags.add("premium")

    elif start_stage.tier >= Tier.LEGENDARY:
        literal_tags.add("premium")

    if has_any_of(start_stage.base_stats, Stat.advance, Stat.retreat):
        literal_tags.add("require_jump")

    try:
        return Tags.from_keywords(literal_tags)

    except TypeError as err:
        raise DataError from err


def _iter_stat_keys_and_types() -> abc.Iterator[tuple[str, type]]:
    for stat_key, data_type in typing.get_type_hints(RawStatsMapping).items():
        origin = typing.get_origin(data_type)

        if origin is int:  # noqa: SIM114
            yield stat_key, int

        elif origin is types.UnionType and {int, type(None)}.issuperset(typing.get_args(data_type)):
            yield stat_key, int

        elif origin is list:
            yield stat_key, list

        else:
            raise RuntimeError(data_type)


def to_stats_mapping(
    data: RawStatsMapping, /, *, on_error: ErrorCallbackType = raises
) -> StatsMapping:
    """Grabs only expected keys and checks value types. Transforms None values into NaNs."""

    final_stats: StatsMapping = {}
    # TODO: implement extrapolation of missing data

    for key, data_type in _iter_stat_keys_and_types():
        if key not in data:
            continue

        match data[key]:
            case int() | None as value if data_type is int:
                stat = _WU_STAT_TO_STAT[key]
                final_stats[stat] = maybe_null(value)

            case [int() | None, int() | None] as values if data_type is list:
                stats = _WU_STAT_LIST_TO_STATS[key]

                for stat, value in zip(stats, values):
                    final_stats[stat] = maybe_null(value)

            case unknown:  # pyright: ignore[reportUnknownVariableType]
                parent = DataTypeError(type(unknown), data_type)  # pyright: ignore[reportUnknownArgumentType]
                on_error(DataTypeAtKeyError(parent, key))

    return final_stats


def to_transform_stages(
    data: AnyItemDict, /, *, on_error: ErrorCallbackType = raises
) -> TransformStage:
    unsafe = wrap_unsafe(data)
    del data

    range_str = assert_key(str, unsafe, "transform_range")
    final_tier = Tier.of_initial(range_str[-1])

    if "stats" in unsafe:
        return TransformStage(
            tier=final_tier,
            base_stats=to_stats_mapping(unsafe["stats"], on_error=on_error),
            max_changing_stats={},
            level_progression=[],  # TODO: level_progression source
        )

    start_tier = Tier.of_initial(range_str[0])

    if start_tier > final_tier:
        msg = "Starting tier higher than final tier"
        raise DataError(msg)

    rolling_stats: StatsMapping = {}
    computed: list[tuple[Tier, StatsMapping, StatsMapping]] = []

    for tier in map(Tier.of_value, range(start_tier, final_tier + 1)):
        # this inferred as LiteralString doesn't play well further down
        key = str(tier.name.lower())
        max_key = "max_" + key

        try:
            base_tier_data = unsafe[key]

        except KeyError:
            on_error(DataKeyError(key))

        else:
            rolling_stats |= to_stats_mapping(base_tier_data, on_error=on_error)

        try:
            max_level_data = unsafe[max_key]

        except KeyError:
            if tier < Tier.DIVINE:
                on_error(DataKeyError(max_key))

            upper_stats = dict[Stat, Any]()

        else:
            upper_stats = to_stats_mapping(max_level_data, on_error=on_error)

        computed.append((tier, rolling_stats.copy(), upper_stats))

    current_stage = None

    for tier, base, addon in reversed(computed):
        current_stage = TransformStage(
            tier=tier,
            base_stats=base,
            max_changing_stats=addon,
            level_progression=[],  # TODO: level_progression source
            next=current_stage,
        )

    if current_stage is None:
        msg = "Data contains no item stats"
        raise DataError(msg)

    return current_stage


def to_item_data(
    data: AnyItemDict, pack_key: PackKey, *, on_error: ErrorCallbackType = raises
) -> ItemData:
    """Construct ItemData from its serialized form.

    Parameters
    ----------
    data: Mapping of serialized data.
    pack_key: The key of a pack this item comes from.
    custom: Whether the item comes from arbitrary or official source.
    """
    unsafe = wrap_unsafe(data)
    start_stage = to_transform_stages(data, on_error=on_error)
    del data
    tags = to_tags(unsafe.get("tags", ()), start_stage)
    item_data = ItemData(
        id=ItemID(assert_key(int, unsafe, "id")),
        pack_key=pack_key,
        name=assert_key(str, unsafe, "name"),
        type=Type[assert_key(str, unsafe, "type").upper()],
        element=Element[assert_key(str, unsafe, "element").upper()],
        tags=tags,
        start_stage=start_stage,
    )
    return item_data


def to_item_pack(data: AnyItemPack, /, *, on_error: ErrorCallbackType = raises) -> ItemPack:
    unsafe = wrap_unsafe(data)
    metadata = extract_metadata(data)
    key = metadata.key

    items: dict[ItemID, ItemData] = {}
    issues: list[DataError] = []

    for item_data in assert_key(abc.Sequence[Any], unsafe, "items", cast=False):
        try:
            item = to_item_data(item_data, key, on_error=on_error)

        except DataError as err:
            issues.append(err)

        else:
            items[item.id] = item

    if issues:
        msg = "Encountered issues while creating item pack"
        on_error(ExceptionGroup[DataError](msg, issues))

    sprites = to_sprite_mapping(data)  # FIXME
    return ItemPack(data=metadata, items=items, sprites=sprites)


def extract_metadata(pack: AnyItemPack, /) -> PackData:
    """Extracts key, name and description from item pack data."""

    unsafe = wrap_unsafe(pack)
    del pack
    version = assert_type(str, unsafe.get("version", "1"))

    if version == "1":
        key = "config"
        try:
            cfg = unsafe[key]

        except KeyError:
            raise DataKeyError(key) from None

    elif version not in ("2", "3"):
        raise DataVersionError(version, "3")

    else:
        cfg = unsafe

    params: dict[str, str] = {}
    pack_key = PackKey(assert_key(str, cfg, "key"))
    for extra in ("name", "description"):
        if extra in cfg:
            # not using assert_key as we don't treat those as mandatory
            params[extra] = assert_type(str, cfg[extra])

    return PackData(key=pack_key, **params)


def extract_key(pack: AnyItemPack, /) -> PackKey:
    """Extract the key of an item pack."""
    return extract_metadata(pack).key
