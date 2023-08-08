from __future__ import annotations

import typing as t
import uuid
from bisect import bisect_left

from attrs import Factory, define, field
from typing_extensions import Self

from .. import _internal
from ..enums import Tier
from ..errors import MaxPowerError, MaxTierError

if t.TYPE_CHECKING:
    from .item import Item
    from .item_data import ItemData

__all__ = ("InvItem",)


def _get_power_bank(item: ItemData, /) -> t.Mapping[Tier, t.Sequence[int]]:
    """Returns the power per level bank for the item."""
    # TODO: legacy and sub epic items
    if item.tags.legacy:
        pass

    if item.name in _internal.SPECIAL_ITEMS:
        return _internal.REDUCED_POWERS

    if item.transform_range[0] >= Tier.LEGENDARY:
        return _internal.PREMIUM_POWERS

    if item.transform_range[-1] <= Tier.EPIC:
        pass

    return _internal.DEFAULT_POWERS


def _get_power_levels_of_item(item: Item, /) -> t.Sequence[int]:
    return _get_power_bank(item.data).get(item.stage.tier, (0,))


@define(kw_only=True)
class InvItem:
    """Represents an inventory bound item."""

    item: Item = field()

    UUID: uuid.UUID = Factory(uuid.uuid4)
    _power: int = field(default=0, init=False)

    @property
    def is_max_power(self) -> bool:
        """Whether the item has reached the maximum power for its tier."""
        return self._power == self.max_power

    @property
    def max_power(self) -> int:
        """The total power necessary to max the item at current tier."""
        return _get_power_levels_of_item(self.item)[-1]

    @property
    def transform_ready(self) -> bool:
        """Returns True if item has enough power and isn't at max tier."""
        return self.is_max_power and self.item.stage.next is not None

    @property
    def power(self) -> int:
        return self._power

    @power.setter
    def power(self, power: int) -> None:
        if power < 0:
            raise ValueError("Power cannot be negative")

        if self.is_max_power:
            raise MaxPowerError(self)

        levels = _get_power_levels_of_item(self.item)
        self.item.level = bisect_left(levels, self.power) + 1
        self._power = min(power, self.max_power)

    def __str__(self) -> str:
        return f"{self.item} {self.UUID}"

    def transform(self) -> None:
        """Transforms the item to higher tier, if it has enough power"""
        if not self.is_max_power:
            raise ValueError("Cannot transform a non-maxed item")

        if self.item.stage.next is None:
            raise MaxTierError(self)

        self.item.stage = self.item.stage.next
        self.power = 0

    @classmethod
    def from_item(cls, item: Item, /) -> Self:
        return cls(item=item)
