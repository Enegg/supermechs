from collections import abc
from enum import auto, unique
from typing import Any, Final, Literal, TypeAlias, overload

from attrs import define, field

from .item import Element, Item, Type
from .typeshed import XOrTupleXY
from .utils import KeyAccessor, PartialEnum

__all__ = ("Mech", "SlotType", "dominant_element")

SlotType: TypeAlias = Item | None
SlotAccessor: TypeAlias = KeyAccessor["Mech.Slot", SlotType]


def _format_count(it: abc.Iterable[Any], /) -> abc.Iterator[str]:
    from collections import Counter

    return (
        f"{item} x{count}" if count > 1 else str(item)
        for item, count in Counter(filter(None, it)).items()
    )


@define(kw_only=True)
class Mech:
    """Represents a mech build."""

    @unique
    class Slot(PartialEnum):
        """Enumeration of mech item slots."""

        TORSO = auto()
        LEGS = auto()
        DRONE = auto()
        TELEPORTER = auto()
        CHARGE = auto()
        HOOK = auto()
        SHIELD = auto()
        SIDE_WEAPON_1 = auto()
        SIDE_WEAPON_2 = auto()
        SIDE_WEAPON_3 = auto()
        SIDE_WEAPON_4 = auto()
        TOP_WEAPON_1 = auto()
        TOP_WEAPON_2 = auto()
        MODULE_1 = auto()
        MODULE_2 = auto()
        MODULE_3 = auto()
        MODULE_4 = auto()
        MODULE_5 = auto()
        MODULE_6 = auto()
        MODULE_7 = auto()
        MODULE_8 = auto()
        PERK = auto()

    name: str = field()
    _setup: Final[abc.MutableMapping[Slot, Item]] = field(factory=dict)

    torso = SlotAccessor(Slot.TORSO)
    legs = SlotAccessor(Slot.LEGS)
    drone = SlotAccessor(Slot.DRONE)
    teleporter = SlotAccessor(Slot.TELEPORTER)
    charge = SlotAccessor(Slot.CHARGE)
    hook = SlotAccessor(Slot.HOOK)
    shield = SlotAccessor(Slot.SHIELD)
    perk = SlotAccessor(Slot.PERK)

    @property
    def side_weapons(self) -> list[SlotType]:
        return [self._setup.get(slot) for slot in _type_to_slots[Type.SIDE_WEAPON]]

    @property
    def top_weapons(self) -> list[SlotType]:
        return [
            self._setup.get(self.Slot.TOP_WEAPON_1),
            self._setup.get(self.Slot.TOP_WEAPON_2),
        ]

    @property
    def modules(self) -> list[SlotType]:
        return [self._setup[slot] for slot in _type_to_slots[Type.MODULE]]

    def __setitem__(self, slot: Slot, item: SlotType, /) -> None:
        if not isinstance(item, SlotType):
            msg = f"Expected {SlotType}, got {type(item).__name__}"
            raise TypeError(msg)

        if item is None:
            del self[slot]

        else:
            self._setup[slot] = item

    def __getitem__(self, slot: Slot, /) -> SlotType:
        return self._setup.get(slot)

    def __delitem__(self, slot: Slot, /) -> None:
        self._setup.pop(slot, None)

    def __str__(self) -> str:
        string_parts = [
            f"{slot.name.capitalize()}: {item}"
            for item, slot in self.iter_items("body", yield_slots=True)
        ]

        if weapon_string := ", ".join(_format_count(self.iter_items("weapons"))):
            string_parts.append("Weapons: " + weapon_string)

        string_parts.extend(
            f"{item.type.name.capitalize()}: {item}"
            for item in self.iter_items("specials")
            if item is not None
        )

        if modules := ", ".join(_format_count(self.iter_items(Type.MODULE))):
            string_parts.append("Modules: " + modules)

        if perk := self.perk:
            string_parts.append(f"Perk: {perk}")

        return "\n".join(string_parts)

    @overload
    def iter_items(
        self,
        *slots: "SlotSelectorType",
        yield_slots: Literal[False] = False,
    ) -> abc.Iterator[SlotType]:
        ...

    @overload
    def iter_items(
        self,
        *slots: "SlotSelectorType",
        yield_slots: Literal[True],
    ) -> abc.Iterator[tuple[SlotType, Slot]]:
        ...

    def iter_items(
        self,
        *slots: "SlotSelectorType",
        yield_slots: bool = False,
    ) -> abc.Iterator[XOrTupleXY[SlotType, Slot]]:
        """Iterator over selected mech's items.

        Parameters
        ----------
        slots: the order and `Slot`s from which to yield.\
         There are a few literal string shorthands for related types:\
         "body" - TORSO & LEGS;\
         "weapons" - SIDE_WEAPON, TOP_WEAPON & DRONE;\
         "specials" - TELEPORTER, CHARGE, HOOK & SHIELD.\
         If no types are provided, yields every item.

        yield_slots: If `True`, yields tuples of both the item and its slot.\
         Otherwise, yields just the items.
        """
        slots_ = self.Slot if not slots else _selectors_to_slots(slots)

        if yield_slots:
            for slot in slots_:
                yield self._setup.get(slot), slot

        else:
            yield from map(self._setup.get, slots_)


SlotSelectorType: TypeAlias = Mech.Slot | Type | Literal["body", "weapons", "specials"]

_slots_of_type: abc.Mapping[Type, abc.Sequence[Mech.Slot]] = {
    Type.SIDE_WEAPON: tuple(Mech.Slot.of_name(f"SIDE_WEAPON_{n}") for n in range(1, 4)),
    Type.TOP_WEAPON: (Mech.Slot.TOP_WEAPON_1, Mech.Slot.TOP_WEAPON_2),
    Type.MODULE: tuple(Mech.Slot.of_name(f"MODULE_{n}") for n in range(1, 9)),
}


def _selectors_to_slots(args: abc.Iterable[SlotSelectorType], /) -> abc.Iterator[Mech.Slot]:
    for arg in args:
        if isinstance(arg, Mech.Slot):
            yield arg

        elif isinstance(arg, Type):
            yield from _slots_of_type.get(arg) or (Mech.Slot.of_name(arg.name),)

        elif arg == "body":
            yield from (Mech.Slot.TORSO, Mech.Slot.LEGS)

        elif arg == "specials":
            yield from (Mech.Slot.TELEPORTER, Mech.Slot.CHARGE, Mech.Slot.HOOK, Mech.Slot.SHIELD)

        elif arg == "weapons":
            yield from _slots_of_type[Type.SIDE_WEAPON]
            yield from _slots_of_type[Type.TOP_WEAPON]
            yield Mech.Slot.DRONE

        else:
            msg = f"Unknown selector type: {arg!r}"
            raise TypeError(msg)


def dominant_element(mech: Mech, /, threshold: int = 2) -> Element | None:
    """Guesses the mech type by equipped items.

    threshold: the difference in item count required for either of the two most common elements\
     to be considered over the other.
    """
    from collections import Counter

    elements = Counter(
        item.element
        for item in mech.iter_items("body", "weapons", Mech.Slot.HOOK)
        if item is not None
    ).most_common(2)
    # return None when there are no elements
    # or the difference between the two most common is indecisive
    if len(elements) == 0 or (len(elements) > 1 and elements[0][1] - elements[1][1] < threshold):
        return None

    # otherwise just return the most common one
    return elements[0][0]
