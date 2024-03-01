import typing
import typing_extensions as typing_
from collections import abc

from supermechs.typeshed import LiteralURL

__all__ = (
    "AnyRawAttachment",
    "ItemImageParams",
    "RawBox2D",
    "RawPoint2D",
    "RawTorsoAttachments",
    "SpritesSheetMixin",
)


class RawPoint2D(typing_.TypedDict):
    x: int
    y: int


RawTorsoAttachments: typing.TypeAlias = abc.Mapping[str, RawPoint2D]
AnyRawAttachment: typing.TypeAlias = RawPoint2D | RawTorsoAttachments | None


class RawBox2D(RawPoint2D):
    width: int
    height: int


class ItemImageParams(typing_.TypedDict, total=False):
    width: int
    height: int
    attachment: RawPoint2D | RawTorsoAttachments


class SpritesSheetMixin(typing_.TypedDict):
    spritesSheet: LiteralURL
    spritesMap: dict[str, RawBox2D]
