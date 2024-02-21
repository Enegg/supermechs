from collections import abc
from typing import Any, TypeAlias

from ..enums.stats import Stat

__all__ = ("MutableStatsMapping", "StatsMapping")

StatType: TypeAlias = Any  # TODO: concrete stat type
StatsMapping: TypeAlias = abc.Mapping[Stat, StatType]
"""Generic mapping of item stats to their values."""
MutableStatsMapping: TypeAlias = abc.MutableMapping[Stat, StatType]
"""Generic mutable mapping of item stats to their values."""
