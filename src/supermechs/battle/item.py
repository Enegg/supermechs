from collections import abc
from typing import Final

from attrs import define, field

from supermechs.abc.stats import StatsMapping
from supermechs.item import Item

__all__ = ("BattleItem",)

# XXX: should the multipliers be applied on BattleItem creation, or should it hold a reference?
# BattleItem should be constructible without an InvItem; it has nothing to do with inventory


@define
class BattleItem:
    """Represents the state of an item during a battle."""

    item: Final[Item]
    stats: Final[StatsMapping]
    multipliers: abc.Mapping[str, float] = field(factory=dict)
    # already_used: bool? XXX probably better to store elsewhere
