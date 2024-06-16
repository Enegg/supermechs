import uuid
from bisect import bisect_left
from collections import abc
from typing import Final
from typing_extensions import Self

from attrs import Factory, define, field

from .abc.item import Element, ItemID, Paint, Tag, Type
from .abc.stats import Tier
from .exceptions import MaxTierError, NegativeValueError, TierUnreachableError
from .stats import TransformStage, get_final_stage

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
    start_stage: Final[TransformStage] = field()
    """The first transformation stage of this item."""

    def iter_stages(self) -> abc.Iterator[TransformStage]:
        """Iterate over the transform stages of this item."""
        stage = self.start_stage
        yield stage

        while stage := stage.next:
            yield stage


@define(kw_only=True)
class Item:
    """Represents unique properties of an item."""

    data: Final[ItemData] = field()
    stage: TransformStage = field()
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
    def tier(self) -> Tier:
        return self.stage.tier

    @property
    def display_level(self) -> str:
        """The level text displayed for this item."""
        return "max" if self.is_maxed else str(self.level + 1)

    @property
    def can_transform(self) -> bool:
        """Whether the item can be transformed, i.e. is not at final stage."""
        return self.stage.next is not None

    @property
    def is_max_level(self) -> bool:
        """Whether the item reached max level for its tier."""
        return self.level == self.stage.max_level

    @property
    def is_maxed(self) -> bool:
        """Whether the item is at its final stage and level."""
        return not self.can_transform and self.is_max_level

    def __str__(self) -> str:
        return f"[{self.stage.tier[0]}] {self.data.name} lvl {self.display_level}"

    def transform(self) -> None:
        """Swap the stage of this item one tier higher."""
        if self.stage.next is None:
            raise MaxTierError

        self.stage = self.stage.next

    @classmethod
    def maxed(cls, data: ItemData, /) -> Self:
        """Create an Item at maximum tier and level."""
        stage = get_final_stage(data.start_stage)
        return cls(data=data, stage=stage, level=stage.max_level)

    @classmethod
    def at_tier(cls, data: ItemData, /, tier: Tier) -> Self:
        """Create an Item at given tier."""
        for stage in data.iter_stages():
            if stage.tier == tier:
                return cls(data=data, stage=stage)

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
        return self.item.stage.level_progression[-1]

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

        progression = self.item.stage.level_progression
        power = min(power, progression[-1])
        self._power = power
        self.item.level = bisect_left(progression, power) + 1

    def __str__(self) -> str:
        return f"{self.item} {self.UUID}"

    def transform(self) -> None:
        """Transform the item to higher tier, if it has enough power."""
        if not self.is_max_power:
            msg = "Cannot transform a non-maxed item"
            raise ValueError(msg)

        self.item.transform()
        self.power = 0
