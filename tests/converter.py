from pathlib import Path

import orjson

from supermechs.api import Item
from supermechs.ext.comparators.converter import (
    STAT_KEY_ORDER,
    ComparisonContext,
    EntryConverter,
)


def loader(path: str, key: str, custom: bool) -> Item:
    with Path(path).open("b") as file:
        return Item.from_json(orjson.loads(file.read()), key, custom)


async def main():
    item1 = loader("tests/data/example_item_v2.json", "@Darkstare", False)
    item2 = loader("tests/data/incomplete_item_v3.json", "@Eneg", False)

    comparator = EntryConverter(item1.max_stats, item2.max_stats, key_order=STAT_KEY_ORDER)
    context = ComparisonContext()

    breakpoint()
    del context, comparator


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
