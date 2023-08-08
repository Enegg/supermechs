import typing as t

import anyio

from . import core
from .enums import Tier
from .platform import json_decoder

if t.TYPE_CHECKING:
    from .typedefs import AnyStatKey, StatData

DEFAULT_POWERS: t.Mapping[Tier, t.Sequence[int]] = {}
PREMIUM_POWERS: t.Mapping[Tier, t.Sequence[int]] = {}
REDUCED_POWERS: t.Mapping[Tier, t.Sequence[int]] = {}
STATS: t.Mapping[str, "core.Stat"] = {}


# this could very well be by IDs, but names are easier to read
SPECIAL_ITEMS = frozenset(("Archimonde", "Armor Annihilator", "BigDaddy", "Chaos Bringer"))


async def load_power_data() -> None:
    path = anyio.Path(__file__).parent / "static"
    file_names = ("default_powers.csv", "premium_powers.csv", "reduced_powers.csv")
    iterables = (Tier, (Tier.LEGENDARY, Tier.MYTHICAL), (Tier.LEGENDARY, Tier.MYTHICAL))
    mappings = (DEFAULT_POWERS, PREMIUM_POWERS, REDUCED_POWERS)

    import csv

    async def worker(
        file_name: str, rarities: t.Iterable[Tier], mapping: t.MutableMapping[Tier, t.Sequence[int]]
    ) -> None:
        async with await (path / file_name).open(newline="") as file:
            rows = csv.reader(await file.readlines(), skipinitialspace=True)
            for rarity, row in zip(rarities, rows):
                mapping[rarity] = tuple(map(int, row))

    async with anyio.create_task_group() as tg:
        for file_name, rarities, mapping in zip(file_names, iterables, mappings, strict=True):
            tg.start_soon(worker, file_name, rarities, mapping)


async def load_stat_data() -> None:
    async with await (anyio.Path(__file__).parent / "static/StatData.json").open() as file:
        json: dict[AnyStatKey, StatData] = json_decoder(await file.read())

    for stat_key, data in json.items():
        STATS[stat_key] = core.Stat.from_dict(data, stat_key)
