from pathlib import Path

from supermechs.api import ItemData
from supermechs.stats import max_stats
from supermechs.typeshed import PackKey

from supermechs.ext.comparators.converter import (
    STAT_KEY_ORDER,
    ComparisonContext,
    EntryConverter,
    run_conversions,
)
from supermechs.ext.deserializers.models import to_item_data
from supermechs.ext.platform import json_decoder


def loader(path: str, key: PackKey, custom: bool) -> ItemData:
    with Path(path).open("rb") as file:
        return to_item_data(json_decoder(file.read()), key)


async def main():
    item1 = loader("tests/data/example_item_v2.json", PackKey("@Darkstare"), False)
    item2 = loader("tests/data/incomplete_item_v3.json", PackKey("@Eneg"), False)

    converter = EntryConverter(
        max_stats(item1.start_stage), max_stats(item2.start_stage), key_order=STAT_KEY_ORDER
    )
    print(converter)
    ctx = ComparisonContext(True, True, True, True)
    run_conversions(converter, ctx)
    print(converter)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
