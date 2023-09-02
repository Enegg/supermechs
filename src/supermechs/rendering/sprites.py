from __future__ import annotations

import typing as t

from attrs import define

if t.TYPE_CHECKING:
    from PIL.Image import Image

    from .attachments import AnyAttachment

__all__ = ("ItemSprite",)


@define
class ItemSprite:
    image: Image
    attachment: AnyAttachment = None

    @property
    def width(self) -> int:
        return self.image.width

    @property
    def height(self) -> int:
        return self.image.height

    @property
    def size(self) -> tuple[int, int]:
        return self.image.size
