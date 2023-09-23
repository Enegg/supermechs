import typing as t

from .context import ComparisonContext
from .converter import StatsGroup
from .helpers import mean_and_deviation as mean_and_deviation

from supermechs.api import STATS, Stat, ValueRange
from supermechs.typeshed import twotuple

damage_keys: t.Final = frozenset(("phyDmg", "expDmg", "eleDmg", "anyDmg"))
custom_stats: t.Mapping[str, Stat] = {
    "spread": Stat("spread", beneficial=False),
    "anyDmg": Stat("anyDmg", buff="+%"),
    "totalDmg": Stat("totalDmg", buff="+%"),
}
STAT_KEY_ORDER: t.Sequence[str] = tuple(STATS)


def sum_damage_entries(
    entries: t.Iterable[t.Sequence[ValueRange | None]], size: int
) -> t.Sequence[ValueRange | None]:
    entry_values: list[ValueRange | None] = [None] * size

    for entry in entries:
        for i, value in enumerate(entry):
            if value is None:
                continue
            # somehow, entry_values[i] is None doesn't narrow type on following item access
            # so need to reassign the value manually
            current_value = entry_values[i]

            if current_value is None:
                current_value = value

            else:
                current_value += value

            entry_values[i] = current_value

    return entry_values


def merge_entries(
    entries: t.Iterable[t.Sequence[ValueRange | None]], size: int
) -> t.Sequence[ValueRange | None]:
    entry_values: list[ValueRange | None] = [None] * size

    for entry in entries:
        for i, value in enumerate(entry):
            if entry_values[i] is None:
                entry_values[i] = value

    return entry_values


def coerce_damage_entries(group: StatsGroup, /) -> None:
    present_damage_keys = damage_keys & group.entries.keys()

    if len(present_damage_keys) <= 1:
        # don't coerce for only one damage type
        return

    # don't add one since the entry will be gone at the time of insert
    index = min(map(group.key_order.index, present_damage_keys))
    entry = merge_entries(map(group.remove_entry, present_damage_keys), group.size)
    group.insert_entry("anyDmg", index, entry)


def calculate_spread(value: t.Any, /) -> float:
    avg, dev = mean_and_deviation(*value)
    return dev / avg


def insert_damage_spread_entry(group: StatsGroup, /) -> None:
    present_damage_keys = damage_keys & group.entries.keys()

    if not present_damage_keys:
        return

    key = next(iter(present_damage_keys))
    total_damage = group.entries[key]

    # insert after the last damage entry
    index = max(map(group.key_order.index, present_damage_keys)) + 1

    group.insert_entry(
        "spread",
        index,
        tuple(None if value is None else calculate_spread(value) for value in total_damage),
    )


def run_conversions(group: StatsGroup, ctx: ComparisonContext) -> None:
    coerce_damage_entries(group)

    if ctx.show_damage_spread:
        insert_damage_spread_entry(group)


@t.overload
def compare_numbers(x: int, y: int, lower_is_better: bool = False) -> twotuple[int]:
    ...


@t.overload
def compare_numbers(x: float, y: float, lower_is_better: bool = False) -> twotuple[float]:
    ...


def compare_numbers(x: float, y: float, lower_is_better: bool = False) -> twotuple[float]:
    return (x - y, 0) if lower_is_better ^ (x > y) else (0, y - x)


def compare_integers(stat: Stat, number1: int, number2: int) -> t.Literal[-1, 0, 1]:
    if number1 == number2:
        return 0

    return -1 if (not stat.beneficial) ^ (number1 > number2) else 1
