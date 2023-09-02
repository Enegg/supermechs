import typing as t
import typing_extensions as tex

from attrs import define, field, validators

from ..enums import Element, Tier, Type
from ..item_stats import TransformStage
from ..typedefs import ID, Name

__all__ = ("ItemData", "Tags", "TransformRange", "transform_range")


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

    return tuple(map(Tier.get_by_value, range(lower, upper + 1)))


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
