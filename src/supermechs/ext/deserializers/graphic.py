import typing as t
import typing_extensions as tex
from functools import partial

from attrs import define, field

from .errors import DataError, DataVersionError
from .typedefs import AnyItemDict, AnyItemPack, ItemPackVer1, ItemPackVer2, ItemPackVer3
from .typedefs.graphics import AnyRawAttachment, RawBox2D, RawPoint2D, RawTorsoAttachments
from .utils import js_format

from supermechs.item import Tier, Type
from supermechs.rendering import (
    AnyAttachment,
    Attachment,
    AttachmentMapping,
    ItemSprite,
    Metadata,
    Point2D,
    create_synthetic_attachments,
    is_attachable,
)
from supermechs.typeshed import ID, T
from supermechs.ext.deserializers.utils import assert_type

if t.TYPE_CHECKING:
    from PIL.Image import Image

Loader: t.TypeAlias = t.Callable[[Metadata], t.Awaitable[T]]
Cropper: t.TypeAlias = t.Callable[[T, int, int, int, int], T]
SpriteMapping: t.TypeAlias = t.Mapping[tuple[ID, Tier], ItemSprite[T]]
ConverterFactory: t.TypeAlias = t.Callable[[AnyItemDict], t.Callable[[ItemSprite[T]], None]]

KEY_TO_ENUM = {
    "leg1": Attachment.LEG_1,
    "leg2": Attachment.LEG_2,
    "side1": Attachment.SIDE_WEAPON_1,
    "side2": Attachment.SIDE_WEAPON_2,
    "side3": Attachment.SIDE_WEAPON_3,
    "side4": Attachment.SIDE_WEAPON_4,
    "top1": Attachment.TOP_WEAPON_1,
    "top2": Attachment.TOP_WEAPON_2,
}


@define
class SpriteResolver(ItemSprite[T]):
    loader: t.Final[Loader[T]]
    metadata: t.Final[Metadata]
    attachment: AnyAttachment
    postprocess: t.Callable[[tex.Self], None] | None = None
    _image: T | None = field(default=None, init=False)

    @property
    @tex.override
    def image(self) -> T:
        if self._image is None:
            msg = "Resource not loaded"
            raise RuntimeError(msg)
        return self._image

    @image.setter
    def image(self, image: T, /) -> None:
        self._image = image

    @image.deleter
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
class SpritesheetResolver(ItemSprite[T]):
    spritesheet: t.Final[ItemSprite[T]]
    rect: t.Final[tuple[int, int, int, int]]
    attachment: AnyAttachment
    crop: Cropper[T]
    postprocess: t.Callable[[tex.Self], None] | None = None
    _image: T | None = field(default=None, init=False)

    @property
    @tex.override
    def metadata(self) -> Metadata:
        sheet_meta = self.spritesheet.metadata
        return Metadata(sheet_meta.source, "sheet", sheet_meta.value)

    @property
    @tex.override
    def image(self) -> T:
        if self._image is None:
            raise RuntimeError("Resource not loaded")  # noqa: EM101
        return self._image

    @image.setter
    def image(self, image: T, /) -> None:
        self._image = image

    @image.deleter
    def image(self) -> None:
        self._image = None

    @tex.override
    async def load(self) -> None:
        # TODO: Implement locks
        if self._image is not None:
            return

        await self.spritesheet.load()

        self._image = self.crop(self.spritesheet.image, *self.rect)

        if self.postprocess is not None:
            self.postprocess(self)


def to_point2d(data: RawPoint2D, /) -> Point2D:
    return Point2D(assert_type(int, data["x"]), assert_type(int, data["y"]))


def to_torso_attachments(data: RawTorsoAttachments, /) -> AttachmentMapping:
    return {KEY_TO_ENUM[key]: to_point2d(mapping) for key, mapping in data.items()}


def to_attachments(data: AnyRawAttachment, /) -> AnyAttachment:
    match data:
        case {"x": int() as x, "y": int() as y}:
            return {Attachment.TORSO: Point2D(x, y)}

        case {
            "leg1": {},
            "leg2": {},
            "side1": {},
            "side2": {},
            "side3": {},
            "side4": {},
            "top1": {},
            "top2": {},
        }:
            return to_torso_attachments(data)

        case None:
            return None

        case _:
            raise DataError


def bounding_box(pos: RawBox2D, /) -> tuple[int, int, int, int]:
    x = assert_type(int, pos["x"])
    y = assert_type(int, pos["y"])
    w = assert_type(int, pos["width"])
    h = assert_type(int, pos["height"])
    return (x, y, x + w, y + h)


def to_sprite_mapping(
    data: AnyItemPack,
    /,
    fetch: Loader[T],
    converter_factory: ConverterFactory[T],
    cropper: Cropper[T],
) -> SpriteMapping[T]:
    """Parse data into an instance primed with item sprites."""

    if "version" not in data or data["version"] == "1":
        return parse_individual_sprites(data, fetch, converter_factory)

    elif data["version"] in ("2", "3"):
        return parse_spritessheet(data, fetch, converter_factory, cropper)

    else:
        raise DataVersionError(data["version"], "3")


def make_converter(
    func: t.Callable[[int, int, Type, ItemSprite[T]], None], /
) -> ConverterFactory[T]:
    """Decorator aiming to ease converting sprites.

    Decorated function should accept sprite width, height, item Type, and the sprite to convert.
    """

    def inner(data: AnyItemDict, /) -> t.Callable[[ItemSprite[T]], None]:
        width = assert_type(int, data.get("width", 0))
        height = assert_type(int, data.get("height", 0))
        type = Type.of_name(data["type"])

        return partial(func, width, height, type)

    return inner


@make_converter
def convert(width: int, height: int, type: Type, sprite: ItemSprite["Image"], /) -> None:
    image = sprite.image

    if image.mode != "RGBA":
        image = image.convert("RGBA")

    size = (width or image.width, height or image.height)

    if image.size != size:
        image = image.resize(size)

    sprite.image = image

    if sprite.attachment is None and is_attachable(type):
        sprite.attachment = create_synthetic_attachments(*size, type)



def parse_individual_sprites(
    data: ItemPackVer1, /, fetch: Loader[T], converter_factory: ConverterFactory[T]
) -> SpriteMapping[T]:
    base_url = assert_type(str, data["config"]["base_url"])
    sprites: SpriteMapping[T] = {}

    for item_dict in data["items"]:
        img_url = js_format(assert_type(str, item_dict["image"]), url=base_url)
        attachment = to_attachments(item_dict.get("attachment"))
        converter = converter_factory(item_dict)
        meta = Metadata("url", "single", img_url)
        sprite = SpriteResolver(fetch, meta, attachment, converter)

        item_id = assert_type(int, item_dict["id"])
        max_tier = Tier.of_initial(assert_type(str, item_dict["transform_range"])[-1])

        if max_tier is Tier.DIVINE:
            sprites[item_id, Tier.MYTHICAL] = sprite

        sprites[item_id, max_tier] = sprite

    return sprites


def parse_spritessheet(
    data: ItemPackVer2 | ItemPackVer3,
    /,
    fetch: Loader[T],
    converter_factory: ConverterFactory[T],
    cropper: Cropper[T],
) -> SpriteMapping[T]:
    spritesheet_url = assert_type(str, data["spritesSheet"])
    spritesheet_map = data["spritesMap"]
    sheet_meta = Metadata("url", "single", spritesheet_url)
    spritesheet = SpriteResolver(fetch, sheet_meta, None)
    sprites: SpriteMapping[T] = {}

    for item_dict in data["items"]:
        attachment = to_attachments(item_dict.get("attachment"))
        sheet_key = assert_type(str, item_dict["name"]).replace(" ", "")
        rect = bounding_box(spritesheet_map[sheet_key])
        converter = converter_factory(item_dict)
        sprite = SpritesheetResolver(spritesheet, rect, attachment, cropper, converter)

        item_id = assert_type(int, item_dict["id"])
        max_tier = Tier.of_initial(assert_type(str, item_dict["transform_range"])[-1])

        if max_tier is Tier.DIVINE:
            sprites[item_id, Tier.MYTHICAL] = sprite

        sprites[item_id, max_tier] = sprite

    return sprites
