import logging
import typing as t

from supermechs.item_pack import ItemPack
from supermechs.urls import PACK_V2

logging.basicConfig(level=logging.DEBUG)


async def runner(link: str = PACK_V2, **extra: t.Any):
    from aiohttp import ClientSession

    # import yarl

    logging.basicConfig(level="INFO")
    async with ClientSession() as session:
        async with session.get(link) as response:
            return ItemPack.from_json(await response.json(content_type=None))
