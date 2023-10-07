from __future__ import annotations

import typing as t
import typing_extensions as tex

from attrs import define, field
from PIL.Image import Image

from .attachments import AnyAttachment

__all__ = ("ItemSprite", "SpriteResolver", "SpritesheetResolver", "Metadata")

Loader = t.Callable[["Metadata"], t.Awaitable[Image]]


class Metadata(t.NamedTuple):
    """Image related metadata."""

    source: t.Literal["url", "file"]
    method: t.Literal["single", "sheet"]
    value: str


class ItemSprite(t.Protocol):
    @property
    def metadata(self) -> Metadata:
        """Image metadata, including its source."""
        ...

    image: Image
    attachment: AnyAttachment

    async def load(self) -> None:
        """Resolve image data."""
        ...


@define
class SpriteResolver(ItemSprite):
    loader: t.Final[Loader]
    metadata: t.Final[Metadata]
    attachment: AnyAttachment
    postprocess: t.Callable[[tex.Self], None] | None = None
    _image: Image | None = field(default=None, init=False)

    @property
    @tex.override
    def image(self) -> Image:
        if self._image is None:
            raise RuntimeError("Resource not loaded")  # noqa: EM101
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
class SpritesheetResolver(ItemSprite):
    spritesheet: t.Final[ItemSprite]
    rect: t.Final[tuple[int, int, int, int]]
    attachment: AnyAttachment
    postprocess: t.Callable[[tex.Self], None] | None = None
    _image: Image | None = field(default=None, init=False)

    @property
    @tex.override
    def metadata(self) -> Metadata:
        sheet_meta = self.spritesheet.metadata
        return Metadata(sheet_meta.source, "sheet", sheet_meta.value)

    @property
    @tex.override
    def image(self) -> Image:
        if self._image is None:
            raise RuntimeError("Resource not loaded")  # noqa: EM101
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
