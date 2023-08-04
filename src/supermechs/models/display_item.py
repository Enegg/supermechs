import typing as t

import typing_extensions as tex
from attrs import define, field

from ..core import MAX_LVL_FOR_TIER
from ..enums import Tier
from ..item_stats import AnyStatsMapping, TransformStage, get_final_stage
from .item_data import ItemData

__all__ = ("DisplayItem",)


Paint: t.TypeAlias = str
"""The name of the paint, of a hex string defining the monolithic color."""


@define(kw_only=True)
class DisplayItem:
    """Represents unique properties of an item."""

    data: ItemData = field()
    stage: "TransformStage" = field()

    level: int = field(default=0)
    display_level: str = field(default="1")
    paint: Paint | None = field(default=None)

    @property
    def current_stats(self) -> "AnyStatsMapping":
        """The stats of this item at its particular tier and level."""
        return self.stage.at(self.level)

    def __str__(self) -> str:
        return f"[{self.stage.tier.name[0]}] {self.data.name} lvl {self.display_level}"

    @classmethod
    def from_data(
        cls, data: ItemData, stage: "TransformStage", /, *, maxed: bool = False
    ) -> tex.Self:
        if maxed:
            stage = get_final_stage(stage)

        level = MAX_LVL_FOR_TIER[stage.tier] if maxed else 0
        display_level = "max" if stage.tier is Tier.DIVINE else str(level + 1)
        return cls(data=data, stage=stage, level=level, display_level=display_level)
