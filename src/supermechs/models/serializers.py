import typing as t

from ..enums import Element, Tier, Type
from ..errors import MalformedData
from ..item_stats import AnyStatsMapping, TransformStage, ValueRange
from ..typedefs import AnyItemDict, RawMechStatsMapping, RawStatsMapping
from ..utils import NaN, has_any_of_keys
from .item_data import ItemData, Tags, TransformRange, transform_range


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
    up, _, down = string.strip().partition("-")
    try:
        return transform_range(Tier.by_initial(up), Tier.by_initial(down) if down else None)

    except ValueError as err:
        raise MalformedData(data=string) from err


def _get_first_stats_mapping(data: AnyItemDict) -> RawStatsMapping:
    if "stats" in data:
        return data["stats"]

    for tier in Tier:
        key = t.cast(str, tier.name.lower())
        if key in data:
            return data[key]

    raise MalformedData("Data contains no item stats")


def to_item_data(data: AnyItemDict, pack_key: str, custom: bool, *, strict: bool = False) -> t.Any:
    """Construct ItemData from its serialized form.

    Parameters
    ----------
    data: Mapping of serialized data.
    pack_key: The key of a pack this item comes from.
    custom: Whether the item comes from arbitrary or official source.
    """
    transform_range = to_transform_range(data["transform_range"])
    tags = to_tags(data.get("tags", ()), transform_range, _get_first_stats_mapping(data), custom)
    stages = to_transform_stages(data, strict=strict)
    item_data = ItemData(
        id=int(data["id"]),
        pack_key=str(pack_key),
        name=data["name"],
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

        if origin is int:
            yield stat_key, int

        elif origin in (types.UnionType, t.Union) and set(args).issubset((int, type(None))):
            yield stat_key, int

        elif origin is list:
            yield stat_key, list

        else:
            raise RuntimeError(f"Unexpected type for key {stat_key!r}: {data_type!r} ({origin})")


def to_stats_mapping(data: RawStatsMapping, *, strict: bool = False) -> AnyStatsMapping:
    """Grabs only expected keys and checks value types. Transforms None values into NaNs."""

    final_stats: AnyStatsMapping = {}
    issues: list[Exception] = []

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
                msg = f"Expected {data_type.__name__} on key {key!r}, got {unknown!r:.20}"
                if strict:
                    issues.append(TypeError(msg))

    if issues:
        raise issues[0]  # exception groups when

    return final_stats


def to_transform_stages(data: AnyItemDict, /, *, strict: bool = False) -> TransformStage:
    if "stats" in data:
        tier = Tier.by_initial(data["transform_range"][-1])
        base_stats = to_stats_mapping(data["stats"], strict=strict)
        return TransformStage(
            tier=tier,
            base_stats=base_stats,
            max_level_stats={}
        )

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
        rolling_stats |= to_stats_mapping(data[key], strict=strict)

        try:
            max_level_data = data["max_" + key]

        except KeyError:
            if tier is not Tier.DIVINE:
                if strict:
                    raise KeyError(f"max_{key} key not found for item {data['name']}")

            upper_stats = AnyStatsMapping()

        else:
            upper_stats = to_stats_mapping(max_level_data, strict=strict)

        computed.append((tier, rolling_stats.copy(), upper_stats))

    current_stage = None

    for tier, base, addon in reversed(computed):
        current_stage = TransformStage(
            tier=tier,
            base_stats=base,
            max_level_stats=addon,
            next=current_stage
        )

    if current_stage is None:
        raise KeyError("Data contains no item stats")

    return current_stage
