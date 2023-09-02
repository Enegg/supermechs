import typing as t
import typing_extensions as tex

from .enums import Type
from .typeshed import XOrTupleXY

__all__ = ("parse_slot_name", "slot_to_type")

_type_to_slot: t.Mapping[Type, tex.LiteralString] = {
    Type.SIDE_WEAPON: "side",
    Type.TOP_WEAPON: "top",
    Type.TELEPORTER: "tele",
    Type.CHARGE_ENGINE: "charge",
    Type.GRAPPLING_HOOK: "hook",
}


def _type_to_partial_slot(type: Type, /) -> tex.LiteralString:
    return _type_to_slot.get(type) or type.name.lower()


def slot_to_type(slot: str, /) -> Type:
    """Convert slot literal to corresponding type enum."""
    if slot.startswith("side"):
        return Type.SIDE_WEAPON

    if slot.startswith("top"):
        return Type.TOP_WEAPON

    if slot.startswith("mod"):
        return Type.MODULE

    return Type[slot.upper()]


def parse_slot_name(slot_selector: XOrTupleXY[str | Type, int], /) -> str:
    """Parse a slot to appropriate name. Raises ValueError if invalid."""
    match slot_selector:
        case (str() as slot, int() as pos):
            slot = slot.lower() + str(pos)

        case (Type() as slot, int() as pos):
            slot = _type_to_partial_slot(slot) + str(pos)

        case Type():
            slot = _type_to_partial_slot(slot_selector)

        case str():  # pyright: ignore[reportUnnecessaryComparison] The hell?
            slot = slot_selector.lower()

    return slot
