import typing as t
import typing_extensions as tex

import anyio

from .enums import Tier
from .platform import toml_decoder

DEFAULT_POWERS: t.Mapping[Tier, t.Sequence[int]] = {}
PREMIUM_POWERS: t.Mapping[Tier, t.Sequence[int]] = {}
REDUCED_POWERS: t.Mapping[Tier, t.Sequence[int]] = {}
STATS: t.Mapping[str, "Stat"] = {}
BUFFABLE_STATS: t.Sequence[str] = []
BASE_LVL_INCREASES: t.Sequence[int] = []
HIT_POINT_INCREASES: t.Sequence[int] = []


# this could very well be by IDs, but names are easier to read
SPECIAL_ITEMS = frozenset(("Archimonde", "Armor Annihilator", "BigDaddy", "Chaos Bringer"))


async def load_power_data() -> None:
    path = anyio.Path(__file__).parent / "static"
    file_names = ("default_powers.csv", "premium_powers.csv", "reduced_powers.csv")
    iterables = (Tier, (Tier.LEGENDARY, Tier.MYTHICAL), (Tier.LEGENDARY, Tier.MYTHICAL))
    mappings = (DEFAULT_POWERS, PREMIUM_POWERS, REDUCED_POWERS)

    import csv

    async def worker(
        file_name: str, rarities: t.Iterable[Tier], mapping: dict[Tier, t.Sequence[int]]
    ) -> None:
        async with await (path / file_name).open(newline="") as file:
            rows = csv.reader(await file.readlines(), skipinitialspace=True)
            for rarity, row in zip(rarities, rows):
                mapping[rarity] = tuple(map(int, row))

    async with anyio.create_task_group() as tg:
        for file_name, rarities, mapping in zip(file_names, iterables, mappings, strict=True):
            tg.start_soon(worker, file_name, rarities, mapping)


class StatData(t.TypedDict):
    key: str
    beneficial: tex.NotRequired[bool]
    buff: tex.NotRequired[t.Literal["+HP", "+%", "-%", "resist%"]]


class StatsData(t.TypedDict):
    levels: t.Mapping[str, t.Sequence[int]]
    level_percents: t.Sequence[int]
    hit_points: t.Sequence[int]
    stats: t.Sequence[StatData]


class Stat(t.NamedTuple):
    key: str
    beneficial: bool = True
    buff: t.Literal["+HP", "+%", "-%", "resist%"] | None = None

    def __str__(self) -> str:
        return self.key

    def __hash__(self) -> int:
        return hash((self.key, type(self)))


async def load_stat_data() -> None:
    async with await (anyio.Path(__file__).parent / "static/StatData.toml").open() as file:
        data: StatsData = toml_decoder(await file.read())

    for stat_data in data["stats"]:
        stat_key = stat_data["key"]
        stat = Stat(stat_key, stat_data.get("beneficial", True), stat_data.get("buff"))
        STATS[stat_key] = stat

        if stat.buff is not None:
            BUFFABLE_STATS.append(stat_key)

    BASE_LVL_INCREASES.extend(data["level_percents"])
    HIT_POINT_INCREASES.extend(data["hit_points"])

    from .arena_buffs import MAX_BUFFS, max_out

    max_out(MAX_BUFFS)
