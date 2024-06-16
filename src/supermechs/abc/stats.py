from collections import abc
from typing import Any, Protocol, TypeAlias

__all__ = ("MutableStatsMapping", "Stat", "StatValue", "StatsMapping", "Tier")

Stat: TypeAlias = str
Tier: TypeAlias = str

StatValue: TypeAlias = Any  # TODO: concrete stat type
StatsMapping: TypeAlias = abc.Mapping[Stat, StatValue]
"""Generic mapping of item stats to their values."""
MutableStatsMapping: TypeAlias = abc.MutableMapping[Stat, StatValue]
"""Generic mutable mapping of item stats to their values."""


class StatsProvider(Protocol):
    def __contains__(self, stat: Stat, /) -> bool: ...

    def at(self, level: int, /) -> StatsMapping:
        """Return the stats at given level."""
        ...
