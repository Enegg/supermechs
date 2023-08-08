import logging

from ._internal import load_power_data, load_stat_data

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
LOGGER.addHandler(logging.NullHandler())


async def init() -> None:
    await load_power_data()
    await load_stat_data()
