from .enums import Type
from .typeshed import XOrTupleXY

__all__ = (
    "BODY_SLOTS",
    "MODULE_SLOTS",
    "SPECIAL_SLOTS",
    "WEAPON_SLOTS",
    "get_slot_name",
    "slot_to_type",
)

BODY_SLOTS = ("torso", "legs", "drone")
WEAPON_SLOTS = ("side1", "side2", "side3", "side4", "top1", "top2")
SPECIAL_SLOTS = ("tele", "charge", "hook")
MODULE_SLOTS = ("mod1", "mod2", "mod3", "mod4", "mod5", "mod6", "mod7", "mod8")
_SLOTS_SET = frozenset(BODY_SLOTS).union(WEAPON_SLOTS, SPECIAL_SLOTS, MODULE_SLOTS)


_type_to_slot_lookup = {
    Type.SIDE_WEAPON: "side",
    Type.TOP_WEAPON: "top",
    Type.TELEPORTER: "tele",
    Type.CHARGE_ENGINE: "charge",
    Type.GRAPPLING_HOOK: "hook",
}


def _type_to_partial_slot(type: Type) -> str:
    return _type_to_slot_lookup.get(type) or type.name.lower()


def slot_to_type(slot: str) -> Type:
    """Convert slot literal to corresponding type enum."""
    if slot.startswith("side"):
        return Type.SIDE_WEAPON

    if slot.startswith("top"):
        return Type.TOP_WEAPON

    if slot.startswith("mod"):
        return Type.MODULE

    return Type[slot.upper()]


def get_slot_name(slot_: XOrTupleXY[str | Type, int], /):
    """Parse a slot to appropriate name. Raises TypeError if invalid."""
    match slot_:
        case (str() as slot, int() as pos):
            slot = slot.lower() + str(pos)

        case (Type() as slot, int() as pos):
            slot = _type_to_partial_slot(slot) + str(pos)

        case Type():
            slot = _type_to_partial_slot(slot_)

        case str():
            slot = slot_.lower()

    if slot not in _SLOTS_SET:
        raise LookupError(f"{slot_!r} is not a valid slot")

    return slot
