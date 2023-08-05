from __future__ import annotations

import typing as t
import uuid
from bisect import bisect_left
from pathlib import Path

from attrs import Factory, define
from typing_extensions import Self

from ..enums import Tier
from ..errors import MaxPowerError, MaxTierError

if t.TYPE_CHECKING:
    from .item import Item
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


def get_power_levels_of_item(item: Item, /) -> t.Sequence[int]:
    return get_power_bank(item.data).get(item.stage.tier, (0,))


@define(kw_only=True)
class InvItem:
    """Represents an inventory bound item."""

    item: Item

    UUID: uuid.UUID = Factory(uuid.uuid4)
    _power: int = 0

    @property
    def is_max_power(self) -> bool:
        """Whether the item has reached the maximum power for its tier."""
        return self._power == self.max_power

    @property
    def max_power(self) -> int:
        """The total power necessary to max the item at current tier."""
        return get_power_levels_of_item(self.item)[-1]

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

        levels = get_power_levels_of_item(self.item)
        self.item.level = bisect_left(levels, self.power) + 1
        self._power = min(self._power + power, self.max_power)

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
        self.item.level = 0

    @classmethod
    def from_item(cls, item: Item, /) -> Self:
        return cls(item=item)
