import typing as t

from .errors import DataError, DataKeyError, DataTypeAtKeyError, DataVersionError
from .graphic import to_sprite_mapping
from .typedefs import AnyItemDict, AnyItemPack, PackMetadata, RawStatsMapping
from .utils import none_to_nan

from supermechs.item import Element, ItemData, Tags, Tier, Type
from supermechs.item.stats import Stat, StatsMapping, TransformStage
from supermechs.item_pack import ItemPack
from supermechs.utils import has_any_of

from supermechs.ext.deserializers.utils import assert_type

if t.TYPE_CHECKING:
    from PIL.Image import Image

ErrorCallbackType: t.TypeAlias = t.Callable[[Exception], None]

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


def raises(exc: BaseException, /) -> t.NoReturn:
    """Simply raises passed exception."""
    raise exc from None


def to_tags(
    tags: t.Iterable[str],
    start_stage: TransformStage,
    custom: bool,
) -> Tags:
    literal_tags = set(tags)

    if "legacy" in literal_tags:
        if start_stage.tier is Tier.MYTHICAL:
            literal_tags.add("premium")

    elif start_stage.tier >= Tier.LEGENDARY:
        literal_tags.add("premium")

    if has_any_of(start_stage.base_stats, Stat.advance, Stat.retreat):
        literal_tags.add("require_jump")

    if custom:
        literal_tags.add("custom")

    try:
        return Tags.from_keywords(literal_tags)

    except TypeError as err:
        raise DataError from err


def _iter_stat_keys_and_types() -> t.Iterator[tuple[str, type]]:
    import types

    for stat_key, data_type in t.get_type_hints(RawStatsMapping).items():
        origin = t.get_origin(data_type)

        if origin is int:  # noqa: SIM114
            yield stat_key, int

        elif origin is types.UnionType and set(t.get_args(data_type)).issubset((int, type(None))):
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
                final_stats[stat] = none_to_nan(value)

            case [int() | None, int() | None] as values if data_type is list:
                stats = _WU_STAT_LIST_TO_STATS[key]

                for stat, value in zip(stats, values):
                    final_stats[stat] = none_to_nan(value)

            case unknown:  # pyright: ignore[reportUnknownVariableType]
                on_error(DataTypeAtKeyError(unknown, data_type, key))  # pyright: ignore[reportUnknownArgumentType]

    return final_stats


def to_transform_stages(
    data: AnyItemDict, /, *, on_error: ErrorCallbackType = raises
) -> TransformStage:
    range_str = assert_type(str, data["transform_range"])
    final_tier = Tier.of_initial(range_str[-1])

    if "stats" in data:
        base_stats = to_stats_mapping(data["stats"], on_error=on_error)
        return TransformStage(tier=final_tier, base_stats=base_stats, max_level_stats={})

    start_tier = Tier.of_initial(range_str[0])

    if start_tier > final_tier:
        msg = "Starting tier higher than final tier"
        raise DataError(msg)

    rolling_stats: StatsMapping = {}
    computed: list[tuple[Tier, StatsMapping, StatsMapping]] = []

    for tier in map(Tier.of_value, range(start_tier, final_tier + 1)):
        key = t.cast(str, tier.name.lower())

        try:
            base_tier_data = t.cast(RawStatsMapping, data[key])

        except KeyError as err:
            on_error(DataKeyError(err))

        else:
            rolling_stats |= to_stats_mapping(base_tier_data, on_error=on_error)

        try:
            max_level_data = t.cast(RawStatsMapping, data["max_" + key])

        except KeyError as err:
            if tier < Tier.DIVINE:
                on_error(DataKeyError(err))

            upper_stats = dict[Stat, t.Any]()

        else:
            upper_stats = to_stats_mapping(max_level_data, on_error=on_error)

        computed.append((tier, rolling_stats.copy(), upper_stats))

    current_stage = None

    for tier, base, addon in reversed(computed):
        current_stage = TransformStage(
            tier=tier, base_stats=base, max_level_stats=addon, next=current_stage
        )

    if current_stage is None:
        msg = "Data contains no item stats"
        raise DataError(msg)

    return current_stage


def to_item_data(
    data: AnyItemDict, pack_key: str, custom: bool, *, on_error: ErrorCallbackType = raises
) -> ItemData:
    """Construct ItemData from its serialized form.

    Parameters
    ----------
    data: Mapping of serialized data.
    pack_key: The key of a pack this item comes from.
    custom: Whether the item comes from arbitrary or official source.
    """
    start_stage = to_transform_stages(data, on_error=on_error)
    tags = to_tags(
        data.get("tags", ()),
        start_stage,
        custom,
    )
    item_data = ItemData(
        id=assert_type(int, data["id"]),
        pack_key=pack_key,
        name=assert_type(str, data["name"]),
        type=Type[assert_type(str, data["type"]).upper()],
        element=Element[assert_type(str, data["element"]).upper()],
        tags=tags,
        start_stage=start_stage,
    )
    return item_data


def to_item_pack(
    data: AnyItemPack, /, *, custom: bool = False, on_error: ErrorCallbackType = raises
) -> ItemPack["Image"]:
    metadata = extract_metadata(data)
    key = assert_type(str, metadata["key"])

    items: dict[int, ItemData] = {}
    issues: list[Exception] = []

    for item_data in data["items"]:
        try:
            item = to_item_data(item_data, key, custom, on_error=on_error)

        except Exception as err:
            issues.append(err)

        else:
            items[item.id] = item

    sprites = to_sprite_mapping(data)

    # what TODO with the issues?

    return ItemPack(
        key=key,
        name=assert_type(str, metadata.get("name", "<no name>")),
        description=assert_type(str, metadata.get("description", "<no description>")),
        items=items,
        sprites=sprites,
        custom=custom,
    )


def extract_metadata(pack: AnyItemPack, /) -> PackMetadata:
    if "version" not in pack or pack["version"] == "1":
        try:
            return pack["config"]

        except KeyError as err:
            raise DataKeyError(err) from None

    if pack["version"] not in ("2", "3"):
        raise DataVersionError(pack["version"], "3")

    return pack


def extract_key(pack: AnyItemPack, /) -> str:
    """Extract the key of an item pack."""
    metadata = extract_metadata(pack)
    return assert_type(str, metadata["key"])
