from pathlib import Path

from supermechs import init
from supermechs.api import ItemData
from supermechs.ext.comparators.converter import (
    STAT_KEY_ORDER,
    ComparisonContext,
    EntryConverter,
    run_conversions,
)
from supermechs.ext.deserializers.models import to_item_data
from supermechs.item_stats import max_stats
from supermechs.platform import json_decoder


def loader(path: str, key: str, custom: bool) -> ItemData:
    with Path(path).open("rb") as file:
        return to_item_data(json_decoder(file.read()), key, custom)


async def main():
    await init()
    item1 = loader("tests/data/example_item_v2.json", "@Darkstare", False)
    item2 = loader("tests/data/incomplete_item_v3.json", "@Eneg", False)

    converter = EntryConverter(
        max_stats(item1.start_stage), max_stats(item2.start_stage), key_order=STAT_KEY_ORDER
    )
    # context = ComparisonContext()
    print(converter)
    ctx = ComparisonContext(True, True, True, True)
    run_conversions(converter, ctx)
    print(converter)

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
