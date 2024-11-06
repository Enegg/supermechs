from collections import abc
from typing import Final
from typing_extensions import Self, override

import attrs
import attrs.validators as v

import supermechs.abc as sabc
from supermechs.utils import default

__all__ = ("ItemData", "ItemStats", "StageLevel", "TransformStage")

_ZERO = 0.0


@attrs.define(kw_only=True)
class ItemStats:
    @default
    @staticmethod
    def zeros() -> sabc.ItemStats:
        return ItemStats()

    weight: float = _ZERO
    hit_points: float = _ZERO
    energy_capacity: float = _ZERO
    regeneration: float = _ZERO
    heat_capacity: float = _ZERO
    cooling: float = _ZERO
    physical_resistance: float = _ZERO
    explosive_resistance: float = _ZERO
    electric_resistance: float = _ZERO
    bullets_capacity: float = _ZERO
    rockets_capacity: float = _ZERO
    walk: float = _ZERO
    jump: float = _ZERO
    physical_damage: float = _ZERO
    physical_damage_addon: float = _ZERO
    physical_resistance_damage: float = _ZERO
    electric_damage: float = _ZERO
    electric_damage_addon: float = _ZERO
    energy_damage: float = _ZERO
    energy_capacity_damage: float = _ZERO
    regeneration_damage: float = _ZERO
    electric_resistance_damage: float = _ZERO
    explosive_damage: float = _ZERO
    explosive_damage_addon: float = _ZERO
    heat_damage: float = _ZERO
    heat_capacity_damage: float = _ZERO
    cooling_damage: float = _ZERO
    explosive_resistance_damage: float = _ZERO
    range: float = _ZERO
    range_addon: float = _ZERO
    push: float = _ZERO
    pull: float = _ZERO
    recoil: float = _ZERO
    advance: float = _ZERO
    retreat: float = _ZERO
    uses: float = _ZERO
    backfire: float = _ZERO
    heat_generation: float = _ZERO
    energy_cost: float = _ZERO
    bullets_cost: float = _ZERO
    rockets_cost: float = _ZERO


@attrs.define(kw_only=True)
class StageLevel:
    power: int
    stats: ItemStats


@attrs.define(kw_only=True)
class TransformStage:
    tier: sabc.StageTier
    levels: abc.Sequence[sabc.StageLevel] = attrs.field(validator=v.min_len(1))


@attrs.define(kw_only=True)
class ItemData:
    id: sabc.ItemID
    name: str
    type: sabc.ItemType
    element: sabc.ItemElement
    stages: abc.Sequence[sabc.TransformStage] = attrs.field(validator=v.min_len(1))
    tags: abc.Set[sabc.ItemTag] = frozenset()


@attrs.define(kw_only=True)
class Item:
    data: Final[ItemData]
    _stage: int = 0
    level: int = 0
    paint: sabc.ItemPaint | None = None

    @property
    def id(self) -> sabc.ItemID:
        return self.data.id

    @property
    def name(self) -> str:
        return self.data.name

    @property
    def type(self) -> sabc.ItemType:
        return self.data.type

    @property
    def element(self) -> sabc.ItemElement:
        return self.data.element

    @property
    def tags(self) -> abc.Set[sabc.ItemTag]:
        return self.data.tags

    @property
    def stage(self) -> sabc.TransformStage:
        return self.data.stages[self._stage]

    @property
    def tier(self) -> sabc.StageTier:
        return self.stage.tier

    @property
    def stats(self) -> sabc.ItemStats:
        return self.stage.levels[self.level].stats

    @override
    def __str__(self) -> str:
        return f"{self.data} at {self.tier} lvl {self.level}"

    @classmethod
    def maxed(cls, data: ItemData, /) -> Self:
        self = cls(data=data)
        self._stage = len(data.stages) - 1
        return self

    @classmethod
    def at_tier(cls, data: ItemData, tier: sabc.StageTier) -> Self:
        for i, stage in enumerate(data.stages):
            if stage.tier == tier:
                self = cls(data=data)
                self._stage = i
                return self

        msg = f"Item {data} does not reach tier {tier}"
        raise ValueError(msg) from None
