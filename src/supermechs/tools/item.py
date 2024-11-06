from collections import abc

from supermechs.abc import HasStages, StageTier

__all__ = ("transform_range",)


def transform_range(item: HasStages, /) -> abc.Sequence[StageTier]:
    """Construct a transform range from item data."""
    return tuple(stage.tier for stage in item.stages)
