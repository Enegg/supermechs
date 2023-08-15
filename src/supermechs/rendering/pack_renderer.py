from __future__ import annotations

import logging
import typing as t

from attrs import define, field

from ..enums import Tier, Type
from ..models.item import Item
from ..typeshed import T, twotuple
from .attachments import cast_attachment

if t.TYPE_CHECKING:
    from PIL.Image import Image

    from ..models.item_data import ItemData
    from ..models.mech import Mech
    from ..typedefs import ID, RawPlane2D
    from .sprites import ItemSprite

__all__ = ("Rectangular", "PackRenderer")

LOGGER = logging.getLogger(__name__)

LAYER_ORDER = (
    "drone",
    "side2",
    "side4",
    "top2",
    "leg2",
    "torso",
    "leg1",
    "top1",
    "side1",
    "side3",
)


class Rectangular(t.Protocol):
    """Object which has width and height."""

    @property
    def width(self) -> int:
        ...

    @property
    def height(self) -> int:
        ...


@define
class Offsets:
    """Dataclass describing how many pixels the complete image extends beyond canvas."""

    left: int = 0
    right: int = 0
    above: int = 0
    below: int = 0

    def adjust(self, image: Rectangular, x: int, y: int) -> None:
        """Updates the canvas size in-place, if the new data extends beyond previous."""
        self.left = max(self.left, -x)
        self.above = max(self.above, -y)
        self.right = max(self.right, x + image.width)
        self.below = max(self.below, y + image.height)

    def final_size(self, base_image: Rectangular) -> twotuple[int]:
        """Return the final size of the canvas, given base image."""
        return (
            self.left + max(base_image.width, self.right),
            self.above + max(base_image.height, self.below),
        )


def combine_attachments(position: twotuple[int], offset: twotuple[int]) -> twotuple[int]:
    corner_x, corner_y = position
    offset_x, offset_y = offset
    return (offset_x - corner_x, offset_y - corner_y)


@define
class Canvas(t.Generic[T]):
    """Class responsible for merging layered images into one."""

    base: Image = field()
    layers: t.Sequence[T] = field()
    offsets: Offsets = field(factory=Offsets)
    images: list[tuple[int, int, Image] | None] = field(init=False)

    def __attrs_post_init__(self) -> None:
        self.images = [None] * len(self.layers)

    def __setitem__(self, position: tuple[T, int, int], image: Image, /) -> None:
        layer, x, y = position
        self.offsets.adjust(image, x, y)
        self.images[self.layers.index(layer)] = (x, y, image)

    def merge(self, base_layer: T, /) -> Image:
        """Merges all images into one and returns it."""
        self.images[self.layers.index(base_layer)] = (0, 0, self.base)

        from PIL import Image

        canvas = Image.new(
            "RGBA",
            self.offsets.final_size(self.base),
            (0, 0, 0, 0),
        )

        for x, y, image in filter(None, self.images):
            canvas.alpha_composite(image, (x + self.offsets.left, y + self.offsets.above))

        return canvas


@define
class PackRenderer:
    pack_key: str
    item_sprites: t.Mapping[ID, ItemSprite]

    @t.overload
    def get_item_sprite(self, item: ItemData, /, tier: Tier) -> ItemSprite:
        ...

    @t.overload
    def get_item_sprite(self, item: Item, /) -> ItemSprite:
        ...

    def get_item_sprite(
        self, item: ItemData | Item, /, tier: Tier | None = None
    ) -> ItemSprite:
        if isinstance(item, Item):
            tier = item.stage.tier
            item = item.data
        del tier  # TODO: implement when storing TieredSprite

        if item.pack_key != self.pack_key:
            raise ValueError("Item of different pack key passed")

        return self.item_sprites[item.id]

    def create_mech_image(self, mech: Mech, /) -> Image:
        if mech.torso is None:
            raise RuntimeError("Cannot create mech image without torso set")

        torso_sprite = self.get_item_sprite(mech.torso.item)

        attachments = cast_attachment(torso_sprite.attachment, Type.TORSO)
        canvas = Canvas[str](torso_sprite.image, LAYER_ORDER)

        if mech.legs is not None:
            legs_sprite = self.get_item_sprite(mech.legs.item)
            leg_attachment = cast_attachment(legs_sprite.attachment, Type.LEGS)

            for layer in ("leg1", "leg2"):
                x, y = combine_attachments(leg_attachment, attachments[layer])
                canvas[layer, x, y] = legs_sprite.image

        for inv_item, layer in mech.iter_items(weapons=True, slots=True):
            if inv_item is None:
                continue

            item_sprite = self.get_item_sprite(inv_item.item)
            item_attachment = cast_attachment(item_sprite.attachment, Type.SIDE_WEAPON)
            x, y = combine_attachments(item_attachment, attachments[layer])
            canvas[layer, x, y] = item_sprite.image

        if mech.drone is not None:
            drone_sprite = self.get_item_sprite(mech.drone.item)
            x = drone_sprite.width // 2 + canvas.offsets.left
            y = drone_sprite.height + 25 + canvas.offsets.above
            canvas["drone", x, y] = drone_sprite.image

        return canvas.merge("torso")


def crop_from_spritesheet(spritesheet: Image, pos: RawPlane2D) -> Image:
    x, y, w, h = pos["x"], pos["y"], pos["width"], pos["height"]
    return spritesheet.crop((x, y, x + w, y + h))
