import typing as t
import typing_extensions as tex

import anyio

from .item import Stat
from .platform import toml_decoder

STATS: t.Mapping[Stat, "BuffData"] = {}
BUFFABLE_STATS: t.Sequence[Stat] = []
BASE_LVL_INCREASES: t.Sequence[int] = []
HIT_POINT_INCREASES: t.Sequence[int] = []


class RawBuffData(t.TypedDict):
    key: str
    beneficial: tex.NotRequired[bool]
    buff: tex.NotRequired[t.Literal["+HP", "+%", "-%", "resist%"]]


class StatsFile(t.TypedDict):
    levels: t.Mapping[str, t.Sequence[int]]
    level_percents: t.Sequence[int]
    hit_points: t.Sequence[int]
    stats: t.Sequence[RawBuffData]


class BuffData(t.NamedTuple):
    key: Stat
    beneficial: bool = True
    buff: t.Literal["+HP", "+%", "-%", "resist%"] | None = None

    def __str__(self) -> str:
        return str(self.key)


async def load_stat_data() -> None:
    async with await (anyio.Path(__file__).parent / "static/StatData.toml").open() as file:
        data: StatsFile = toml_decoder(await file.read())

    for stat_data in data["stats"]:
        stat_key = Stat.of_name(stat_data["key"])

        stat = BuffData(stat_key, stat_data.get("beneficial", True), stat_data.get("buff"))
        STATS[stat_key] = stat

        if stat.buff is not None:
            BUFFABLE_STATS.append(stat_key)

    BASE_LVL_INCREASES.extend(data["level_percents"])
    HIT_POINT_INCREASES.extend(data["hit_points"])

    from .arena_buffs import MAX_BUFFS, max_out

    max_out(MAX_BUFFS)
