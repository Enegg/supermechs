from __future__ import annotations

import typing_extensions as t
from typing import TYPE_CHECKING

from attrs import define, field
from PIL.Image import Image

if TYPE_CHECKING:
    from .attachments import AnyAttachment

__all__ = ("ItemSprite", "SingleResolver", "SpritesheetResolver")

MetadataT = t.TypeVar("MetadataT", infer_variance=True)
Loader = t.Callable[[MetadataT], t.Awaitable[Image]]
Processor = t.Callable[[Image], Image]

MISSING_ATTACHMENT: t.Any = object()


class ItemSprite(t.Protocol[MetadataT]):
    @property
    def metadata(self) -> MetadataT:
        """Image metadata, including its source."""
        ...

    @property
    def image(self) -> t.Awaitable[Image]:
        ...

    @image.deleter
    def image(self) -> None:
        ...

    @property
    def attachment(self) -> AnyAttachment:
        ...

    async def load(self) -> None:
        """Resolve image data."""
        ...


@define
class SingleResolver(ItemSprite[MetadataT]):
    loader: t.Final[Loader[MetadataT]]
    metadata: t.Final[MetadataT]
    attachment: AnyAttachment = MISSING_ATTACHMENT
    post_processors: t.Final[t.Sequence[Processor]] = field(default=())
    _image: Image | None = field(default=None, init=False)

    @property
    @t.override
    async def image(self) -> Image:
        await self.load()
        assert self._image is not None
        return self._image

    @image.deleter
    @t.override
    def image(self) -> None:
        self._image = None

    @t.override
    async def load(self) -> None:
        # TODO: Implement locks
        if self._image is not None:
            return

        image = await self.loader(self.metadata)

        for processor in self.post_processors:
            image = processor(image)

        self._image = image


@define
class SpritesheetResolver(ItemSprite[MetadataT]):
    spritesheet: t.Final[ItemSprite[MetadataT]]
    rect: t.Final[tuple[int, int, int, int]]
    attachment: AnyAttachment = MISSING_ATTACHMENT
    post_processors: t.Sequence[Processor] = field(default=())
    _image: Image | None = field(default=None, init=False)

    @property
    @t.override
    def metadata(self) -> MetadataT:
        return self.spritesheet.metadata

    @property
    @t.override
    async def image(self) -> Image:
        await self.load()
        assert self._image is not None
        return self._image

    @image.deleter
    @t.override
    def image(self) -> None:
        self._image = None

    @t.override
    async def load(self) -> None:
        # TODO: Implement locks
        if self._image is not None:
            return

        image = await self.spritesheet.image
        image = image.crop(self.rect)

        for processor in self.post_processors:
            image = processor(image)

        self._image = image
