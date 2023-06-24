from attrs import define, field
from typing_extensions import Self

from ..item_stats import AnyStatsMapping
from .inv_item import InvItem

# XXX: should the multipliers be applied on BattleItem creation, or should it hold a reference?

def apply_multipliers(
    stats: AnyStatsMapping, multipliers: dict[str, float] = {}, /, **mults: float
) -> None:
    """"""
    for key, value in {**multipliers, **mults}.items():
        old = stats.get(key)

        if old is None:
            continue

        stats[key] = round(old * value)


def battle_item_factory(base_item: InvItem, multipliers: dict[str, float] = {}, ) -> "BattleItem":
    """Create a BattleItem with pre-applied multipliers."""
    stats = base_item.current_stats
    apply_multipliers(stats, multipliers)
    return BattleItem.from_item(base_item)


@define
class BattleItem:
    """Represents the state of an item during a battle."""
    item: InvItem
    stats: AnyStatsMapping
    multipliers: dict[str, float] = field(factory=dict)
    # XXX already_used: bool? ...prolly better to store elsewhere

    @classmethod
    def from_item(cls, item: InvItem, /) -> Self:
        return cls(item=item, stats=item.current_stats)
