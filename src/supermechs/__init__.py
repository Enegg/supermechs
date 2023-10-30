import logging

logging.getLogger(__name__).addHandler(logging.NullHandler())


async def init() -> None:
    from ._internal import load_stat_data

    await load_stat_data()
