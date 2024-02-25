from collections import abc
from typing import TypeAlias

from typing_extensions import TypedDict

from supermechs.typeshed import LiteralURL

__all__ = (
    "AnyRawAttachment",
    "ItemImageParams",
    "RawBox2D",
    "RawPoint2D",
    "RawTorsoAttachments",
    "SpritesSheetMixin",
)


class RawPoint2D(TypedDict):
    x: int
    y: int


RawTorsoAttachments: TypeAlias = abc.Mapping[str, RawPoint2D]
AnyRawAttachment: TypeAlias = RawPoint2D | RawTorsoAttachments | None


class RawBox2D(RawPoint2D):
    width: int
    height: int


class ItemImageParams(TypedDict, total=False):
    width: int
    height: int
    attachment: RawPoint2D | RawTorsoAttachments


class SpritesSheetMixin(TypedDict):
    spritesSheet: LiteralURL
    spritesMap: dict[str, RawBox2D]
