import typing as t

from ..typeshed import T

if t.TYPE_CHECKING:
    from .attachments import AnyAttachment

__all__ = ("ItemSprite", "Metadata")


class Metadata(t.NamedTuple):
    """Image related metadata."""

    source: t.Literal["url", "file"]
    method: t.Literal["single", "sheet"]
    value: str


class ItemSprite(t.Protocol[T]):
    @property
    def metadata(self) -> Metadata:
        """Image metadata, including its source."""
        ...

    image: T
    attachment: "AnyAttachment"

    async def load(self) -> None:
        """Resolve image data."""
        ...
