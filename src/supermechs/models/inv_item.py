from __future__ import annotations

import typing as t
import uuid
from bisect import bisect_left
from pathlib import Path

from attrs import Factory, define, field
from typing_extensions import Self

from ..core import TransformRange, next_tier
from ..enums import Element, Tier, Type
from ..errors import MaxPowerError, MaxTierError
from ..item_stats import AnyStatsMapping, ItemStats
from ..typedefs import ID, Name
from ..utils import cached_slot_property
from .item_base import ItemBase, ItemProto, Tags

__all__ = ("InvItem", "InvItemProto")


def _load_power_data_files() -> t.Iterator[dict[Tier, tuple[int, ...]]]:
    path = Path(__file__).parent / "static"
    file_names = ("default_powers.csv", "premium_powers.csv", "reduced_powers.csv")
    iterables = (Tier, (Tier.LEGENDARY, Tier.MYTHICAL), (Tier.LEGENDARY, Tier.MYTHICAL))

    import csv

    for file_name, rarities in zip(file_names, iterables):
        file_path = path / file_name

        with file_path.open(newline="") as file:
            rows = csv.reader(file, skipinitialspace=True)

            yield {rarity: tuple(map(int, row)) for rarity, row in zip(rarities, rows)}


class _Powers(t.NamedTuple):
    default: dict[Tier, tuple[int, ...]]
    premium: dict[Tier, tuple[int, ...]]
    reduced: dict[Tier, tuple[int, ...]]


_powers: _Powers
_loaded: bool = False


# this could very well be by IDs, but names are easier to read
_REDUCED_COST_ITEMS = frozenset(("Archimonde", "Armor Annihilator", "BigDaddy", "Chaos Bringer"))


def get_power_bank(item: ItemProto) -> dict[Tier, tuple[int, ...]]:
    """Returns the power per level bank for the item."""
    global _powers, _loaded

    if not _loaded:
        _powers = _Powers(*_load_power_data_files())
        _loaded = True

    if item.tags.legacy:
        pass

    if item.name in _REDUCED_COST_ITEMS:
        return _powers.reduced

    if item.transform_range.min >= Tier.LEGENDARY:
        return _powers.premium

    if item.transform_range.max <= Tier.EPIC:
        # TODO: this has special case too, but currently I have no data on that
        pass

    return _powers.default


def get_power_levels_of_item(item: InvItemProto) -> tuple[int, ...]:
    return get_power_bank(item).get(item.tier, (0,))


class InvItemProto(ItemProto, t.Protocol):
    @property
    def tier(self) -> Tier:
        ...

    @cached_slot_property
    def level(self) -> int:
        ...

    @cached_slot_property
    def current_stats(self) -> AnyStatsMapping:
        ...


@define(kw_only=True)
class InvItem:
    """Represents an item inside inventory."""

    base: ItemBase

    @property
    def id(self) -> ID:
        return self.base.id

    @property
    def pack_key(self) -> str:
        return self.base.pack_key

    @property
    def name(self) -> Name:
        return self.base.name

    @property
    def type(self) -> Type:
        return self.base.type

    @property
    def element(self) -> Element:
        return self.base.element

    @property
    def transform_range(self) -> TransformRange:
        return self.base.transform_range

    @property
    def stats(self) -> ItemStats:
        return self.base.stats

    @property
    def tags(self) -> Tags:
        return self.base.tags

    tier: Tier
    power: int = 0
    UUID: uuid.UUID = Factory(uuid.uuid4)
    _level: int = field(init=False, repr=False, eq=False)
    _current_stats: AnyStatsMapping = field(init=False, repr=False, eq=False)

    @property
    def maxed(self) -> bool:
        """Whether the item has reached the maximum power for its tier."""
        return self.power == self.max_power

    @property
    def max_power(self) -> int:
        """Returns the total power necessary to max the item at current tier."""
        return get_power_levels_of_item(self)[-1]

    @cached_slot_property
    def current_stats(self) -> AnyStatsMapping:
        """The stats of this item at its particular tier and level."""
        return self.base.stats[self.tier].at(self.level)

    @cached_slot_property
    def level(self) -> int:
        """The level of this item."""
        del self.current_stats
        levels = get_power_levels_of_item(self)
        return bisect_left(levels, self.power) + 1

    def __str__(self) -> str:
        level = "max" if self.maxed else self.level
        return f"[{self.tier.name[0]}] {self.name} lvl {level}"

    def add_power(self, power: int) -> None:
        """Adds power to the item."""

        if power < 0:
            raise ValueError("Power cannot be negative")

        if self.maxed:
            raise MaxPowerError(self)

        del self.level
        self.power = min(self.power + power, self.max_power)

    def is_ready_to_transform(self) -> bool:
        """Returns True if item has enough power to transform
        and hasn't reached max transform tier, False otherwise"""
        return self.maxed and self.tier < self.transform_range.max

    def transform(self) -> None:
        """Transforms the item to higher tier, if it has enough power"""
        if not self.maxed:
            raise ValueError("Cannot transform a non-maxed item")

        if self.tier is self.transform_range.max:
            raise MaxTierError(self)

        self.tier = next_tier(self.tier)
        self.power = 0

    @classmethod
    def from_item(cls, item: ItemBase, /, *, maxed: bool = False) -> Self:
        return cls(base=item, tier=item.transform_range.max if maxed else item.transform_range.min)
