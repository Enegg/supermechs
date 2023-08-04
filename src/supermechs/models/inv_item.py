from __future__ import annotations

import typing as t
import uuid
from bisect import bisect_left
from pathlib import Path

from attrs import Factory, define, field
from typing_extensions import Self

from ..enums import Tier
from ..errors import MaxPowerError, MaxTierError
from ..utils import cached_slot_property

if t.TYPE_CHECKING:
    from ..item_stats import AnyStatsMapping
    from .display_item import DisplayItem
    from .item_data import ItemData

__all__ = ("InvItem",)


def _read_power_data_files() -> t.Iterator[dict[Tier, tuple[int, ...]]]:
    path = Path(__file__).parent / "static"
    file_names = ("default_powers.csv", "premium_powers.csv", "reduced_powers.csv")
    iterables = (Tier, (Tier.LEGENDARY, Tier.MYTHICAL), (Tier.LEGENDARY, Tier.MYTHICAL))

    import csv

    for file_name, rarities in zip(file_names, iterables):
        file_path = path / file_name

        with file_path.open(newline="") as file:
            rows = csv.reader(file, skipinitialspace=True)

            yield {rarity: tuple(map(int, row)) for rarity, row in zip(rarities, rows)}


def _load_power_data() -> None:
    global _powers, _loaded
    _powers = _Powers(*_read_power_data_files())
    _loaded = True


class _Powers(t.NamedTuple):
    default: t.Mapping[Tier, t.Sequence[int]]
    premium: t.Mapping[Tier, t.Sequence[int]]
    reduced: t.Mapping[Tier, t.Sequence[int]]


_powers: _Powers
_loaded: bool = False


# this could very well be by IDs, but names are easier to read
_REDUCED_COST_ITEMS = frozenset(("Archimonde", "Armor Annihilator", "BigDaddy", "Chaos Bringer"))


def next_tier(current: Tier, /) -> Tier:
    """Returns the next tier in line."""
    return Tier.get_by_value(current.value + 1)


def get_power_bank(item: ItemData, /) -> t.Mapping[Tier, t.Sequence[int]]:
    """Returns the power per level bank for the item."""
    global _powers, _loaded

    if not _loaded:
        _load_power_data()

    if item.tags.legacy:
        pass

    if item.name in _REDUCED_COST_ITEMS:
        return _powers.reduced

    if item.transform_range[0] >= Tier.LEGENDARY:
        return _powers.premium

    if item.transform_range[-1] <= Tier.EPIC:
        # TODO: this has special case too, but currently I have no data on that
        pass

    return _powers.default


def get_power_levels_of_item(item: InvItem, /) -> t.Sequence[int]:
    return get_power_bank(item.item.data).get(item.tier, (0,))


@define(kw_only=True)
class InvItem:
    """Represents an inventory bound item."""

    item: DisplayItem

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
        """The total power necessary to max the item at current tier."""
        return get_power_levels_of_item(self)[-1]

    @cached_slot_property
    def current_stats(self) -> AnyStatsMapping:
        """The stats of this item at its particular tier and level."""
        return self.item.base.stats.at(self.level)

    @cached_slot_property
    def level(self) -> int:
        """The level of this item."""
        del self.current_stats
        levels = get_power_levels_of_item(self)
        return bisect_left(levels, self.power) + 1

    def __str__(self) -> str:
        return f"{self.item} {self.UUID}"

    def add_power(self, power: int) -> None:
        """Adds power to the item."""

        if power < 0:
            raise ValueError("Power cannot be negative")

        if self.maxed:
            raise MaxPowerError(self)

        del self.level
        self.power = min(self.power + power, self.max_power)

    def is_transform_ready(self) -> bool:
        """Returns True if item has enough power to transform
        and hasn't reached max transform tier, False otherwise"""
        return self.maxed and self.tier < self.item.data.transform_range[-1]

    def transform(self) -> None:
        """Transforms the item to higher tier, if it has enough power"""
        if not self.maxed:
            raise ValueError("Cannot transform a non-maxed item")

        if self.tier is self.item.data.transform_range[-1]:
            raise MaxTierError(self)

        self.tier = next_tier(self.tier)
        self.power = 0

    @classmethod
    def from_item(cls, item: DisplayItem, /) -> Self:
        return cls(item=item)
