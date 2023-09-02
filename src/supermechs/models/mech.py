from __future__ import annotations

import typing as t
from collections import Counter
from functools import partial
from types import MappingProxyType
from typing_extensions import Self

from attrs import define, field

from .. import constants
from ..enums import Element, Type
from ..typeshed import XOrTupleXY
from ..utils import cached_slot_property, format_count, has_any_of_keys
from .item import InvItem, Item

if t.TYPE_CHECKING:
    from uuid import UUID

__all__ = ("Mech", "SlotType", "SlotSelectorType")

SlotType = InvItem | None
SlotSelectorType = XOrTupleXY[Type, int]

# ------------------------------------------ Constraints -------------------------------------------


def jumping_required(mech: Mech) -> bool:
    # unequipping legs is allowed, so no legs tests positive
    return mech.legs is None or "jumping" in mech.legs.item.current_stats


def no_duplicate_stats(mech: Mech, module: Item) -> bool:
    present_exclusive_stat_keys = module.current_stats.keys() & constants.EXCLUSIVE_STAT_KEYS

    for equipped_module in mech.iter_items(Type.MODULE):
        if equipped_module is None or equipped_module.item is module:
            continue

        if not equipped_module.item.current_stats.keys().isdisjoint(present_exclusive_stat_keys):
            return False

    return True


def get_constraints_of_item(item: Item, /) -> t.Callable[[Mech], bool] | None:
    if item.data.type is Type.MODULE and has_any_of_keys(
        item.current_stats, *constants.EXCLUSIVE_STAT_KEYS
    ):
        return partial(no_duplicate_stats, module=item)

    if item.data.tags.require_jump:
        return jumping_required

    return None


# ------------------------------------------- Validators -------------------------------------------


def assert_not_custom(mech: Mech, /) -> bool:
    return all(not inv_item.item.data.tags.custom for inv_item in filter(None, mech.iter_items()))


def validate(mech: Mech, /) -> bool:
    """Check if the mech is battle ready."""
    return (
        # torso present
        mech.torso is not None
        # legs present
        and mech.legs is not None
        # at least one weapon
        and any(weapon is not None for weapon in mech.iter_items("weapons"))
        # not overweight
        and mech.weight <= constants.OVERLOADED_MAX_WEIGHT
        # no constraints are broken
        and all(constr(mech) for constr in mech._constraints.values())
    )


def _index_for_slot(slot: SlotSelectorType, /) -> tuple[int, Type]:
    match slot:
        case Type() as type_:
            if abs_index := Mech._indexes.get(type_) is None:
                raise ValueError(f"{type_} requires an index")

        case (Type() as type_, int() as index):
            slice_ = Mech._slices.get(type_)

            if slice_ is None:
                raise ValueError(f"{type_} is not indexable")

            if index not in range(slice_.stop - slice_.start):
                raise IndexError(f"Item index {index} out of range")

            abs_index = index + int(slice_.start)

        case other:  # pyright: ignore[reportUnnecessaryComparison]
            raise TypeError(f"Invalid slot: {other}")

    return abs_index, type_


_type_groups: t.Mapping[str, t.Sequence[Type]] = {
    "body": (Type.TORSO, Type.LEGS, Type.DRONE),
    "weapons": (Type.SIDE_WEAPON, Type.TOP_WEAPON),
    "specials": (Type.TELEPORTER, Type.CHARGE, Type.HOOK),
}


def _flatten_types(args: t.Iterable[Type | str], /) -> t.Iterator[Type]:
    for arg in args:
        if isinstance(arg, Type):
            yield arg

        else:
            yield from _type_groups[arg]


@define(kw_only=True)
class Mech:
    """Represents a mech build."""

    name: str = field()
    custom: t.Final[bool] = False
    _items: t.Final[t.MutableSequence[SlotType]] = field(factory=lambda: [None] * 20)
    _constraints: t.Final[t.MutableMapping[UUID, t.Callable[[Self], bool]]] = field(
        init=False, factory=dict
    )

    # cached properties
    _stats: t.MutableMapping[str, int] = field(init=False, repr=False, eq=False)
    _dominant_element: Element | None = field(init=False, repr=False, eq=False)

    _indexes: t.ClassVar[t.Mapping[Type, int]] = {
        Type.TORSO: 0,
        Type.LEGS: 1,
        Type.DRONE: 2,
        Type.TELEPORTER: 3,
        Type.CHARGE: 4,
        Type.HOOK: 5,
    }
    _slices: t.ClassVar[t.Mapping[Type, slice]] = {
        Type.SIDE_WEAPON: slice(6, 10),
        Type.TOP_WEAPON: slice(10, 12),
        Type.MODULE: slice(12, 20),
    }

    @property
    def torso(self) -> SlotType:
        return self._items[self._indexes[Type.TORSO]]

    @property
    def legs(self) -> SlotType:
        return self._items[self._indexes[Type.LEGS]]

    @property
    def drone(self) -> SlotType:
        return self._items[self._indexes[Type.DRONE]]

    @property
    def teleporter(self) -> SlotType:
        return self._items[self._indexes[Type.TELEPORTER]]

    @property
    def charge(self) -> SlotType:
        return self._items[self._indexes[Type.CHARGE]]

    @property
    def hook(self) -> SlotType:
        return self._items[self._indexes[Type.HOOK]]

    @property
    def side_weapons(self) -> t.Sequence[SlotType]:
        return self._items[self._slices[Type.SIDE_WEAPON]]

    @property
    def top_weapons(self) -> t.Sequence[SlotType]:
        return self._items[self._slices[Type.TOP_WEAPON]]

    @property
    def modules(self) -> t.Sequence[SlotType]:
        return self._items[self._slices[Type.MODULE]]

    @property
    def weight(self) -> int:
        """The weight of the mech."""
        return self.stat_summary.get("weight", 0)

    @cached_slot_property
    def stat_summary(self) -> t.Mapping[str, int]:
        """A dict of the mech's stats, in order as they appear in workshop."""

        # inherit the key order from summary
        stats = dict.fromkeys(constants.SUMMARY_STAT_KEYS, 0)

        for inv_item in filter(None, self.iter_items()):
            for stat in constants.SUMMARY_STAT_KEYS:
                if (value := inv_item.item.current_stats.get(stat)) is not None:
                    stats[stat] += value

        if (overload := stats["weight"] - constants.MAX_WEIGHT) > 0:
            stats["health"] -= overload * constants.HP_PENALTY_PER_KG

        for stat, value in tuple(stats.items())[2:]:  # keep weight and health
            if value == 0:
                del stats[stat]

        return MappingProxyType(stats)

    @cached_slot_property
    def dominant_element(self) -> Element | None:
        """Guesses the mech type by equipped items."""
        excluded = (Type.CHARGE_ENGINE, Type.TELEPORTER)
        elements = Counter(
            inv_item.item.data.element
            for inv_item in self.iter_items("body", "weapons", "specials")
            if inv_item is not None
            if inv_item.item.data.type not in excluded
        ).most_common(2)
        # return None when there are no elements
        # or the difference between the two most common is indecisive
        if len(elements) == 0 or (len(elements) > 1 and elements[0][1] - elements[1][1] < 2):
            return None

        # otherwise just return the most common one
        return elements[0][0]

    def __setitem__(self, slot: SlotSelectorType, inv_item: SlotType, /) -> None:
        if not isinstance(inv_item, SlotType):
            raise TypeError(f"Expected {SlotType}, got {type(inv_item).__name__}")

        index, target_type = _index_for_slot(slot)

        prev = self._items[index]

        if inv_item is not None:
            data = inv_item.item.data
            if data.type is not target_type:
                raise TypeError(f"Item type {data.type} does not match slot {target_type!r}")

            if data.tags.custom and not self.custom:
                raise TypeError("Cannot set a custom item on this mech")

            if prev is not None and prev.UUID in self._constraints:
                del self._constraints[prev.UUID]

            if (constraint := get_constraints_of_item(inv_item.item)) is not None:
                self._constraints[inv_item.UUID] = constraint

        del self.stat_summary

        self._evict_expired_cache(inv_item, prev)
        self._items[index] = inv_item

    def __getitem__(self, slot: XOrTupleXY[Type, int], /) -> SlotType:
        index, _ = _index_for_slot(slot)
        return self._items[index]

    def __str__(self) -> str:
        string_parts = [
            f"{inv_item.item.data.type.name.capitalize()}: {inv_item}"
            for inv_item in self.iter_items("body")
            if inv_item is not None
        ]

        if weapon_string := ", ".join(format_count(self.iter_items("weapons"))):
            string_parts.append("Weapons: " + weapon_string)

        string_parts.extend(
            f"{inv_item.item.data.type.name.capitalize()}: {inv_item}"
            for inv_item in self.iter_items("specials")
            if inv_item is not None
        )

        if modules := ", ".join(format_count(self.iter_items(Type.MODULE))):
            string_parts.append("Modules: " + modules)

        return "\n".join(string_parts)

    def _evict_expired_cache(self, new: SlotType, old: SlotType) -> None:
        """Deletes cached attributes if they expire."""
        # # Setting a displayable item will not change the image
        # # only if the old item was the same item
        # # For simplicity I don't exclude that case from updating the image
        # if new is not None and new.type.displayable:
        #     del self.image

        # # the item was set to None, thus the appearance will change
        # # only if the previous one was displayable
        # elif old is not None and old.type.displayable:
        #     del self.image

        if new is None or old is None or new.item.data.element is not old.item.data.element:
            del self.dominant_element

    @t.overload
    def iter_items(
        self,
        *types: Type | t.Literal["body", "weapons", "specials"],
        slots: t.Literal[False] = False,
    ) -> t.Iterator[SlotType]:
        ...

    @t.overload
    def iter_items(
        self,
        *types: Type | t.Literal["body", "weapons", "specials"],
        slots: t.Literal[True],
    ) -> t.Iterator[tuple[SlotType, Type]]:
        ...

    def iter_items(
        self,
        *types: Type | t.Literal["body", "weapons", "specials"],
        slots: bool = False,
    ) -> t.Iterator[XOrTupleXY[SlotType, Type]]:
        """Iterator over mech's selected items.

        Parameters
        ----------
        types: the order and types of items to yield. "body" is a shorthand for TORSO, LEGS & DRONE\
        ; "weapons" for SIDE_WEAPON and TOP_WEAPON; "specials" for TELEPORTER, CHARGE & HOOK.\
        If no types are specified, yields every item.

        slots: If `True`, yields tuples of both the item and its slot's type.\
            Otherwise, yields just the items.

        Yields
        ------
        `InvItem | None`
            If `slots` is set to `False`.
        `tuple[InvItem | None, Type]`
            If `slots` is set to `True`.
        """

        from itertools import chain, repeat

        if slots:

            def factory(item: SlotType, type: Type, /) -> XOrTupleXY[SlotType, Type]:
                return item, type

        else:

            def factory(item: SlotType, type: Type, /) -> XOrTupleXY[SlotType, Type]:
                del type
                return item

        types_ = chain(self._indexes, self._slices) if not types else _flatten_types(types)

        for type in types_:
            if (index := self._indexes.get(type)) is not None:
                yield factory(self._items[index], type)

            else:
                slice_ = self._slices[type]
                yield from map(factory, self._items[slice_], repeat(type))
