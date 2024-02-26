import types
import typing
from collections import abc

from .errors import Catch, DataPath, DataTypeError, DataValueError
from .typedefs import AnyItemDict, RawStatsMapping
from .utils import assert_key, maybe_null

from supermechs.abc.stats import StatsMapping
from supermechs.enums.stats import Stat, Tier
from supermechs.stats import StatsDict, TransformStage

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
    """Grabs only expected keys and checks value types. Transforms None values into NaNs."""

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
        final_tier = Tier.of_initial(range_str[-1])

    key = "stats"
    if key in data:
        with catch:
            stats = to_stats_mapping(data[key], at=(*at, key))

        catch.checkpoint()
        return TransformStage(
            tier=final_tier,
            base_stats=stats,
            max_changing_stats={},
            level_progression=[],  # TODO: level_progression source
        )
    del key

    catch.checkpoint()
    start_tier = Tier.of_initial(range_str[0])

    if start_tier > final_tier:
        msg = "Starting tier higher than final tier"
        raise DataValueError(msg, at=at)

    rolling_stats: StatsMapping = {}
    computed: list[tuple[Tier, StatsMapping, StatsMapping]] = []

    for tier in map(Tier.of_value, range(start_tier, final_tier + 1)):
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
            computed.append((tier, rolling_stats.copy(), upper_stats))

    catch.checkpoint()
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
