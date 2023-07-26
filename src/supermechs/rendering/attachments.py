from __future__ import annotations

import typing as t

from typing_extensions import Self

from ..enums import Type
from ..errors import MalformedData

if t.TYPE_CHECKING:
    from ..typedefs import AnyRawAttachment, RawPoint2D, RawTorsoAttachments

__all__ = (
    "Point2D",
    "TorsoAttachments",
    "AnyAttachment",
    "parse_raw_attachment",
    "is_attachable",
    "create_synthetic_attachment",
    "cast_attachment",
)


class Point2D(t.NamedTuple):
    x: int
    y: int

    @classmethod
    def from_dict(cls, mapping: RawPoint2D, /) -> Self:
        x, y = mapping["x"], mapping["y"]

        if not (isinstance(x, int) and isinstance(y, int)):
            raise TypeError(f"Attachment got x: {type(x)}, y: {type(y)} as values")

        return cls(x, y)


TorsoAttachments = t.Mapping[str, Point2D]
AnyAttachment = Point2D | TorsoAttachments | None


def is_displayable(type: Type) -> bool:
    """Whether item of given type can appear in a composite mech's image."""
    return type not in (Type.TELEPORTER, Type.CHARGE, Type.HOOK, Type.MODULE)


def is_attachable(type: Type) -> bool:
    """Whether item of given type should have an image attachment."""
    return is_displayable(type) and type is not Type.DRONE


def attachments_from_raw(mapping: RawTorsoAttachments) -> TorsoAttachments:
    return {key: Point2D.from_dict(mapping) for key, mapping in mapping.items()}


def parse_raw_attachment(raw_attachment: AnyRawAttachment) -> AnyAttachment:
    match raw_attachment:
        case {"x": int() as x, "y": int() as y}:
            return Point2D(x, y)

        case {
            "leg1": {},
            "leg2": {},
            "side1": {},
            "side2": {},
            "side3": {},
            "side4": {},
            "top1": {},
            "top2": {},
        }:
            return attachments_from_raw(raw_attachment)

        case None:
            return None

        case unknown:
            raise MalformedData("Invalid attachment", unknown)


position_coeffs = {Type.LEGS: (0.5, 0.1), Type.SIDE_WEAPON: (0.3, 0.5), Type.TOP_WEAPON: (0.3, 0.8)}


def create_synthetic_attachment(width: int, height: int, type: Type) -> AnyAttachment:
    """Create an attachment off given image size. Likely won't work well for scope-like items.
    Note: taken directly from WU, credits to Raul."""

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

    if coeffs := position_coeffs.get(type, None):
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
