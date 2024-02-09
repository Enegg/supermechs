from collections import abc
from typing import Literal, TypeAlias

from attrs import define, field

from .gamerules import DEFAULT_GAME_RULES, BuildRules, VariadicType
from .item import Element, Item, Type
from .utils import KeyAccessor, SequenceView

__all__ = ("Mech", "SlotMemberType", "dominant_element")

SlotMemberType: TypeAlias = Item | None
SlotType: TypeAlias = Type | tuple[VariadicType, int]
SlotAccessor: TypeAlias = KeyAccessor[Type, SlotMemberType]
SlotSelectorType: TypeAlias = SlotType | Literal["body", "weapons", "specials"]


@define(kw_only=True)
class Mech:
    """Represents a mech build."""

    name: str = field()
    rules: BuildRules = field(default=DEFAULT_GAME_RULES.builds)
    _setup: abc.MutableMapping[SlotType, Item] = field(factory=dict, init=False)
    # fmt: off
    torso      = SlotAccessor(Type.TORSO)
    legs       = SlotAccessor(Type.LEGS)
    drone      = SlotAccessor(Type.DRONE)
    teleporter = SlotAccessor(Type.TELEPORTER)
    charge     = SlotAccessor(Type.CHARGE)
    hook       = SlotAccessor(Type.HOOK)
    shield     = SlotAccessor(Type.SHIELD)
    perk       = SlotAccessor(Type.PERK)
    # fmt: on

    def side_weapons(self):
        """A sequence-like object providing a view on mech's side weapons."""
        return SequenceView(self, Type.SIDE_WEAPON, self.rules.VARIADIC_SLOTS[Type.SIDE_WEAPON])

    def top_weapons(self):
        """A sequence-like object providing a view on mech's top weapons."""
        return SequenceView(self, Type.TOP_WEAPON, self.rules.VARIADIC_SLOTS[Type.TOP_WEAPON])

    def modules(self):
        """A sequence-like object providing a view on mech's modules."""
        return SequenceView(self, Type.MODULE, self.rules.VARIADIC_SLOTS[Type.MODULE])

    def __setitem__(self, slot: SlotType, item: SlotMemberType, /) -> None:
        if not isinstance(item, SlotMemberType):
            msg = f"Expected {SlotMemberType}, got {type(item).__name__}"
            raise TypeError(msg)

        if isinstance(slot, tuple):
            variadic_type, index = slot
            n_slots = self.rules.VARIADIC_SLOTS[variadic_type]
            if index >= n_slots:
                msg = f"Slot index greater than allowed ({index} >= {n_slots}) for {variadic_type}"
                raise IndexError(msg)

        if item is None:
            del self[slot]

        else:
            self._setup[slot] = item

    def __getitem__(self, slot: SlotType, /) -> SlotMemberType:
        return self._setup.get(slot)

    def __delitem__(self, slot: SlotType, /) -> None:
        self._setup.pop(slot, None)

    def __str__(self) -> str:
        string_parts = [
            f"{slot.name.capitalize()}: {item}"
            for item, slot in zip(self.iter_items("body"), (Type.TORSO, Type.LEGS), strict=True)
        ]

        if weapon_string := ", ".join(map(str, self.iter_items("weapons"))):
            string_parts.append("Weapons: " + weapon_string)

        string_parts.extend(
            f"{item.type.name.capitalize()}: {item}"
            for item in self.iter_items("specials")
            if item is not None
        )

        if modules := ", ".join(map(str, self.iter_items(Type.MODULE))):
            string_parts.append("Modules: " + modules)

        if perk := self.perk:
            string_parts.append(f"Perk: {perk}")

        return "\n".join(string_parts)

    def iter_items(self, *slots: "SlotSelectorType") -> abc.Iterator[SlotMemberType]:
        """Iterator over selected mech's items.

        Parameters
        ----------
        slots: the order and `Type`s of items to yield.\
         Literal string shorthands for related types:\
         "body" - `TORSO` & `LEGS`;\
         "weapons" - `SIDE_WEAPON`s, `TOP_WEAPON`s & `DRONE`;\
         "specials" - `TELEPORTER`, `CHARGE`, `HOOK` & `SHIELD`.\
         If no slots are provided, yields every item.
        """
        if slots:
            slots_ = _selectors_to_slots(slots, self.rules)
            yield from map(self._setup.get, slots_)
            return

        variadic = (Type.SIDE_WEAPON, Type.TOP_WEAPON, Type.MODULE)

        for type in Type:
            if type in variadic:
                yield from SequenceView(self, type, self.rules.VARIADIC_SLOTS[type])

            else:
                yield self._setup.get(type)


def _selectors_to_slots(
    args: abc.Iterable[SlotSelectorType], /, rules: BuildRules
) -> abc.Iterator[SlotType]:
    for arg in args:
        if isinstance(arg, Type | tuple):
            yield arg

        elif arg == "body":
            yield from (Type.TORSO, Type.LEGS)

        elif arg == "specials":
            yield from (Type.TELEPORTER, Type.CHARGE, Type.HOOK, Type.SHIELD)

        elif arg == "weapons":
            for subtype in (Type.SIDE_WEAPON, Type.TOP_WEAPON):
                yield from ((subtype, n) for n in range(rules.VARIADIC_SLOTS[subtype]))
            yield Type.DRONE

        else:
            msg = f"Invalid selector: {arg}"
            raise TypeError(msg)


def dominant_element(mech: Mech, /, threshold: int = 2) -> Element | None:
    """Guesses the mech type by equipped items.

    threshold: the difference in item count required for either of the two most common elements\
     to be considered over the other.
    """
    from collections import Counter

    elements = Counter(
        item.element for item in mech.iter_items("body", "weapons", Type.HOOK) if item is not None
    ).most_common(2)
    # return None when there are no elements
    # or the difference between the two most common is indecisive
    if len(elements) == 0 or (len(elements) > 1 and elements[0][1] - elements[1][1] < threshold):
        return None

    # otherwise just return the most common one
    return elements[0][0]
