from __future__ import annotations

import typing as t
from collections import Counter
from functools import partial
from types import MappingProxyType

from attrs import Attribute, define, field, fields
from attrs.validators import max_len
from typing_extensions import Self

from .. import constants
from ..constants import WORKSHOP_STATS
from ..converters import get_slot_name, slot_to_type
from ..enums import Element, Type
from ..user_input import StringLimits
from ..utils import cached_slot_property, format_count
from .inv_item import InvItem

if t.TYPE_CHECKING:
    from uuid import UUID

    from ..typeshed import XOrTupleXY

__all__ = ("Mech", "SlotType")

BODY_SLOTS = ("torso", "legs", "drone")
WEAPON_SLOTS = ("side1", "side2", "side3", "side4", "top1", "top2")
SPECIAL_SLOTS = ("tele", "charge", "hook")
MODULE_SLOTS = ("mod1", "mod2", "mod3", "mod4", "mod5", "mod6", "mod7", "mod8")

SlotType = InvItem | None


# ------------------------------------------ Constraints -------------------------------------------


def jumping_required(mech: Mech) -> bool:
    # unequipping legs is allowed, so no legs tests positive
    return mech.legs is None or "jumping" in mech.legs.stats


def no_duplicate_stats(mech: Mech, module: InvItem) -> bool:
    exclusive_stats = module.current_stats.keys() & constants.EXCLUSIVE_STATS

    for equipped_module in mech.iter_items(modules=True):
        if equipped_module is None or equipped_module is module:
            continue

        if equipped_module.stats.has_any_of_stats(*exclusive_stats):
            return False

    return True


def get_constraints_of_item(item: InvItem) -> t.Callable[[Mech], bool] | None:
    if item.type is Type.MODULE and item.stats.has_any_of_stats(*constants.EXCLUSIVE_STATS):
        return partial(no_duplicate_stats, module=item)

    if item.tags.require_jump:
        return jumping_required

    return None


# ------------------------------------------- Validators -------------------------------------------


def _is_valid_type(
    inst: t.Any, attr: Attribute[SlotType | t.Any], value: SlotType | t.Any,
) -> None:
    """Check if item type matches the slot it is assigned to."""
    del inst

    if value is None:
        return

    if not isinstance(value, InvItem):
        raise TypeError(f"Invalid object set as item: {value!r}")

    valid_type = slot_to_type(attr.name)

    if value.type is not valid_type:
        raise ValueError(f"Mech slot {attr.name} expects a type {valid_type}, got {value.type}")


def assert_not_custom(mech: Mech) -> bool:
    for item in filter(None, mech.iter_items()):
        if item.tags.custom:
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
        and any(wep is not None for wep in mech.iter_items(weapons=True))
        # not over max overload
        and mech.weight <= constants.MAX_OVERWEIGHT
        # no constraints are broken
        and all(constr(mech) for constr in mech.constraints.values())
    )


@define(kw_only=True)
class Mech:
    """Represents a mech build."""

    name: str = field(validator=max_len(StringLimits.name))
    custom: bool = False
    constraints: dict[UUID, t.Callable[[Self], bool]] = field(factory=dict, init=False)

    _stats: dict[str, int] = field(init=False, repr=False, eq=False)
    _dominant_element: Element | None = field(init=False, repr=False, eq=False)

    # fmt: off
    torso:  SlotType = field(default=None, validator=_is_valid_type, metadata={"group": "body"})
    legs:   SlotType = field(default=None, validator=_is_valid_type, metadata={"group": "body"})
    drone:  SlotType = field(default=None, validator=_is_valid_type, metadata={"group": "body"})
    side1:  SlotType = field(default=None, validator=_is_valid_type, metadata={"group": "weapon"})
    side2:  SlotType = field(default=None, validator=_is_valid_type, metadata={"group": "weapon"})
    side3:  SlotType = field(default=None, validator=_is_valid_type, metadata={"group": "weapon"})
    side4:  SlotType = field(default=None, validator=_is_valid_type, metadata={"group": "weapon"})
    top1:   SlotType = field(default=None, validator=_is_valid_type, metadata={"group": "weapon"})
    top2:   SlotType = field(default=None, validator=_is_valid_type, metadata={"group": "weapon"})
    tele:   SlotType = field(default=None, validator=_is_valid_type, metadata={"group": "special"})
    charge: SlotType = field(default=None, validator=_is_valid_type, metadata={"group": "special"})
    hook:   SlotType = field(default=None, validator=_is_valid_type, metadata={"group": "special"})
    mod1:   SlotType = field(default=None, validator=_is_valid_type, metadata={"group": "module"})
    mod2:   SlotType = field(default=None, validator=_is_valid_type, metadata={"group": "module"})
    mod3:   SlotType = field(default=None, validator=_is_valid_type, metadata={"group": "module"})
    mod4:   SlotType = field(default=None, validator=_is_valid_type, metadata={"group": "module"})
    mod5:   SlotType = field(default=None, validator=_is_valid_type, metadata={"group": "module"})
    mod6:   SlotType = field(default=None, validator=_is_valid_type, metadata={"group": "module"})
    mod7:   SlotType = field(default=None, validator=_is_valid_type, metadata={"group": "module"})
    mod8:   SlotType = field(default=None, validator=_is_valid_type, metadata={"group": "module"})
    # fmt: on

    @property
    def weight(self) -> int:
        """The weight of the mech."""
        return self.stats.get("weight", 0)

    @cached_slot_property
    def stats(self) -> t.Mapping[str, int]:
        """A dict of the mech's stats, in order as they appear in workshop."""

        # inherit the order of dict keys from workshop stats
        stats = dict.fromkeys(WORKSHOP_STATS, 0)

        for item in filter(None, self.iter_items()):
            for stat in WORKSHOP_STATS:
                if (value := item.current_stats.get(stat)) is not None:
                    stats[stat] += value

        if (overweight := stats["weight"] - constants.MAX_WEIGHT) > 0:
            stats["health"] -= overweight * constants.HEALTH_PENALTY_PER_KG

        for stat, value in tuple(stats.items())[2:]:  # keep weight and health
            if value == 0:
                del stats[stat]

        return MappingProxyType(stats)

    @cached_slot_property
    def dominant_element(self) -> Element | None:
        """Guesses the mech type by equipped items."""
        excluded = {Type.CHARGE_ENGINE, Type.TELEPORTER}
        elements = Counter(
            item.element
            for item in self.iter_items(body=True, weapons=True, specials=True)
            if item is not None
            if item.type not in excluded
        ).most_common(2)
        # the 2 ensures there are at most 2 elements to compare together

        # return None when there are no elements
        # or the difference between the two most common is small
        if len(elements) == 0 or (len(elements) >= 2 and elements[0][1] - elements[1][1] < 2):
            return None

        # otherwise just return the most common one
        return elements[0][0]

    def __setitem__(self, slot: XOrTupleXY[str | Type, int], item: SlotType, /) -> None:
        if not isinstance(item, (InvItem, type(None))):
            raise TypeError(f"Expected Item object or None, got {type(item)}")

        slot = get_slot_name(slot)

        if item is not None:
            if slot_to_type(slot) is not item.type:
                raise TypeError(f"Item type {item.type} does not match slot {slot!r}")

            if item.tags.custom and not self.custom:
                raise TypeError("Cannot set a custom item on this mech")

            if (prev := self[slot]) is not None and prev.UUID in self.constraints:
                del self.constraints[prev.UUID]

            if (constraint := get_constraints_of_item(item)) is not None:
                self.constraints[item.UUID] = constraint

        del self.stats

        self._evict_expired_cache(item, self[slot])
        setattr(self, slot, item)

    def __getitem__(self, slot: XOrTupleXY[str | Type, int]) -> SlotType:
        return getattr(self, get_slot_name(slot))

    def __str__(self) -> str:
        string_parts = [
            f"{item.type.name.capitalize()}: {item}"
            for item in self.iter_items(body=True)
            if item is not None
        ]

        if weapon_string := ", ".join(format_count(self.iter_items(weapons=True))):
            string_parts.append("Weapons: " + weapon_string)

        string_parts.extend(
            f"{item.type.name.capitalize()}: {item}"
            for item in self.iter_items(specials=True)
            if item is not None
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

        if new is None or old is None or new.element is not old.element:
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
        `InvItem`
            If `slots` is set to `False`.
        `tuple[InvItem, str]`
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
