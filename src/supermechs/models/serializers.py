import typing as t

from ..enums import Element, Tier, Type
from ..errors import InvalidKeyValue, MalformedData, UnknownDataVersion
from ..item_pack import ItemPack
from ..item_stats import AnyStatsMapping, TransformStage, ValueRange
from ..typedefs import AnyItemDict, AnyItemPack, RawMechStatsMapping, RawStatsMapping
from ..utils import NaN, assert_type, has_any_of_keys
from .item_data import ItemData, Tags, TransformRange, transform_range

ErrorCallbackType = t.Callable[[Exception], None]


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

    if has_any_of_keys(stats, "advance", "retreat"):
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
        return transform_range(Tier.by_initial(up), Tier.by_initial(down) if down else None)

    except ValueError as err:
        raise MalformedData(data=string) from err


def _get_first_stats_mapping(data: AnyItemDict, /) -> RawStatsMapping:
    if "stats" in data:
        return data["stats"]

    for tier in Tier:
        key = t.cast(str, tier.name.lower())
        if key in data:
            return data[key]

    raise MalformedData("Data contains no item stats")


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
    import itertools
    import types

    for stat_key, data_type in itertools.chain(
        t.get_type_hints(RawMechStatsMapping).items(), t.get_type_hints(RawStatsMapping).items()
    ):
        origin, args = t.get_origin(data_type), t.get_args(data_type)

        if origin is int:  # noqa: SIM114
            yield stat_key, int

        elif origin in (types.UnionType, t.Union) and set(args).issubset((int, type(None))):
            yield stat_key, int

        elif origin is list:
            yield stat_key, list

        else:
            raise RuntimeError(f"Unexpected type for key {stat_key!r}: {data_type!r} ({origin})")


def to_stats_mapping(
    data: RawStatsMapping, /, *, on_error: ErrorCallbackType = raises
) -> AnyStatsMapping:
    """Grabs only expected keys and checks value types. Transforms None values into NaNs."""

    final_stats: AnyStatsMapping = {}
    # TODO: implement extrapolation of missing data

    for key, data_type in _iter_stat_keys_and_types():
        if key not in data:
            continue

        match data[key]:
            case int() | None as value if data_type is int:
                final_stats[key] = NaN if value is None else value

            case [int() | None as x, int() | None as y] if data_type is list:
                final_stats[key] = ValueRange(
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
        tier = Tier.by_initial(data["transform_range"][-1])
        base_stats = to_stats_mapping(data["stats"], on_error=on_error)
        return TransformStage(tier=tier, base_stats=base_stats, max_level_stats={})

    hit = False
    rolling_stats: AnyStatsMapping = {}

    computed: list[tuple[Tier, AnyStatsMapping, AnyStatsMapping]] = []

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

            upper_stats = AnyStatsMapping()

        else:
            upper_stats = to_stats_mapping(max_level_data, on_error=on_error)

        computed.append((tier, rolling_stats.copy(), upper_stats))

    current_stage = None

    for tier, base, addon in reversed(computed):
        current_stage = TransformStage(
            tier=tier, base_stats=base, max_level_stats=addon, next=current_stage
        )

    if current_stage is None:
        raise MalformedData("Data contains no item stats")

    return current_stage


def to_item_pack(
    data: AnyItemPack, /, *, custom: bool = False, on_error: ErrorCallbackType = raises
) -> ItemPack:
    if "version" not in data or data["version"] == "1":
        metadata = data["config"]

    elif data["version"] in ("2", "3"):
        metadata = data

    else:
        raise UnknownDataVersion("pack", data["version"], 3)

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

    pack = ItemPack(
        key=key,
        items=items,
        name=assert_type(str, metadata.get("name", "<no name>")),
        description=assert_type(str, metadata.get("description", "<no description>")),
        custom=custom,
    )
    return pack
