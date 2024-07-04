from collections import abc
from typing import Literal, TypeAlias, overload

from attrs import define, field

from .abc.item import Type
from .abc.mech import Slot
from .enums.item import TypeEnum
from .enums.mech import ModuleEnum, SideWeaponEnum, TopWeaponEnum
from .gamerules import BuildRules
from .item import Item
from .utils import KeyAccessor, SequenceView

__all__ = ("Mech", "SlotMemberType")

SlotMemberType: TypeAlias = Item | None
SlotAccessor: TypeAlias = KeyAccessor[Type, SlotMemberType]
SlotSelectorType: TypeAlias = Slot | Literal["body", "weapons", "specials"]


@define(kw_only=True)
class Mech:
    """Represents a mech build."""

    side_weapon_slots: abc.Sequence[Slot] = field(default=tuple(SideWeaponEnum))
    top_weapon_slots: abc.Sequence[Slot] = field(default=tuple(TopWeaponEnum))
    module_slots: abc.Sequence[Slot] = field(default=tuple(ModuleEnum))
    rules: BuildRules = field(default=BuildRules.default)
    _setup: abc.MutableMapping[Slot, Item] = field(factory=dict, init=False)
    # fmt: off
    torso      = SlotAccessor(TypeEnum.TORSO)
    legs       = SlotAccessor(TypeEnum.LEGS)
    drone      = SlotAccessor(TypeEnum.DRONE)
    teleporter = SlotAccessor(TypeEnum.TELEPORTER)
    charge     = SlotAccessor(TypeEnum.CHARGE)
    hook       = SlotAccessor(TypeEnum.HOOK)
    shield     = SlotAccessor(TypeEnum.SHIELD)
    perk       = SlotAccessor(TypeEnum.PERK)
    # fmt: on

    def side_weapons(self):  # noqa: ANN201
        """Sequence-like object providing a view on mech's side weapons."""
        return SequenceView(self, self.side_weapon_slots)

    def top_weapons(self):  # noqa: ANN201
        """Sequence-like object providing a view on mech's top weapons."""
        return SequenceView(self, self.top_weapon_slots)

    def modules(self):  # noqa: ANN201
        """Sequence-like object providing a view on mech's modules."""
        return SequenceView(self, self.module_slots)

    def __setitem__(self, slot: Slot, item: SlotMemberType, /) -> None:
        if not isinstance(item, SlotMemberType):
            msg = f"Expected {SlotMemberType}, got {type(item).__name__}"
            raise TypeError(msg)

        if item is None:
            del self[slot]

        else:
            self._setup[slot] = item

    def __getitem__(self, slot: Slot, /) -> SlotMemberType:
        return self._setup.get(slot)

    def __delitem__(self, slot: Slot, /) -> None:
        self._setup.pop(slot, None)

    def __str__(self) -> str:
        string_parts = [
            f"{slot.name.capitalize()}: {self[slot]}" for slot in (TypeEnum.TORSO, TypeEnum.LEGS)
        ]

        if weapon_string := ", ".join(str(item) for item in self.iter_items("weapons") if item):
            string_parts.append("Weapons: " + weapon_string)

        string_parts.extend(
            f"{item.type.capitalize()}: {item}"
            for item in self.iter_items("specials")
            if item is not None
        )

        if modules := ", ".join(str(item) for item in self.modules() if item):
            string_parts.append("Modules: " + modules)

        if perk := self.perk:
            string_parts.append(f"Perk: {perk}")

        return "\n".join(string_parts)

    @overload
    def iter_items(self) -> abc.Iterator[Item]: ...

    @overload
    def iter_items(self, *slots: SlotSelectorType) -> abc.Iterator[SlotMemberType]: ...

    def iter_items(self, *slots: SlotSelectorType) -> abc.Iterator[SlotMemberType]:
        """Iterator over selected mech's items.

        Parameters
        ----------
        slots:
            The order and `Type`s of items to yield.
            If no slots are provided, yields every equipped item.

            Literal string shorthands for related types:

            - "body" - `TORSO` & `LEGS`;
            - "weapons" - `SIDE_WEAPON`s, `TOP_WEAPON`s & `DRONE`;
            - "specials" - `TELEPORTER`, `CHARGE`, `HOOK` & `SHIELD`.
        """
        if not slots:
            yield from self._setup.values()
            return

        for slot in slots:
            if slot == "body":
                yield self.torso
                yield self.legs

            elif slot == "specials":
                yield self.teleporter
                yield self.charge
                yield self.hook
                yield self.shield

            elif slot == "weapons":
                yield from self.side_weapons()
                yield from self.top_weapons()
                yield self.drone

            else:
                yield self[slot]
