from supermechs.abc.item import Type
from supermechs.enums.item import TypeEnum

__all__ = ("is_attachable", "is_displayable")


def is_displayable(type: Type, /) -> bool:
    """Whether items of given type are a part of mech's sprite."""
    return type not in (TypeEnum.TELEPORTER, TypeEnum.CHARGE, TypeEnum.HOOK, TypeEnum.MODULE)


def is_attachable(type: Type, /) -> bool:
    """Whether item of given type should have a joint."""
    return is_displayable(type) and type != TypeEnum.DRONE
