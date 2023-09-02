import typing as t
from typing_extensions import Self

from attrs import define, field

from ..item_stats import AnyStatsMapping
from .inv_item import InvItem

__all__ = ("BattleItem",)
# XXX: should the multipliers be applied on BattleItem creation, or should it hold a reference?
# BattleItem should be constructible without an InvItem; it has nothing to do with inventory

def apply_multipliers(
    stats: AnyStatsMapping, multipliers: t.Mapping[str, float] = {}, /, **mults: float
) -> None:
    """WIP"""
    for key, value in {**multipliers, **mults}.items():
        old = stats.get(key)

        if old is None:
            continue

        stats[key] = round(old * value)


def battle_item_factory(base_item: InvItem, multipliers: dict[str, float] = {}, ) -> "BattleItem":
    """Create a BattleItem with pre-applied multipliers."""
    stats = base_item.item.current_stats
    apply_multipliers(stats, multipliers)
    return BattleItem.from_item(base_item)


@define
class BattleItem:
    """Represents the state of an item during a battle."""
    item: InvItem
    stats: AnyStatsMapping
    multipliers: t.Mapping[str, float] = field(factory=dict)
    # already_used: bool? XXX prolly better to store elsewhere

    @classmethod
    def from_item(cls, inv_item: InvItem, /) -> Self:
        return cls(item=inv_item, stats=inv_item.item.current_stats)
