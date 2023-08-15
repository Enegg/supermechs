from __future__ import annotations

import typing as t
from collections import Counter
from functools import partial
from types import MappingProxyType

from attrs import Attribute, define, field, fields
from typing_extensions import Self

from .. import constants
from ..converters import parse_slot_name, slot_to_type
from ..enums import Element, Type
from ..utils import cached_slot_property, format_count, has_any_of_keys
from .inv_item import InvItem

if t.TYPE_CHECKING:
    from uuid import UUID

    from ..typeshed import XOrTupleXY
    from .item import Item

__all__ = ("Mech", "SlotType")

BODY_SLOTS = ("torso", "legs", "drone")
WEAPON_SLOTS = ("side1", "side2", "side3", "side4", "top1", "top2")
SPECIAL_SLOTS = ("tele", "charge", "hook")
MODULE_SLOTS = ("mod1", "mod2", "mod3", "mod4", "mod5", "mod6", "mod7", "mod8")

SlotType = InvItem | None


# ------------------------------------------ Constraints -------------------------------------------


def jumping_required(mech: Mech) -> bool:
    # unequipping legs is allowed, so no legs tests positive
    return mech.legs is None or "jumping" in mech.legs.item.current_stats


def no_duplicate_stats(mech: Mech, module: Item) -> bool:
    present_exclusive_stat_keys = module.current_stats.keys() & constants.EXCLUSIVE_STAT_KEYS

    for equipped_module in mech.iter_items(modules=True):
        if equipped_module is None or equipped_module.item is module:
            continue

        if not equipped_module.item.current_stats.keys().isdisjoint(present_exclusive_stat_keys):
            return False

    return True


def get_constraints_of_item(item: Item, /) -> t.Callable[[Mech], bool] | None:
    if (
        item.data.type is Type.MODULE
        and has_any_of_keys(item.current_stats, *constants.EXCLUSIVE_STAT_KEYS)
        ):
        return partial(no_duplicate_stats, module=item)

    if item.data.tags.require_jump:
        return jumping_required

    return None


# ------------------------------------------- Validators -------------------------------------------


def assert_not_custom(mech: Mech) -> bool:
    for inv_item in filter(None, mech.iter_items()):
        if inv_item.item.data.tags.custom:
            return False

    return True


def validate(mech: Mech, /) -> bool:
    """Check if the mech is battle ready."""
    return (
        # torso present
        mech.torso is not None
        # legs present
        and mech.legs is not None
        # at least one weapon
        and any(weapon is not None for weapon in mech.iter_items(weapons=True))
        # not overweight
        and mech.weight <= constants.OVERLOADED_MAX_WEIGHT
        # no constraints are broken
        and all(constr(mech) for constr in mech.constraints.values())
    )


@define(kw_only=True)
class Mech:
    """Represents a mech build."""

    name: str = field()
    custom: bool = False
    constraints: t.MutableMapping[UUID, t.Callable[[Self], bool]] = field(init=False, factory=dict)

    _stats: t.MutableMapping[str, int] = field(init=False, repr=False, eq=False)
    _dominant_element: Element | None = field(init=False, repr=False, eq=False)

    # fmt: off
    torso:      SlotType = field(init=False, default=None)
    legs:       SlotType = field(init=False, default=None)
    drone:      SlotType = field(init=False, default=None)
    teleporter: SlotType = field(init=False, default=None)
    charge:     SlotType = field(init=False, default=None)
    hook:       SlotType = field(init=False, default=None)
    _side_weapons: list[SlotType] = field(init=False, factory=lambda: [None] * 4)
    _top_weapons: list[SlotType] = field(init=False, factory=lambda: [None] * 2)
    _modules: list[SlotType] = field(init=False, factory=lambda: [None] * 8)
    # fmt: on

    @property
    def side_weapons(self) -> t.Sequence[SlotType]:
        return tuple(self._side_weapons)

    @property
    def top_weapons(self) -> t.Sequence[SlotType]:
        return tuple(self._top_weapons)

    @property
    def modules(self) -> t.Sequence[SlotType]:
        return tuple(self._modules)

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
            for inv_item in self.iter_items(body=True, weapons=True, specials=True)
            if inv_item is not None
            if inv_item.item.data.type not in excluded
        ).most_common(2)
        # return None when there are no elements
        # or the difference between the two most common is indecisive
        if len(elements) == 0 or (len(elements) > 1 and elements[0][1] - elements[1][1] < 2):
            return None

        # otherwise just return the most common one
        return elements[0][0]

    def __setitem__(self, slot: XOrTupleXY[str | Type, int], inv_item: SlotType, /) -> None:
        if not isinstance(inv_item, (InvItem, type(None))):
            raise TypeError(f"Expected Item object or None, got {type(inv_item)}")

        slot = parse_slot_name(slot)
        prev: SlotType = getattr(self, slot)

        if inv_item is not None:
            if slot_to_type(slot) is not inv_item.item.data.type:
                raise TypeError(f"Item type {inv_item.item.data.type} does not match slot {slot!r}")

            if inv_item.item.data.tags.custom and not self.custom:
                raise TypeError("Cannot set a custom item on this mech")

            if prev is not None and prev.UUID in self.constraints:
                del self.constraints[prev.UUID]

            if (constraint := get_constraints_of_item(inv_item.item)) is not None:
                self.constraints[inv_item.UUID] = constraint

        del self.stat_summary

        self._evict_expired_cache(inv_item, prev)
        setattr(self, slot, inv_item)

    def __str__(self) -> str:
        string_parts = [
            f"{inv_item.item.data.type.name.capitalize()}: {inv_item}"
            for inv_item in self.iter_items(body=True)
            if inv_item is not None
        ]

        if weapon_string := ", ".join(format_count(self.iter_items(weapons=True))):
            string_parts.append("Weapons: " + weapon_string)

        string_parts.extend(
            f"{inv_item.item.data.type.name.capitalize()}: {inv_item}"
            for inv_item in self.iter_items(specials=True)
            if inv_item is not None
        )

        if modules := ", ".join(format_count(self.iter_items(modules=True))):
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
        *,
        body: bool = ...,
        weapons: bool = ...,
        specials: bool = ...,
        modules: bool = ...,
        slots: t.Literal[False] = False,
    ) -> t.Iterator[SlotType]:
        ...

    @t.overload
    def iter_items(
        self,
        *,
        body: bool = ...,
        weapons: bool = ...,
        specials: bool = ...,
        modules: bool = ...,
        slots: t.Literal[True],
    ) -> t.Iterator[tuple[SlotType, str]]:
        ...

    def iter_items(
        self,
        *,
        body: bool = False,
        weapons: bool = False,
        specials: bool = False,
        modules: bool = False,
        slots: bool = False,
    ) -> t.Iterator[XOrTupleXY[SlotType, str]]:
        """Iterator over mech's selected items.

        Parameters
        ----------
        body, weapons, specials, modules: `bool`
            Selectors denoting which groups of parts to yield.
            If none are set to `True`, yields from all groups.
            - `body` yields torso, legs and drone;
            - `weapons` yields side & top weapons;
            - `specials` yields teleport, charge and hook;
            - `modules` yields modules.

        slots: `bool`
            If `True`, yields all selected items as tuple pairs of (`InvItem`, `str`).
            If `False`, yields only the items.

        Yields
        ------
        `InvItem | None`
            If `slots` is set to `False`.
        `tuple[InvItem | None, str]`
            If `slots` is set to `True`.
        """
        selectors = (body, weapons, specials, modules)

        from itertools import compress, groupby

        factory: t.Callable[[str], XOrTupleXY[SlotType, str]]

        if slots:
            factory = lambda slot: (getattr(self, slot), slot)  # noqa: E731

        else:
            factory = partial(getattr, self)

        all_fields: tuple[Attribute[t.Any], ...] = fields(type(self))
        iterator = groupby(
            all_fields, key=lambda attr: attr.metadata.get("group", "")
        )
        next(iterator)  # discard no group fields

        if any(selectors):
            # in the negative case we treat all selectors as True
            iterator = compress(iterator, selectors)

        for _, slot_group in iterator:
            for slot in slot_group:
                yield factory(slot.name)
