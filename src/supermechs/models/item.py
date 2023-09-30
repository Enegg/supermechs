import typing as t
import typing_extensions as tex
import uuid
from bisect import bisect_left

from attrs import Factory, define, field, validators

from .. import _internal
from ..enums import Element, Tier, Type
from ..errors import MaxPowerError, MaxTierError
from ..item_stats import StatsMapping, TransformStage, get_final_stage
from ..typedefs import ID, Name

__all__ = (
    "Tags", "TransformRange", "transform_range",
    "ItemData", "Item", "InvItem", "BattleItem"
)


class Tags(t.NamedTuple):
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
    def from_keywords(cls, it: t.Iterable[str], /) -> tex.Self:
        """Create Tags object from an iterable of string attributes."""
        return cls(**dict.fromkeys(it, True))


TransformRange = t.Sequence[Tier]
"""A range of transformation tiers an item can have."""


def transform_range(lower: Tier | int, upper: Tier | int | None = None) -> TransformRange:
    """Construct a transform range from upper and lower bounds.

    Note: unlike `range` object, upper bound is inclusive.
    """
    lower = int(lower)
    upper = lower if upper is None else int(upper)

    if lower > upper:
        raise ValueError("Minimum tier greater than maximum tier")

    return tuple(map(Tier.of_value, range(lower, upper + 1)))


@define(kw_only=True)
class ItemData:
    """Dataclass storing item data independent of its tier and level."""
    id: ID = field(validator=validators.ge(1))
    """The ID of the item, unique within its pack."""
    pack_key: str = field()
    """The key of the pack this item comes from."""
    name: Name = field(validator=validators.min_len(1))
    """The display name of the item."""
    type: Type = field(validator=validators.in_(Type), repr=str)
    """Member of Type enum denoting the function of the item."""
    element: Element = field(validator=validators.in_(Element), repr=str)
    """Member of Element enum denoting the element of the item."""
    transform_range: TransformRange = field(validator=validators.min_len(1))
    """Range of transformation tiers the item can have."""
    tags: Tags = field()
    """A set of boolean tags which alter item's behavior/appearance."""
    start_stage: TransformStage = field()
    """The first transformation stage of this item."""


Paint: t.TypeAlias = str
"""The name of the paint, or a #-prefixed hex string as a color."""


@define(kw_only=True)
class Item:
    """Represents unique properties of an item."""

    data: ItemData = field()
    stage: TransformStage = field()
    level: int = field(default=0)
    paint: Paint | None = field(default=None)

    @property
    def current_stats(self) -> StatsMapping:
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
        cls, data: ItemData, stage: TransformStage | None = None, /, *, maxed: bool = False
    ) -> tex.Self:
        if stage is None:
            stage = data.start_stage

        if maxed:
            stage = get_final_stage(stage)

        level = stage.max_level if maxed else 0
        return cls(data=data, stage=stage, level=level)


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
    def from_item(cls, item: Item, /) -> tex.Self:
        return cls(item=item)


# XXX: should the multipliers be applied on BattleItem creation, or should it hold a reference?
# BattleItem should be constructible without an InvItem; it has nothing to do with inventory

@define
class BattleItem:
    """Represents the state of an item during a battle."""
    item: Item
    stats: StatsMapping
    multipliers: t.Mapping[str, float] = field(factory=dict)
    # already_used: bool? XXX prolly better to store elsewhere

    @classmethod
    def from_item(cls, item: Item, /) -> tex.Self:
        return cls(item=item, stats=item.current_stats)
