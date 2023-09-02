import logging
import typing as t
from bisect import insort_left

from attrs import define, field

from ..enums import Tier, Type
from ..models.item import Item, ItemData
from ..typeshed import twotuple
from ..utils import large_mapping_repr
from .attachments import TORSO_ATTACHMENT_FIELDS, cast_attachment

if t.TYPE_CHECKING:
    from PIL.Image import Image

    from ..models.mech import Mech
    from ..typedefs import ID
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
class Canvas:
    """Class responsible for merging layered images into one."""

    base: "Image" = field()
    offsets: Offsets = field(factory=Offsets)
    images: t.MutableSequence[tuple[int, int, int, "Image"]] = field(init=False, factory=list)

    def __setitem__(self, position: tuple[int, int, int], image: "Image", /) -> None:
        layer, x, y = position
        self.offsets.adjust(image, x, y)
        insort_left(self.images, (layer, x, y, image), key=lambda t: t[0])

    def merge(self, base_layer: int, /) -> "Image":
        """Merges all images into one and returns it."""
        insort_left(self.images, (base_layer, 0, 0, self.base), key=lambda t: t[0])

        from PIL import Image

        canvas = Image.new(
            "RGBA",
            self.offsets.final_size(self.base),
            (0, 0, 0, 0),
        )

        for _, x, y, image in self.images:
            canvas.alpha_composite(image, (x + self.offsets.left, y + self.offsets.above))

        return canvas


@define
class PackRenderer:
    pack_key: str = field()
    sprites: t.Mapping["ID", "ItemSprite"] = field(repr=large_mapping_repr)

    @t.overload
    def get_item_sprite(self, item: "ItemData", /, tier: Tier) -> "ItemSprite":
        ...

    @t.overload
    def get_item_sprite(self, item: Item, /) -> "ItemSprite":
        ...

    def get_item_sprite(self, item: "ItemData | Item", /, tier: Tier | None = None) -> "ItemSprite":
        if isinstance(item, Item):
            tier = item.stage.tier
            item = item.data
        del tier  # TODO: implement when storing TieredSprite

        if item.pack_key != self.pack_key:
            raise ValueError("Item of different pack key passed")

        return self.sprites[item.id]

    def create_mech_image(self, mech: "Mech", /) -> "Image":
        if mech.torso is None:
            raise RuntimeError("Cannot create mech image without torso set")

        torso_sprite = self.get_item_sprite(mech.torso.item)

        attachments = cast_attachment(torso_sprite.attachment, Type.TORSO)
        canvas = Canvas(torso_sprite.image)

        if mech.legs is not None:
            legs_sprite = self.get_item_sprite(mech.legs.item)
            leg_attachment = cast_attachment(legs_sprite.attachment, Type.LEGS)

            for layer in TORSO_ATTACHMENT_FIELDS[:2]:
                x, y = combine_attachments(leg_attachment, attachments[layer])
                canvas[LAYER_ORDER.index(layer), x, y] = legs_sprite.image

        for inv_item, layer in zip(mech.iter_items("weapons"), TORSO_ATTACHMENT_FIELDS[2:]):
            if inv_item is None:
                continue

            item_sprite = self.get_item_sprite(inv_item.item)
            item_attachment = cast_attachment(item_sprite.attachment, Type.SIDE_WEAPON)
            x, y = combine_attachments(item_attachment, attachments[layer])
            canvas[LAYER_ORDER.index(layer), x, y] = item_sprite.image

        if mech.drone is not None:
            drone_sprite = self.get_item_sprite(mech.drone.item)
            x = drone_sprite.width // 2 + canvas.offsets.left
            y = drone_sprite.height + 25 + canvas.offsets.above
            canvas[LAYER_ORDER.index("drone"), x, y] = drone_sprite.image

        return canvas.merge(LAYER_ORDER.index("torso"))
