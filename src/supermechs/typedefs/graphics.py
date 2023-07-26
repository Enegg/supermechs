import typing as t

__all__ = (
    "RawPoint2D",
    "RawPlane2D",
    "RawTorsoAttachments",
    "AnyRawAttachment",
    "ItemImageParams",
)


class RawPoint2D(t.TypedDict):
    x: int
    y: int


RawTorsoAttachments = t.Mapping[str, RawPoint2D]
AnyRawAttachment = RawPoint2D | RawTorsoAttachments | None


class RawPlane2D(RawPoint2D):
    width: int
    height: int


class ItemImageParams(t.TypedDict, total=False):
    width: int
    height: int
    attachment: RawPoint2D | RawTorsoAttachments
