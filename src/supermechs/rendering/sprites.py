from __future__ import annotations

import typing as t
import typing_extensions as tex
from typing import TYPE_CHECKING

from attrs import define, field
from PIL.Image import Image

if TYPE_CHECKING:
    from .attachments import AnyAttachment

__all__ = ("ItemSprite", "SingleResolver", "SpritesheetResolver")

MetadataT = tex.TypeVar("MetadataT", infer_variance=True)
Loader = t.Callable[[MetadataT], t.Awaitable[Image]]


class ItemSprite(t.Protocol[MetadataT]):
    @property
    def metadata(self) -> MetadataT:
        """Image metadata, including its source."""
        ...

    image: Image
    attachment: AnyAttachment

    async def load(self) -> None:
        """Resolve image data."""
        ...


@define
class SingleResolver(ItemSprite[MetadataT]):
    loader: t.Final[Loader[MetadataT]]
    metadata: t.Final[MetadataT]
    attachment: AnyAttachment
    postprocess: t.Callable[[tex.Self], None] | None = None
    _image: Image | None = field(default=None, init=False)

    @property
    @tex.override
    def image(self) -> Image:
        if self._image is None:
            raise RuntimeError("Resource not loaded")
        return self._image

    @image.setter
    def image(self, image: Image, /) -> None:
        self._image = image

    @image.deleter
    @tex.override
    def image(self) -> None:
        self._image = None

    @tex.override
    async def load(self) -> None:
        # TODO: Implement locks
        if self._image is not None:
            return

        self._image = await self.loader(self.metadata)

        if self.postprocess is not None:
            self.postprocess(self)



@define
class SpritesheetResolver(ItemSprite[MetadataT]):
    spritesheet: t.Final[ItemSprite[MetadataT]]
    rect: t.Final[tuple[int, int, int, int]]
    attachment: AnyAttachment
    postprocess: t.Callable[[tex.Self], None] | None = None
    _image: Image | None = field(default=None, init=False)

    @property
    @tex.override
    def metadata(self) -> MetadataT:
        return self.spritesheet.metadata

    @property
    @tex.override
    def image(self) -> Image:
        if self._image is None:
            raise RuntimeError("Resource not loaded")
        return self._image

    @image.setter
    def image(self, image: Image, /) -> None:
        self._image = image

    @image.deleter
    @tex.override
    def image(self) -> None:
        self._image = None

    @tex.override
    async def load(self) -> None:
        # TODO: Implement locks
        if self._image is not None:
            return

        await self.spritesheet.load()
        self._image = self.spritesheet.image.crop(self.rect)

        if self.postprocess is not None:
            self.postprocess(self)
