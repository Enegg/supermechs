from collections import abc
from typing import TYPE_CHECKING
from typing_extensions import TypeVar, override

import attrs

import supermechs.abc as sabc
from supermechs.enums import SlotName
from supermechs.utils import default

__all__ = ("Mech", "MechSummary", "MutableMech")

ItemT = TypeVar("ItemT", infer_variance=True)
_ZERO = 0.0


@attrs.define(frozen=TYPE_CHECKING)
class Mech(sabc.Mech[ItemT]):
    setup: abc.Mapping[sabc.MechSlot, ItemT] = attrs.field(factory=dict)

    @property
    @override
    def torso(self) -> ItemT | None:
        return self.setup.get(sabc.MechSlot(SlotName.torso))

    @property
    @override
    def legs(self) -> ItemT | None:
        return self.setup.get(sabc.MechSlot(SlotName.legs))

    @property
    @override
    def drone(self) -> ItemT | None:
        return self.setup.get(sabc.MechSlot(SlotName.drone))

    @property
    @override
    def charge(self) -> ItemT | None:
        return self.setup.get(sabc.MechSlot(SlotName.charge))

    @property
    @override
    def teleport(self) -> ItemT | None:
        return self.setup.get(sabc.MechSlot(SlotName.teleport))

    @property
    @override
    def hook(self) -> ItemT | None:
        return self.setup.get(sabc.MechSlot(SlotName.hook))

    @property
    @override
    def shield(self) -> ItemT | None:
        return self.setup.get(sabc.MechSlot(SlotName.shield))

    @property
    @override
    def perk(self) -> ItemT | None:
        return self.setup.get(sabc.MechSlot(SlotName.perk))

    @override
    def __getitem__(self, name: sabc.MechSlot, /) -> ItemT | None:
        return self.setup.get(name)

    @override
    def iter_items(self) -> abc.Iterator[ItemT]:
        yield from self.setup.values()


@attrs.define(frozen=TYPE_CHECKING)
class MutableMech(Mech[ItemT]):
    if TYPE_CHECKING:
        setup: abc.MutableMapping[sabc.MechSlot, ItemT] = attrs.field(factory=dict)

    def __setitem__(self, name: sabc.MechSlot, item: ItemT | None, /) -> None:
        if item is None:
            del self[name]

        else:
            self.setup[name] = item

    def __delitem__(self, name: sabc.MechSlot, /) -> None:
        self.setup.pop(name, None)

    def to_mech(self) -> Mech[ItemT]:
        return Mech(dict(self.setup))


@attrs.define
class MechSummary:
    @default
    @staticmethod
    def zeros() -> sabc.MechSummary:
        return MechSummary()

    weight: float = _ZERO
    hit_points: float = _ZERO
    energy_capacity: float = _ZERO
    regeneration: float = _ZERO
    heat_capacity: float = _ZERO
    cooling: float = _ZERO
    physical_resistance: float = _ZERO
    explosive_resistance: float = _ZERO
    electric_resistance: float = _ZERO
    bullets_capacity: float = _ZERO
    rockets_capacity: float = _ZERO
    walk: float = _ZERO
    jump: float = _ZERO
