import types
import typing
from collections import abc

from .exceptions import Catch, DataPath, DataTypeError, DataValueError
from .stat_providers import InterpolatedStats, StaticStats
from .typedefs import AnyItemDict, RawStatsMapping
from .utils import assert_key, maybe_null

from supermechs.abc.stats import StatsMapping, StatsProvider
from supermechs.enums.stats import StatEnum, TierEnum
from supermechs.stats import StatsDict, TransformStage

_WU_STAT_TO_STAT = {
    "weight":      StatEnum.weight,
    "health":      StatEnum.hit_points,
    "eneCap":      StatEnum.energy_capacity,
    "eneReg":      StatEnum.regeneration,
    "heaCap":      StatEnum.heat_capacity,
    "heaCol":      StatEnum.cooling,
    "bulletsCap":  StatEnum.bullets_capacity,
    "rocketsCap":  StatEnum.rockets_capacity,
    "phyRes":      StatEnum.physical_resistance,
    "expRes":      StatEnum.explosive_resistance,
    "eleRes":      StatEnum.electric_resistance,
    "phyResDmg":   StatEnum.physical_resistance_damage,
    "eneDmg":      StatEnum.energy_damage,
    "eneCapDmg":   StatEnum.energy_capacity_damage,
    "eneRegDmg":   StatEnum.regeneration_damage,
    "eleResDmg":   StatEnum.electric_resistance_damage,
    "heaDmg":      StatEnum.heat_damage,
    "heaCapDmg":   StatEnum.heat_capacity_damage,
    "heaColDmg":   StatEnum.cooling_damage,
    "expResDmg":   StatEnum.explosive_resistance_damage,
    "walk":        StatEnum.walk,
    "jump":        StatEnum.jump,
    "push":        StatEnum.push,
    "pull":        StatEnum.pull,
    "recoil":      StatEnum.recoil,
    "advance":     StatEnum.advance,
    "retreat":     StatEnum.retreat,
    "uses":        StatEnum.uses,
    "backfire":    StatEnum.backfire,
    "heaCost":     StatEnum.heat_generation,
    "eneCost":     StatEnum.energy_cost,
    "bulletsCost": StatEnum.bullets_cost,
    "rocketsCost": StatEnum.rockets_cost,
}  # fmt: skip
_WU_STAT_LIST_TO_STATS = {
    "phyDmg": (StatEnum.physical_damage, StatEnum.physical_damage_addon),
    "eleDmg": (StatEnum.electric_damage, StatEnum.electric_damage_addon),
    "expDmg": (StatEnum.explosive_damage, StatEnum.explosive_damage_addon),
    "range":  (StatEnum.range, StatEnum.range_addon),
}  # fmt: skip
_STAT_KEYS_AND_TYPES: abc.Mapping[str, type] = typing.get_type_hints(RawStatsMapping)


def _iter_stat_keys_and_types() -> abc.Iterator[tuple[str, type]]:
    superset = {int, type(None)}
    for stat_key, data_type in _STAT_KEYS_AND_TYPES.items():
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


def to_stats_mapping(data: RawStatsMapping, /, *, at: DataPath = ()) -> StatsMapping:
    """Grab only expected keys and check value types. Transform None values into NaNs."""
    catch = Catch()
    final_stats: StatsMapping = {}
    # TODO: extrapolation of missing data

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
                unknown: typing.Any
                catch.add(DataTypeError(type(unknown), data_type, at=(*at, key)))

    unknown_keys = data.keys() - _STAT_KEYS_AND_TYPES.keys()
    if unknown_keys:
        msg = f"Unknown extra keys: {', '.join(map(repr, unknown_keys))}"
        catch.add(DataValueError(msg, at=at))

    catch.checkpoint("Problems while parsing stat mapping:")
    return final_stats


def to_transform_stages(data: AnyItemDict, /, *, at: DataPath = ()) -> TransformStage:
    catch = Catch()

    with catch:
        range_str = assert_key(str, data, "transform_range", at=at)
        final_tier = TierEnum.of_initial(range_str[-1])

    key = "stats"
    if key in data:
        with catch:
            base_stats = to_stats_mapping(data[key], at=(*at, key))

        catch.checkpoint()
        return TransformStage(
            tier=final_tier,
            stats=StaticStats(base_stats),
            level_progression=[],  # TODO: level_progression source
        )
    del key

    catch.checkpoint()
    start_tier = TierEnum.of_initial(range_str[0])

    if start_tier > final_tier:
        msg = "Starting tier higher than final tier"
        raise DataValueError(msg, at=at)

    rolling_stats: StatsMapping = {}
    computed: list[tuple[TierEnum, StatsProvider]] = []

    for tier in map(TierEnum.of_value, range(start_tier, final_tier + 1)):
        key = tier.name.lower()
        max_key = "max_" + key

        with catch:
            base_tier_data = assert_key(RawStatsMapping, data, key, at=at)
            rolling_stats |= to_stats_mapping(base_tier_data, at=(*at, key))

        if tier is final_tier and max_key not in data:
            upper_stats = StatsDict()

        else:
            with catch:
                max_level_data = assert_key(RawStatsMapping, data, max_key, at=at)
                upper_stats = to_stats_mapping(max_level_data, at=(*at, max_key))

        if not catch.issues:
            if upper_stats:
                stats = InterpolatedStats(rolling_stats.copy(), upper_stats, 0)

            else:
                stats = StaticStats(rolling_stats.copy())

            computed.append((tier, stats))

    catch.checkpoint()
    current_stage = None

    for tier, stats in reversed(computed):
        current_stage = TransformStage(
            tier=tier,
            stats=stats,
            level_progression=[],  # TODO: level_progression source
            next=current_stage,
        )

    if current_stage is None:
        msg = "Data contains no item stats"
        raise DataValueError(msg, at=at)

    return current_stage
