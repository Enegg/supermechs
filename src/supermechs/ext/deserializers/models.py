import typing as t

from .typedefs import AnyItemDict, AnyItemPack, RawStatsMapping
from .utils import NaN

from supermechs.enums import Element, Tier, Type
from supermechs.errors import InvalidKeyValue, MalformedData, UnknownDataVersion
from supermechs.item_pack import ItemPack
from supermechs.item_stats import Stat, StatsMapping, TransformStage, ValueRange
from supermechs.models.item import ItemData, Tags, TransformRange, transform_range
from supermechs.utils import assert_type, has_any_of

ErrorCallbackType = t.Callable[[Exception], None]
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
    "phyDmg":      Stat.physical_damage,
    "phyResDmg":   Stat.physical_resistance_damage,
    "eleDmg":      Stat.electric_damage,
    "eneDmg":      Stat.energy_damage,
    "eneCapDmg":   Stat.energy_capacity_damage,
    "eneRegDmg":   Stat.regeneration_damage,
    "eleResDmg":   Stat.electric_resistance_damage,
    "expDmg":      Stat.explosive_damage,
    "heaDmg":      Stat.heat_damage,
    "heaCapDmg":   Stat.heat_capacity_damage,
    "heaColDmg":   Stat.cooling_damage,
    "expResDmg":   Stat.explosive_resistance_damage,
    "walk":        Stat.walk,
    "jump":        Stat.jump,
    "range":       Stat.range,
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
# fmt: on


def raises(exc: BaseException, /) -> t.NoReturn:
    """Simply raises passed exception."""
    raise exc


def to_tags(
    tags: t.Iterable[str],
    transform_range: TransformRange,
    stats: RawStatsMapping,
    custom: bool,
    /,
) -> Tags:
    literal_tags = set(tags)

    if "legacy" in literal_tags:
        if transform_range[0] is Tier.MYTHICAL:
            literal_tags.add("premium")

    elif transform_range[0] >= Tier.LEGENDARY:
        literal_tags.add("premium")

    if has_any_of(stats, "advance", "retreat"):
        literal_tags.add("require_jump")

    if custom:
        literal_tags.add("custom")

    try:
        return Tags.from_keywords(literal_tags)

    except TypeError as err:
        raise MalformedData(data=literal_tags) from err


def to_transform_range(string: str, /) -> TransformRange:
    """Construct a TransformRange object from a string like "C-E" or "M"."""
    up, _, down = assert_type(str, string).strip().partition("-")
    try:
        return transform_range(Tier.of_initial(up), Tier.of_initial(down) if down else None)

    except ValueError as err:
        raise MalformedData(data=string) from err


def _get_first_stats_mapping(data: AnyItemDict, /) -> RawStatsMapping:
    if "stats" in data:
        return data["stats"]

    for tier in Tier:
        key = t.cast(str, tier.name.lower())
        if key in data:
            return data[key]

    msg = "Data contains no item stats"
    raise MalformedData(msg)


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
    transform_range = to_transform_range(data["transform_range"])
    tags = to_tags(data.get("tags", ()), transform_range, _get_first_stats_mapping(data), custom)
    stages = to_transform_stages(data, on_error=on_error)
    item_data = ItemData(
        id=assert_type(int, data["id"]),
        pack_key=assert_type(str, pack_key),
        name=assert_type(str, data["name"]),
        type=Type[data["type"].upper()],
        element=Element[data["element"].upper()],
        transform_range=transform_range,
        tags=tags,
        start_stage=stages,
    )
    return item_data


def _iter_stat_keys_and_types() -> t.Iterator[tuple[str, type]]:
    import types

    for stat_key, data_type in t.get_type_hints(RawStatsMapping).items():
        origin = t.get_origin(data_type)

        if origin is int:  # noqa: SIM114
            yield stat_key, int

        elif origin in (types.UnionType, t.Union) and set(t.get_args(data_type)).issubset(
            (int, type(None))
        ):
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

        stat = _WU_STAT_TO_STAT[key]

        match data[key]:
            case int() | None as value if data_type is int:
                final_stats[stat] = NaN if value is None else value

            case [int() | None as x, int() | None as y] if data_type is list:
                final_stats[stat] = ValueRange(
                    NaN if x is None else x,
                    NaN if y is None else y,
                )

            case unknown:
                on_error(InvalidKeyValue(unknown, data_type, key))

    return final_stats


def to_transform_stages(
    data: AnyItemDict, /, *, on_error: ErrorCallbackType = raises
) -> TransformStage:
    if "stats" in data:
        tier = Tier.of_initial(data["transform_range"][-1])
        base_stats = to_stats_mapping(data["stats"], on_error=on_error)
        return TransformStage(tier=tier, base_stats=base_stats, max_level_stats={})

    hit = False
    rolling_stats: StatsMapping = {}

    computed: list[tuple[Tier, StatsMapping, StatsMapping]] = []

    for tier in Tier:
        key = t.cast(str, tier.name.lower())

        if key not in data:
            # if we already populated the dict with stats,
            # missing key means we should break as there will be no further stats
            if hit:
                break

            continue

        hit = True
        rolling_stats |= to_stats_mapping(data[key], on_error=on_error)

        try:
            max_level_data = data["max_" + key]

        except KeyError:
            if tier is not Tier.DIVINE:
                on_error(KeyError(f"max_{key} key not found for item {data['name']}"))

            upper_stats = StatsMapping()

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
        raise MalformedData(msg)

    return current_stage


def to_item_pack(
    data: AnyItemPack, /, *, custom: bool = False, on_error: ErrorCallbackType = raises
) -> ItemPack:
    if "version" not in data or data["version"] == "1":
        metadata = data["config"]

    elif data["version"] in ("2", "3"):
        metadata = data

    else:
        raise UnknownDataVersion("pack", data["version"], 3)  # noqa: EM101

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

    # what TODO with the issues?

    return ItemPack(
        key=key,
        items=items,
        name=assert_type(str, metadata.get("name", "<no name>")),
        description=assert_type(str, metadata.get("description", "<no description>")),
        custom=custom,
    )


def extract_key(pack: AnyItemPack, /) -> str:
    """Extract the key of an item pack.

    Raises
    ------
    TypeError on unknown version.
    """
    if "version" not in pack or pack["version"] == "1":
        key = pack["config"]["key"]

    elif pack["version"] in ("2", "3"):
        key = pack["key"]

    else:
        raise UnknownDataVersion("pack", pack["version"], 3)  # noqa: EM101

    return assert_type(str, key)
