from __future__ import annotations

import typing as t
from enum import auto

from ..item import Type
from ..utils import PartialEnum

__all__ = (
    "AnyAttachment",
    "AttachmentMapping",
    "Attachment",
    "Point2D",
    "create_synthetic_attachments",
    "is_attachable",
)


class Attachment(PartialEnum):
    """Enumeration of attachment points."""

    TORSO = auto()
    LEG_1 = auto()
    LEG_2 = auto()
    SIDE_WEAPON_1 = auto()
    SIDE_WEAPON_2 = auto()
    SIDE_WEAPON_3 = auto()
    SIDE_WEAPON_4 = auto()
    TOP_WEAPON_1 = auto()
    TOP_WEAPON_2 = auto()
    HAT = auto()
    CHARGE = auto()
    JUMP_JETS = auto()


class Point2D(t.NamedTuple):
    x: float
    y: float


AttachmentMapping: t.TypeAlias = t.Mapping[Attachment, Point2D]
AnyAttachment = AttachmentMapping | None


def is_displayable(type: Type, /) -> bool:
    """Whether item of given type affects mech's sprite."""
    return type not in (Type.TELEPORTER, Type.CHARGE, Type.HOOK, Type.MODULE)


def is_attachable(type: Type, /) -> bool:
    """Whether item of given type should have an image attachment."""
    return is_displayable(type) and type is not Type.DRONE


def create_synthetic_attachments(width: int, height: int, type: Type) -> AttachmentMapping | None:
    """Create an attachment off given image size.

    Note: likely won't work well for scope-like items.

    https://github.com/ctrlraul/supermechs-workshop/blob/6fe2e0a29bd4776f50f893d2ab0722020279e2d3/src/items/ItemsManager.ts#L286-L325
    """
    if type is Type.TORSO:
        # fmt: off
        return {
            Attachment.LEG_1:         Point2D(width * 0.40, height * 0.9),
            Attachment.LEG_2:         Point2D(width * 0.80, height * 0.9),
            Attachment.SIDE_WEAPON_1: Point2D(width * 0.25, height * 0.6),
            Attachment.SIDE_WEAPON_2: Point2D(width * 0.75, height * 0.6),
            Attachment.SIDE_WEAPON_3: Point2D(width * 0.20, height * 0.3),
            Attachment.SIDE_WEAPON_4: Point2D(width * 0.80, height * 0.3),
            Attachment.TOP_WEAPON_1:  Point2D(width * 0.25, height * 0.1),
            Attachment.TOP_WEAPON_2:  Point2D(width * 0.75, height * 0.1),
            Attachment.HAT:           Point2D(width * 0.50, height * 0.1),
            Attachment.CHARGE:        Point2D(width * 0.10, height * 0.5),
        }
        # fmt: on

    if type is Type.LEGS:
        # fmt: off
        return {
            Attachment.TORSO:     Point2D(width * 0.5, height * 0.1),
            # not all legs can jump but whatever
            Attachment.JUMP_JETS: Point2D(width * 0.5, height),
        }
        # fmt: on

    if type is Type.SIDE_WEAPON:
        return {Attachment.TORSO: Point2D(width * 0.3, height * 0.5)}

    if type is Type.TOP_WEAPON:
        return {Attachment.TORSO: Point2D(width * 0.3, height * 0.8)}

    return None


def assert_attachment(attachment: AnyAttachment, /) -> AttachmentMapping:
    if attachment is None:
        msg = "Item does not have a joint"
        raise TypeError(msg)

    return attachment
