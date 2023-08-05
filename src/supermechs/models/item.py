import typing as t

import typing_extensions as tex
from attrs import define, field

from ..item_stats import AnyStatsMapping, TransformStage, get_final_stage
from .item_data import ItemData

__all__ = ("Item",)


Paint: t.TypeAlias = str
"""The name of the paint, or a #-prefixed hex string as a color."""


@define(kw_only=True)
class Item:
    """Represents unique properties of an item."""

    data: ItemData = field()
    stage: "TransformStage" = field()
    level: int = field(default=0)
    paint: Paint | None = field(default=None)

    @property
    def current_stats(self) -> "AnyStatsMapping":
        """The stats of this item at its particular tier and level."""
        return self.stage.at(self.level)

    @property
    def is_maxed(self) -> bool:
        """Whether the item is at final stage and level."""
        return self.stage.next is None and self.level == self.stage.max_level

    @property
    def display_level(self) -> str:
        """The level text displayed for this item."""
        return "max" if self.is_maxed else str(self.level + 1)

    def __str__(self) -> str:
        return f"[{self.stage.tier.name[0]}] {self.data.name} lvl {self.display_level}"

    @classmethod
    def from_data(
        cls, data: ItemData, stage: "TransformStage", /, *, maxed: bool = False
    ) -> tex.Self:
        if maxed:
            stage = get_final_stage(stage)

        level = stage.max_level if maxed else 0
        return cls(data=data, stage=stage, level=level)
