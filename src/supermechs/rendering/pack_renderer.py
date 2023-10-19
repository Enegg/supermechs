import typing as t
from bisect import insort_left

import anyio
from attrs import define, field

from ..item import Item, ItemData, Tier
from ..mech import Mech
from ..typeshed import ID, twotuple
from ..utils import large_mapping_repr
from .attachments import Attachment, assert_attachment

if t.TYPE_CHECKING:
    from PIL.Image import Image

    from .sprites import ItemSprite

__all__ = ("Rectangular", "PackRenderer")

LAYER_ORDER = (
    Attachment.SIDE_WEAPON_2,
    Attachment.SIDE_WEAPON_4,
    Attachment.TOP_WEAPON_2,
    Attachment.LEG_2,
    Attachment.TORSO,
    Attachment.LEG_1,
    Attachment.TOP_WEAPON_1,
    Attachment.SIDE_WEAPON_1,
    Attachment.SIDE_WEAPON_3,
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


def combine_attachments(position: twotuple[float], offset: twotuple[float]) -> twotuple[int]:
    return (round(offset[0] - position[0]), round(offset[1] - position[1]))


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
            msg = "Item of different pack key passed"
            raise ValueError(msg)

        return self.sprites[item.id]

    async def load_mech_images(self, mech: Mech, /) -> None:
        async with anyio.create_task_group() as tg:
            for item in filter(None, mech.iter_items(Mech.Slot.TORSO, Mech.Slot.LEGS, "weapons")):
                sprite = self.get_item_sprite(item)
                tg.start_soon(sprite.load)

    def create_mech_image(self, mech: Mech, /) -> "Image":
        if mech.torso is None:
            msg = "Cannot create mech image without torso set"
            raise RuntimeError(msg)

        torso_sprite = self.get_item_sprite(mech.torso)
        attachments = assert_attachment(torso_sprite.attachment)
        canvas = Canvas(torso_sprite.image)

        if mech.legs is not None:
            legs_sprite = self.get_item_sprite(mech.legs)
            leg_attachment = assert_attachment(legs_sprite.attachment)[Attachment.TORSO]

            for layer in (Attachment.LEG_1, Attachment.LEG_2):
                x, y = combine_attachments(leg_attachment, attachments[layer])
                canvas[LAYER_ORDER.index(layer), x, y] = legs_sprite.image

        for item, slot in mech.iter_items("weapons", yield_slots=True):
            if item is None:
                continue

            layer = Attachment.of_name(slot.name)

            item_sprite = self.get_item_sprite(item)
            item_attachment = assert_attachment(item_sprite.attachment)[Attachment.TORSO]
            x, y = combine_attachments(item_attachment, attachments[layer])
            canvas[LAYER_ORDER.index(layer), x, y] = item_sprite.image

        if mech.drone is not None:
            drone_sprite = self.get_item_sprite(mech.drone)
            drone_image = drone_sprite.image
            x = drone_image.width // 2 + canvas.offsets.left
            y = drone_image.height + 25 + canvas.offsets.above
            canvas[-1, -x, -y] = drone_image

        return canvas.merge(LAYER_ORDER.index("torso"))
