from collections import abc
from typing import Any, Protocol, TypeAlias

from supermechs.enums.stats import Stat

__all__ = ("MutableStatsMapping", "StatsMapping")

StatType: TypeAlias = Any  # TODO: concrete stat type
StatsMapping: TypeAlias = abc.Mapping[Stat, StatType]
"""Generic mapping of item stats to their values."""
MutableStatsMapping: TypeAlias = abc.MutableMapping[Stat, StatType]
"""Generic mutable mapping of item stats to their values."""


class StatsProvider(Protocol):
    def __contains__(self, stat: Stat, /) -> bool:
        ...

    def at(self, level: int, /) -> StatsMapping:
        """Return the stats at given level."""
        ...
