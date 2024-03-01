from ..enums.item import Type

__all__ = ("is_attachable", "is_displayable")


def is_displayable(type: Type, /) -> bool:
    """Whether items of given type are a part of mech's sprite."""
    return type not in (Type.TELEPORTER, Type.CHARGE, Type.HOOK, Type.MODULE)


def is_attachable(type: Type, /) -> bool:
    """Whether item of given type should have a joint."""
    return is_displayable(type) and type is not Type.DRONE
