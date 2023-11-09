import typing as t

__all__ = (
    "RawBox2D",
    "RawPoint2D",
    "RawTorsoAttachments",
    "AnyRawAttachment",
    "ItemImageParams",
)


class RawPoint2D(t.TypedDict):
    x: int
    y: int


RawTorsoAttachments = t.Mapping[str, RawPoint2D]
AnyRawAttachment = RawPoint2D | RawTorsoAttachments | None


class RawBox2D(RawPoint2D):
    width: int
    height: int


class ItemImageParams(t.TypedDict, total=False):
    width: int
    height: int
    image: str
    attachment: RawPoint2D | RawTorsoAttachments
