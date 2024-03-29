from collections import abc

from supermechs.enums.stats import Tier
from supermechs.item import ItemData

__all__ = ("transform_range",)


def transform_range(item: ItemData, /) -> abc.Sequence[Tier]:
    """Construct a transform range from item data."""
    return tuple(stage.tier for stage in item.iter_stages())
