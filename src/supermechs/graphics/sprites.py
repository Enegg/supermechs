from typing import Literal, NamedTuple, Protocol, TypeAlias, TypedDict

from supermechs.typeshed import LiteralURL

__all__ = ("Metadata", "Rectangular")

ImageSize: TypeAlias = tuple[int, int]


class ImageParams(TypedDict, total=False):
    resize: ImageSize
    url: LiteralURL
    bounding_box: tuple[int, int, int, int]


class Rectangular(Protocol):
    """Object with width and height."""

    @property
    def size(self) -> ImageSize:
        ...

    @property
    def width(self) -> int:
        ...

    @property
    def height(self) -> int:
        ...


class Metadata(NamedTuple):
    """Image related metadata."""

    type: Literal["single", "sheet"]
    extras: ImageParams


def get_target_size(image: Rectangular, metadata: Metadata, /) -> ImageSize:
    x, y = metadata.extras.get("resize") or (0, 0)
    return (x or image.width, y or image.height)
