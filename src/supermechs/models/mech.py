from __future__ import annotations

import typing as t
from collections import Counter
from functools import partial
from types import MappingProxyType

from attrs import define, field

from supermechs import constants
from supermechs.enums import Element, PartialEnum, Type
from supermechs.models.item import Item
from supermechs.typeshed import XOrTupleXY
from supermechs.utils import cached_slot_property, has_any_of

__all__ = ("Mech", "SlotType")

# ------------------------------------------ Constraints -------------------------------------------


def jumping_required(mech: Mech) -> bool:
    # unequipping legs is allowed, so no legs tests positive
    return mech.legs is None or "jumping" in mech.legs.current_stats


def no_duplicate_stats(mech: Mech, module: Item) -> bool:
    present_exclusive_stat_keys = module.current_stats.keys() & constants.EXCLUSIVE_STAT_KEYS

    for equipped_module in mech.iter_items(Type.MODULE):
        if equipped_module is None or equipped_module is module:
            continue

        if has_any_of(equipped_module.current_stats, present_exclusive_stat_keys):
            return False

    return True


def get_constraints_of_item(item: Item, /) -> t.Callable[[Mech], bool] | None:
    if item.data.type is Type.MODULE and has_any_of(
        item.current_stats, *constants.EXCLUSIVE_STAT_KEYS
    ):
        return partial(no_duplicate_stats, module=item)

    if item.data.tags.require_jump:
        return jumping_required

    return None


# ------------------------------------------- Validators -------------------------------------------


def assert_not_custom(mech: Mech, /) -> bool:
    return all(not inv_item.data.tags.custom for inv_item in filter(None, mech.iter_items()))


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
        # and all(constr(mech) for constr in mech._constraints.values())
    )


def _format_count(it: t.Iterable[t.Any], /) -> t.Iterator[str]:
    from collections import Counter
    return (
        f'{item}{f" x{count}" * (count > 1)}' for item, count in Counter(filter(None, it)).items()
    )


def _flatten_slots(args: t.Iterable[SlotSelectorType], /) -> t.Iterator[Mech.Slot]:
    for arg in args:
        if isinstance(arg, Mech.Slot):
            yield arg

        elif isinstance(arg, Type):
            yield from _type_to_slots.get(arg) or (Mech.Slot.of_name(arg.name), )

        elif arg == "body":
            yield from (Mech.Slot.TORSO, Mech.Slot.LEGS, Mech.Slot.DRONE)

        elif arg == "specials":
            yield from (Mech.Slot.TELEPORTER, Mech.Slot.CHARGE, Mech.Slot.HOOK)

        elif arg == "weapons":
            yield from _type_to_slots[Type.SIDE_WEAPON]
            yield from _type_to_slots[Type.TOP_WEAPON]

        else:
            raise TypeError(f"Unknown selector type: {arg!r}")


@define(kw_only=True)
class Mech:
    """Represents a mech build."""

    class _SlotData(t.NamedTuple):
        type: Type

    class Slot(_SlotData, PartialEnum):
        """Enumeration of mech slots."""
        TORSO = (Type.TORSO, )
        LEGS = (Type.LEGS, )
        DRONE = (Type.DRONE, )
        TELEPORTER = (Type.TELEPORTER, )
        CHARGE = (Type.CHARGE, )
        HOOK = (Type.HOOK, )
        SHIELD = (Type.SHIELD, )
        SIDE_WEAPON_1 = (Type.SIDE_WEAPON, )
        SIDE_WEAPON_2 = (Type.SIDE_WEAPON, )
        SIDE_WEAPON_3 = (Type.SIDE_WEAPON, )
        SIDE_WEAPON_4 = (Type.SIDE_WEAPON, )
        TOP_WEAPON_1 = (Type.TOP_WEAPON, )
        TOP_WEAPON_2 = (Type.TOP_WEAPON, )
        MODULE_1 = (Type.MODULE, )
        MODULE_2 = (Type.MODULE, )
        MODULE_3 = (Type.MODULE, )
        MODULE_4 = (Type.MODULE, )
        MODULE_5 = (Type.MODULE, )
        MODULE_6 = (Type.MODULE, )
        MODULE_7 = (Type.MODULE, )
        MODULE_8 = (Type.MODULE, )
        PERK = (Type.PERK, )

    name: str = field()
    custom: t.Final[bool] = False
    _items: t.Final[t.MutableMapping[Slot, Item]] = field(factory=dict)

    # cached properties
    _stat_summary: t.MutableMapping[str, int] = field(init=False, repr=False, eq=False)
    _dominant_element: Element | None = field(init=False, repr=False, eq=False)

    @property
    def torso(self) -> SlotType:
        return self._items.get(self.Slot.TORSO)

    @property
    def legs(self) -> SlotType:
        return self._items.get(self.Slot.LEGS)

    @property
    def drone(self) -> SlotType:
        return self._items.get(self.Slot.DRONE)

    @property
    def teleporter(self) -> SlotType:
        return self._items.get(self.Slot.TELEPORTER)

    @property
    def charge(self) -> SlotType:
        return self._items.get(self.Slot.CHARGE)

    @property
    def hook(self) -> SlotType:
        return self._items.get(self.Slot.HOOK)

    @property
    def side_weapons(self) -> t.Sequence[SlotType]:
        return [self._items[slot] for slot in _type_to_slots[Type.SIDE_WEAPON]]

    @property
    def top_weapons(self) -> t.Sequence[SlotType]:
        return [
            self._items.get(self.Slot.TOP_WEAPON_1),
            self._items.get(self.Slot.TOP_WEAPON_2),
        ]

    @property
    def modules(self) -> t.Sequence[SlotType]:
        return [self._items[slot] for slot in _type_to_slots[Type.MODULE]]

    @property
    def weight(self) -> int:
        """The weight of the mech."""
        return self.stat_summary.get("weight", 0)

    @cached_slot_property
    def stat_summary(self) -> t.Mapping[str, int]:
        """A dict of the mech's stats, in order as they appear in workshop."""

        # inherit the key order from summary
        stats = dict.fromkeys(constants.SUMMARY_STAT_KEYS, 0)

        for item in filter(None, self.iter_items()):
            for stat in constants.SUMMARY_STAT_KEYS:
                if (value := item.current_stats.get(stat)) is not None:
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
            item.data.element
            for item in self.iter_items("body", "weapons", "specials")
            if item is not None
            if item.data.type not in excluded
        ).most_common(2)
        # return None when there are no elements
        # or the difference between the two most common is indecisive
        if len(elements) == 0 or (len(elements) > 1 and elements[0][1] - elements[1][1] < 2):
            return None

        # otherwise just return the most common one
        return elements[0][0]

    def __setitem__(self, slot: Slot, item: SlotType, /) -> None:
        if not isinstance(item, SlotType):
            raise TypeError(f"Expected {SlotType}, got {type(item).__name__}")

        if item is not None:
            data = item.data
            if data.type is not slot.type:
                raise TypeError(f"Item type {data.type} does not match slot {slot.type}")

            if data.tags.custom and not self.custom:
                raise TypeError("Cannot set a custom item on this mech")

        self._evict_expired_cache(item, self._items.get(slot))

        if item is None:
            del self._items[slot]

        else:
            self._items[slot] = item

    def __getitem__(self, slot: Slot, /) -> SlotType:
        return self._items.get(slot)

    def __str__(self) -> str:
        string_parts = [
            f"{item.data.type.name.capitalize()}: {item}"
            for item in self.iter_items("body")
            if item is not None
        ]

        if weapon_string := ", ".join(_format_count(self.iter_items("weapons"))):
            string_parts.append("Weapons: " + weapon_string)

        string_parts.extend(
            f"{item.data.type.name.capitalize()}: {item}"
            for item in self.iter_items("specials")
            if item is not None
        )

        if modules := ", ".join(_format_count(self.iter_items(Type.MODULE))):
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
        del self.stat_summary

        if new is None or old is None or new.data.element is not old.data.element:
            del self.dominant_element

    @t.overload
    def iter_items(
        self,
        *slots: SlotSelectorType,
        yield_slots: t.Literal[False] = False,
    ) -> t.Iterator[SlotType]:
        ...

    @t.overload
    def iter_items(
        self,
        *slots: SlotSelectorType,
        yield_slots: t.Literal[True],
    ) -> t.Iterator[tuple[SlotType, Slot]]:
        ...

    def iter_items(
        self,
        *slots: SlotSelectorType,
        yield_slots: bool = False,
    ) -> t.Iterator[XOrTupleXY[SlotType, Slot]]:
        """Iterator over mech's selected items.

        Parameters
        ----------
        slots: the order and types of items to yield. "body" is a shorthand for TORSO, LEGS & DRONE\
        ; "weapons" for SIDE_WEAPON and TOP_WEAPON; "specials" for TELEPORTER, CHARGE & HOOK.\
        If no types are specified, yields every item.

        yield_slots: If `True`, yields tuples of both the item and its slot.\
            Otherwise, yields just the items.

        Yields
        ------
        `Item | None`
            If `slots` is set to `False`.
        `tuple[Item | None, Slot]`
            If `slots` is set to `True`.
        """
        if yield_slots:

            def factory(item: SlotType, slot: Mech.Slot, /) -> XOrTupleXY[SlotType, Mech.Slot]:
                return item, slot

        else:

            def factory(item: SlotType, slot: Mech.Slot, /) -> XOrTupleXY[SlotType, Mech.Slot]:
                del slot
                return item

        slots_ = self.Slot if not slots else _flatten_slots(slots)

        for slot in slots_:
            yield factory(self._items.get(slot), slot)


SlotType = Item | None
SlotSelectorType = Mech.Slot | Type | t.Literal["body", "weapons", "specials"]

_type_to_slots: t.Mapping[Type, t.Sequence[Mech.Slot]] = {
    Type.SIDE_WEAPON: tuple(Mech.Slot.of_name(f"SIDE_WEAPON_{n}") for n in range(1, 4)),
    Type.TOP_WEAPON: (Mech.Slot.TOP_WEAPON_1, Mech.Slot.TOP_WEAPON_2),
    Type.MODULE: tuple(Mech.Slot.of_name(f"MODULE_{n}") for n in range(1, 9))
}
