import typing as t
from collections import Counter

from attrs import Attribute, define, field

from ..converters import slot_to_type
from ..enums import Element, Type
from ..typeshed import XOrTupleXY
from ..utils import cached_slot_property
from .item import Item

ItemSlot = Item | None


def _is_valid_type(
    inst: t.Any, attr: Attribute[ItemSlot | t.Any], item: ItemSlot | t.Any, /
) -> None:
    """Check if item type matches the slot it is assigned to."""
    del inst

    if item is None:
        return

    if not isinstance(item, Item):
        raise TypeError(f"Invalid object set as item: {item!r}")

    valid_type = slot_to_type(attr.name)
    actual_type = item.data.type

    if actual_type is not valid_type:
        raise ValueError(f"Mech slot {attr.name} expects a {valid_type} type, got {actual_type}")


@define
class DisplayMech:
    # fmt: off
    torso:    ItemSlot = field(default=None, init=False, validator=_is_valid_type)
    legs:     ItemSlot = field(default=None, init=False, validator=_is_valid_type)
    drone:    ItemSlot = field(default=None, init=False, validator=_is_valid_type)
    teleport: ItemSlot = field(default=None, init=False, validator=_is_valid_type)
    charge:   ItemSlot = field(default=None, init=False, validator=_is_valid_type)
    hook:     ItemSlot = field(default=None, init=False, validator=_is_valid_type)
    _side_weapons: t.MutableSequence[ItemSlot] = field(init=False, factory=lambda: [None] * 4)
    _top_weapons:  t.MutableSequence[ItemSlot] = field(init=False, factory=lambda: [None] * 2)
    _modules:      t.MutableSequence[ItemSlot] = field(init=False, factory=lambda: [None] * 8)
    # fmt: on
    _dominant_element: Element | None = field(init=False, repr=False, eq=False)

    @property
    def side_weapons(self) -> t.Sequence[ItemSlot]:
        return tuple(self._side_weapons)

    @property
    def top_weapons(self) -> t.Sequence[ItemSlot]:
        return tuple(self._top_weapons)

    @property
    def modules(self) -> t.Sequence[ItemSlot]:
        return tuple(self._modules)

    @cached_slot_property
    def dominant_element(self) -> Element | None:
        """Guesses the mech type by equipped items."""
        excluded = {Type.CHARGE_ENGINE, Type.TELEPORTER}
        elements = Counter(
            item.data.element
            for item in self.iter_items(body=True, weapons=True, specials=True)
            if item is not None
            if item.data.type not in excluded
        ).most_common(2)
        # return None when there are no elements
        # or the difference between the two most common is small
        if len(elements) == 0 or (len(elements) > 1 and elements[0][1] - elements[1][1] < 2):
            return None

        # otherwise just return the most common one
        return elements[0][0]

    @t.overload
    def iter_items(
        self,
        *,
        body: bool = ...,
        weapons: bool = ...,
        specials: bool = ...,
        modules: bool = ...,
        slots: t.Literal[False] = False,
    ) -> t.Iterator[ItemSlot]:
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
    ) -> t.Iterator[tuple[ItemSlot, str]]:
        ...

    def iter_items(
        self,
        *,
        body: bool = False,
        weapons: bool = False,
        specials: bool = False,
        modules: bool = False,
        slots: bool = False,
    ) -> t.Iterator[XOrTupleXY[ItemSlot, str]]:
        """Iterator over mech's selected items.

        Parameters
        ----------
        body: Whether to include the torso, legs and drone.
        weapons: Whether to include the side and top weapons.
        specials: Whether to include the teleport, charge and hook.
        modules: Whether to include the modules.

        If none of the above selectors are True (the default), yields from all groups.

        slots: If `True`, yields tuples of both the item and its slot's name.\
            Otherwise, yields just the items.

        Yields
        ------
        `InvItem | None`
            If `slots` is set to `False`.
        `tuple[InvItem | None, str]`
            If `slots` is set to `True`.
        """
        if not (body or weapons or specials or modules):
            body = weapons = specials = modules = True

        factory: t.Callable[[str], XOrTupleXY[ItemSlot, str]]

        if slots:
            factory = lambda slot: (getattr(self, slot), slot)  # noqa: E731

        else:
            from functools import partial
            factory = partial(getattr, self)

        if body:
            yield from map(factory, ("torso", "legs", "drone"))

        if weapons:
            if slots:
                yield from zip(self._side_weapons, ("side1", "side2", "side3", "side4"))
                yield from zip(self._top_weapons, ("top1", "top2"))

            else:
                yield from self._side_weapons
                yield from self._top_weapons

        if specials:
            yield from map(factory, ("teleport", "charge", "hook"))

        if modules:
            if slots:
                yield from zip(self._modules, (f"mod{n}" for n in range(1, 9)))
