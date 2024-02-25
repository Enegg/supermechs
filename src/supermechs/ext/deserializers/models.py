import types
import typing
from collections import abc
from contextlib import contextmanager
from typing import Any, NoReturn, TypeAlias

from exceptiongroup import ExceptionGroup
from typing_extensions import TypeVar

from .errors import (
    DataError,
    DataKeyError,
    DataTypeError,
    DataValueError,
    DataVersionError,
)
from .typedefs import AnyItemDict, AnyItemPack, RawStatsMapping
from .utils import assert_key, assert_type, maybe_null, wrap_unsafe

from supermechs.abc.item import ItemID
from supermechs.abc.item_pack import PackKey
from supermechs.abc.stats import StatsMapping
from supermechs.enums.item import Element, Type
from supermechs.enums.stats import Stat, Tier
from supermechs.item import ItemData, Tags
from supermechs.item_pack import ItemPack, PackData
from supermechs.stats import StatsDict, TransformStage
from supermechs.utils import has_any_of

ExcT = TypeVar("ExcT", bound=Exception, infer_variance=True)
MaybeGroup: TypeAlias = ExcT | ExceptionGroup[ExcT]

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
}  # fmt: skip
_WU_STAT_LIST_TO_STATS = {
    "phyDmg": (Stat.physical_damage, Stat.physical_damage_addon),
    "eleDmg": (Stat.electric_damage, Stat.electric_damage_addon),
    "expDmg": (Stat.explosive_damage, Stat.explosive_damage_addon),
    "range":  (Stat.range, Stat.range_addon),
}  # fmt: skip


@contextmanager
def catch(callback: abc.Callable[[Exception], None], /) -> abc.Iterator[None]:
    exc: MaybeGroup[DataError]
    try:
        yield

    except (DataError, ExceptionGroup) as exc:
        callback(exc)


def raises(exc: BaseException, /) -> NoReturn:
    """Simply raises passed exception."""
    raise exc from None


def to_tags(
    tags: abc.Iterable[str],
    start_stage: TransformStage,
    *,
    collect_errors: bool = True,
    at: tuple[Any, ...] = (),
) -> Tags:
    literal_tags = set[str]()
    valid = Tags.__annotations__.keys()

    issues: list[Exception] = []
    on_error = issues.append if collect_errors else raises

    for element in tags:
        if not isinstance(element, str):
            on_error(DataTypeError(type(element), str, at=at))

        elif element not in valid:
            msg = f"{element!r} is not a valid tag"
            on_error(DataValueError(msg, at=at))

        else:
            literal_tags.add(element)

    if "legacy" in literal_tags:
        if start_stage.tier is Tier.MYTHICAL:
            literal_tags.add("premium")

    elif start_stage.tier >= Tier.LEGENDARY:
        literal_tags.add("premium")

    if has_any_of(start_stage.base_stats, Stat.advance, Stat.retreat):
        literal_tags.add("require_jump")

    if issues:
        msg = "Problems while parsing item tags:"
        raise ExceptionGroup[Exception](msg, issues) from None

    return Tags.from_keywords(literal_tags)


def _iter_stat_keys_and_types() -> abc.Iterator[tuple[str, type]]:
    superset = {int, type(None)}
    for stat_key, data_type in typing.get_type_hints(RawStatsMapping).items():
        origin = typing.get_origin(data_type)

        if origin is int:  # noqa: SIM114
            yield stat_key, int

        elif origin is types.UnionType and superset.issuperset(typing.get_args(data_type)):
            yield stat_key, int

        elif origin is list:
            yield stat_key, list

        else:
            msg = f"Unexpected type for key {stat_key!r}: {data_type}"
            raise RuntimeError(msg)


def to_stats_mapping(
    data: RawStatsMapping, /, *, collect_errors: bool = True, at: tuple[Any, ...] = ()
) -> StatsMapping:
    """Grabs only expected keys and checks value types. Transforms None values into NaNs."""

    final_stats: StatsMapping = {}
    issues: list[Exception] = []
    on_error = issues.append if collect_errors else raises
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

                for stat, value in zip(stats, values, strict=True):
                    final_stats[stat] = maybe_null(value)

            case unknown:
                unknown: Any
                on_error(DataTypeError(type(unknown), data_type, at=(*at, key)))

    if issues:
        msg = "Problems while parsing stat mapping:"
        raise ExceptionGroup[Exception](msg, issues) from None

    return final_stats


def to_transform_stages(  # noqa: PLR0912
    data: AnyItemDict, /, *, collect_errors: bool = True, at: tuple[Any, ...] = ()
) -> TransformStage:
    unsafe = wrap_unsafe(data)
    del data

    range_str = assert_key(str, unsafe, "transform_range", at=at)
    final_tier = Tier.of_initial(range_str[-1])

    key = "stats"
    if key in unsafe:
        return TransformStage(
            tier=final_tier,
            base_stats=to_stats_mapping(unsafe[key], at=(*at, key), collect_errors=collect_errors),
            max_changing_stats={},
            level_progression=[],  # TODO: level_progression source
        )
    del key

    start_tier = Tier.of_initial(range_str[0])

    if start_tier > final_tier:
        msg = "Starting tier higher than final tier"
        raise DataValueError(msg, at=at)

    rolling_stats: StatsMapping = {}
    computed: list[tuple[Tier, StatsMapping, StatsMapping]] = []

    issues: list[Exception] = []
    on_error = issues.append if collect_errors else raises

    for tier in map(Tier.of_value, range(start_tier, final_tier + 1)):
        # this inferred as LiteralString doesn't play well further down
        key = str(tier.name.lower())
        max_key = "max_" + key

        try:
            base_tier_data = unsafe[key]

        except KeyError:
            on_error(DataKeyError(key, at=at))

        else:
            with catch(on_error):
                rolling_stats |= to_stats_mapping(
                    base_tier_data, collect_errors=collect_errors, at=(*at, key)
                )

        try:
            max_level_data = unsafe[max_key]

        except KeyError:
            if tier is not final_tier:
                on_error(DataKeyError(max_key, at=at))
                continue

            upper_stats = StatsDict()

        else:
            upper_stats = StatsDict()

            with catch(on_error):
                upper_stats = to_stats_mapping(
                    max_level_data, collect_errors=collect_errors, at=(*at, max_key)
                )

        computed.append((tier, rolling_stats.copy(), upper_stats))

    if issues:
        msg = "Problems while creating transformation stages:"
        raise ExceptionGroup[Exception](msg, issues) from None

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
        raise DataValueError(msg, at=at)

    return current_stage


def to_item_data(
    data: AnyItemDict, pack_key: PackKey, *, at: tuple[Any, ...] = (), collect_errors: bool = True
) -> ItemData:
    """Construct ItemData from its serialized form.

    Parameters
    ----------
    data: Mapping of serialized data.
    pack_key: The key of a pack this item comes from.
    custom: Whether the item comes from arbitrary or official source.
    """
    unsafe = wrap_unsafe(data)
    start_stage = to_transform_stages(data, collect_errors=collect_errors, at=at)
    del data
    tags = to_tags(unsafe.get("tags", ()), start_stage, collect_errors=collect_errors, at=at)
    item_data = ItemData(
        id=ItemID(assert_key(int, unsafe, "id", at=at)),
        pack_key=pack_key,
        name=assert_key(str, unsafe, "name", at=at),
        type=Type[assert_key(str, unsafe, "type", at=at).upper()],
        element=Element[assert_key(str, unsafe, "element", at=at).upper()],
        tags=tags,
        start_stage=start_stage,
    )
    return item_data


def to_item_pack(data: AnyItemPack, /, *, collect_errors: bool = True) -> ItemPack:
    unsafe = wrap_unsafe(data)
    metadata = extract_metadata(data)
    items: dict[ItemID, ItemData] = {}
    key = "items"

    issues: list[Exception] = []
    on_error = issues.append if collect_errors else raises

    for i, item_data in enumerate(assert_key(abc.Sequence[Any], unsafe, key, cast=False)):
        try:
            item = to_item_data(item_data, metadata.key, collect_errors=collect_errors, at=(key, i))

        except Exception as err:
            on_error(err)

        else:
            items[item.id] = item

    if issues:
        msg = "Problems while creating item pack:"
        raise ExceptionGroup[Exception](msg, issues) from None

    return ItemPack(data=metadata, items=items, sprites={})


def extract_metadata(pack: AnyItemPack, /) -> PackData:
    """Extracts key, name and description from item pack data."""

    unsafe = wrap_unsafe(pack)
    del pack
    version = assert_type(str, unsafe.get("version", "1"))

    if version == "1":
        cfg = assert_key(dict[str, Any], unsafe, "config")

    elif version not in ("2", "3"):
        raise DataVersionError(version, "3")

    else:
        cfg = unsafe

    params: dict[str, str] = {}
    pack_key = PackKey(assert_key(str, cfg, "key"))
    for extra in ("name", "description"):
        if extra in cfg:
            # not using assert_key as we don't treat those as mandatory
            params[extra] = assert_type(str, cfg[extra], at=(extra,))

    return PackData(key=pack_key, **params)


def extract_key(pack: AnyItemPack, /) -> PackKey:
    """Extract the key of an item pack."""
    return extract_metadata(pack).key
