import uuid
from collections import abc
from typing import Final
from typing_extensions import Self

from attrs import Factory, define, field

from .abc.item import Element, ItemID, Paint, Tag, Type
from .abc.stats import Tier, TransformStage
from .exceptions import MaxTierError, NegativeValueError, TierUnreachableError

__all__ = ("InvItem", "Item", "ItemData")


@define(kw_only=True)
class ItemData:
    """Dataclass storing item data independent of its tier and level."""

    id: Final[ItemID] = field()
    """The ID of the item."""
    name: Final[str] = field()
    """The display name of the item."""
    type: Final[Type] = field()
    """Type denoting the function of the item."""
    element: Final[Element] = field()
    """Element of the item."""
    tags: Final[abc.Set[Tag]] = field()
    """A set of tags which alter item's behavior/appearance."""
    stages: Final[abc.Sequence[TransformStage]] = field()
    """The first transformation stage of this item."""


@define(kw_only=True)
class Item:
    """Represents unique properties of an item."""

    data: Final[ItemData] = field()
    stage_index: int = field(default=0)
    level: int = field(default=0)
    paint: Paint | None = field(default=None)

    @property
    def id(self) -> ItemID:
        return self.data.id

    @property
    def name(self) -> str:
        return self.data.name

    @property
    def type(self) -> Type:
        return self.data.type

    @property
    def element(self) -> Element:
        return self.data.element

    @property
    def tags(self) -> abc.Set[Tag]:
        return self.data.tags

    @property
    def stage(self) -> TransformStage:
        return self.data.stages[self.stage_index]

    @property
    def tier(self) -> Tier:
        return self.stage.tier

    @property
    def display_level(self) -> str:
        """The level text displayed for this item."""
        return "max" if self.is_maxed else str(self.level + 1)

    @property
    def can_transform(self) -> bool:
        """Whether the item can be transformed, i.e. is not at final stage."""
        return not self.is_max_tier and self.is_max_level

    @property
    def is_max_tier(self) -> bool:
        """Whether the item reached its final stage."""
        return self.stage_index >= len(self.data.stages) - 1

    @property
    def is_max_level(self) -> bool:
        """Whether the item reached max level for its tier."""
        return self.level >= self.stage.max_level

    @property
    def is_maxed(self) -> bool:
        """Whether the item is at its final stage and level."""
        return self.is_max_tier and self.is_max_level

    def __str__(self) -> str:
        return f"[{self.stage.tier[0]}] {self.data.name} lvl {self.display_level}"

    def transform(self) -> None:
        """Swap the stage of this item one tier higher."""
        if self.is_max_tier:
            raise MaxTierError

        if not self.is_max_level:
            msg = "Cannot transform before reaching max level"
            raise ValueError(msg)

        self.stage_index += 1

    @classmethod
    def maxed(cls, data: ItemData, /) -> Self:
        """Create an Item at maximum tier and level."""
        index = len(data.stages) - 1
        return cls(data=data, stage_index=index, level=data.stages[index].max_level)

    @classmethod
    def at_tier(cls, data: ItemData, /, tier: Tier) -> Self:
        """Create an Item at given tier."""
        for i, stage in enumerate(data.stages):
            if stage.tier == tier:
                return cls(data=data, stage_index=i)

        raise TierUnreachableError(tier)


@define(kw_only=True)
class InvItem:
    """Represents an inventory bound item."""

    item: Final[Item] = field()
    UUID: Final[uuid.UUID] = Factory(uuid.uuid4)
    _power: int = field(default=0, init=False)

    @property
    def is_max_power(self) -> bool:
        """Whether the item has reached the maximum power for its tier."""
        return self._power == self.max_power

    @property
    def max_power(self) -> int:
        """The total power necessary to max the item at current tier."""
        return self.item.stage.max_power()

    @property
    def can_transform(self) -> bool:
        """True if item has enough power and isn't at max tier."""
        return self.is_max_power and self.item.can_transform

    @property
    def power(self) -> int:
        return self._power

    @power.setter
    def power(self, power: int, /) -> None:
        if power < 0:
            raise NegativeValueError(power)

        power = self.item.stage.clamp_power(power)
        self._power = power
        self.item.level = self.item.stage.level_at(power)

    def __str__(self) -> str:
        return f"{self.item} {self.UUID}"

    def transform(self) -> None:
        """Transform the item to higher tier, if it has enough power."""
        if not self.is_max_power:
            msg = "Cannot transform a non-maxed item"
            raise ValueError(msg)

        self.item.transform()
        self.power = 0
