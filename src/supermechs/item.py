import uuid
from bisect import bisect_left
from collections import abc
from typing import Final, NamedTuple

from attrs import Factory, define, field, validators
from typing_extensions import Self

from .abc.item import ItemID, Name, Paint
from .abc.item_pack import PackKey
from .enums.item import Element, Type
from .enums.stats import Tier
from .errors import MaxTierError, NegativeValueError, OutOfRangeError, TierUnreachableError
from .stats import TransformStage, get_final_stage

__all__ = ("InvItem", "Item", "ItemData", "Tags")


class Tags(NamedTuple):
    """Lightweight class for storing a set of boolean tags about an item."""

    premium: bool = False
    """Whether the item is considered "premium"."""
    sword: bool = False
    """Whether the item "swings" in its animation."""
    melee: bool = False
    """Whether the item is a melee weapon."""
    roller: bool = False
    """Specific to legs, whether they roll or walk."""
    legacy: bool = False
    """Whether the item is considered legacy."""
    require_jump: bool = False
    """Whether the item requires the ability to jump to be equipped."""
    custom: bool = False
    """Whether the item is not from the default item pack."""

    @classmethod
    def from_keywords(cls, it: abc.Iterable[str], /) -> Self:
        """Create Tags object from an iterable of string attributes."""
        return cls(**dict.fromkeys(it, True))


@define(kw_only=True)
class ItemData:
    """Dataclass storing item data independent of its tier and level."""

    id: Final[ItemID] = field(validator=validators.ge(1))
    """The ID of the item, unique within its pack."""
    pack_key: Final[PackKey] = field()
    """The key of the pack this item comes from."""
    name: Final[Name] = field(validator=validators.min_len(1))
    """The display name of the item."""
    type: Final[Type] = field(validator=validators.in_(Type), repr=str)
    """Member of Type enum denoting the function of the item."""
    element: Final[Element] = field(validator=validators.in_(Element), repr=str)
    """Member of Element enum denoting the element of the item."""
    tags: Final[Tags] = field()
    """A set of boolean tags which alter item's behavior/appearance."""
    start_stage: Final[TransformStage] = field()
    """The first transformation stage of this item."""

    def iter_stages(self) -> abc.Iterator[TransformStage]:
        """Iterator over the transform stages of this item."""
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
    def pack_key(self) -> PackKey:
        return self.data.pack_key

    @property
    def name(self) -> Name:
        return self.data.name

    @property
    def type(self) -> Type:
        return self.data.type

    @property
    def element(self) -> Element:
        return self.data.element

    @property
    def tags(self) -> Tags:
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
        return f"[{self.stage.tier.name[0]}] {self.data.name} lvl {self.display_level}"

    def transform(self) -> None:
        """Swap the stage of this item one tier higher."""

        if self.stage.next is None:
            raise MaxTierError

        self.stage = self.stage.next

    @classmethod
    def from_data(cls, data: ItemData, /, tier: Tier | None = None, level: int = 0) -> Self:
        """Create an Item with ItemData at preset tier and level.

        Parameters
        ----------
        data: ItemData to create Item with.
        tier: if not None, the tier to create the Item at. Defaults to the lowest tier.
        level: the level to create the Item at. If -1, will set to maximum for given tier.\
            If `tier` is None, will also set the tier to the maximum reachable.
        """
        MAGIC = -1

        if tier is not None:
            for stage in data.iter_stages():
                if stage.tier is tier:
                    break

            else:
                raise TierUnreachableError(tier)

        elif level == MAGIC:
            stage = get_final_stage(data.start_stage)

        else:
            stage = data.start_stage

        max_level = stage.max_level

        if level == MAGIC:
            level = max_level

        elif not 0 <= level <= max_level:
            raise OutOfRangeError(MAGIC, level, max_level)

        return cls(data=data, stage=stage, level=level)


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
        """Returns True if item has enough power and isn't at max tier."""
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
        """Transforms the item to higher tier, if it has enough power"""
        if not self.is_max_power:
            msg = "Cannot transform a non-maxed item"
            raise ValueError(msg)

        self.item.transform()
        self.power = 0
