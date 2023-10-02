from __future__ import annotations

import typing as t

from ..models.item import Type

__all__ = (
    "TORSO_ATTACHMENT_FIELDS",
    "Point2D",
    "TorsoAttachments",
    "AnyAttachment",
    "is_attachable",
    "create_synthetic_attachment",
    "cast_attachment",
)


class Point2D(t.NamedTuple):
    x: int
    y: int


TorsoAttachments = t.Mapping[str, Point2D]
AnyAttachment = Point2D | TorsoAttachments | None

TORSO_ATTACHMENT_FIELDS = ("leg1", "leg2", "side1", "side2", "side3", "side4", "top1", "top2")


def is_displayable(type: Type, /) -> bool:
    """Whether item of given type can appear in a composite mech's image."""
    return type not in (Type.TELEPORTER, Type.CHARGE, Type.HOOK, Type.MODULE)


def is_attachable(type: Type, /) -> bool:
    """Whether item of given type should have an image attachment."""
    return is_displayable(type) and type is not Type.DRONE


_position_coeffs: t.Mapping[Type, tuple[float, float]] = {
    Type.LEGS: (0.5, 0.1), Type.SIDE_WEAPON: (0.3, 0.5), Type.TOP_WEAPON: (0.3, 0.8)
}


def create_synthetic_attachment(width: int, height: int, type: Type) -> AnyAttachment:
    """Create an attachment off given image size.

    Note: likely won't work well for scope-like items.

    Taken directly from WU, credits to Raul.
    """
    if type is Type.TORSO:
        return dict(
            leg1=Point2D(round(width * 0.40), round(height * 0.9)),
            leg2=Point2D(round(width * 0.80), round(height * 0.9)),
            side1=Point2D(round(width * 0.25), round(height * 0.6)),
            side2=Point2D(round(width * 0.75), round(height * 0.6)),
            side3=Point2D(round(width * 0.20), round(height * 0.3)),
            side4=Point2D(round(width * 0.80), round(height * 0.3)),
            top1=Point2D(round(width * 0.25), round(height * 0.1)),
            top2=Point2D(round(width * 0.75), round(height * 0.1)),
        )

    if coeffs := _position_coeffs.get(type, None):
        return Point2D(round(width * coeffs[0]), round(height * coeffs[1]))

    return None


@t.overload
def cast_attachment(attachment: AnyAttachment, type: t.Literal[Type.TORSO]) -> TorsoAttachments:
    ...


@t.overload
def cast_attachment(
    attachment: AnyAttachment, type: t.Literal[Type.SIDE_WEAPON, Type.TOP_WEAPON, Type.LEGS]
) -> Point2D:
    ...


@t.overload
def cast_attachment(attachment: AnyAttachment, type: Type) -> None:
    ...


def cast_attachment(attachment: AnyAttachment, type: Type) -> AnyAttachment:
    del type
    return attachment
