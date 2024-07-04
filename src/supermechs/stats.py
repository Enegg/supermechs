from typing import TypeAlias

from .abc.stats import Stat, StatValue

__all__ = ("StatsDict",)

StatsDict: TypeAlias = dict[Stat, StatValue]
"""Concrete mapping type of item stats to values."""
