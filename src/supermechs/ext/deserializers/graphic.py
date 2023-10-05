import typing as t

from .typedefs.graphics import AnyRawAttachment, RawPlane2D, RawPoint2D, RawTorsoAttachments
from .typedefs.packs import AnyItemPack, ItemPackVer1, ItemPackVer2, ItemPackVer3
from .utils import js_format

from supermechs.errors import MalformedData, UnknownDataVersion
from supermechs.models.item import Type
from supermechs.rendering import (
    AnyAttachment,
    Attachment,
    AttachmentMapping,
    ItemSprite,
    Metadata,
    PackRenderer,
    Point2D,
    SingleResolver,
    SpritesheetResolver,
    create_synthetic_attachments,
    is_attachable,
)
from supermechs.utils import assert_type

if t.TYPE_CHECKING:
    from PIL.Image import Image

    from supermechs.typedefs import ID

ImageFetcher = t.Callable[[Metadata], t.Awaitable["Image"]]


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

        case unknown:
            raise MalformedData("Invalid attachment", unknown)


def bounding_box(pos: RawPlane2D, /) -> tuple[int, int, int, int]:
    x, y, w, h = pos["x"], pos["y"], pos["width"], pos["height"]
    return (x, y, x + w, y + h)


def to_pack_renderer(data: AnyItemPack, /, fetch: ImageFetcher) -> PackRenderer:
    """Parse data into an instance primed with item sprites."""

    if "version" not in data or data["version"] == "1":
        return to_pack_renderer_v1(data, fetch)

    elif data["version"] in ("2", "3"):
        return to_pack_renderer_v2(data, fetch)

    else:
        raise UnknownDataVersion(PackRenderer, data["version"])


def make_converter(width: int, height: int, type: Type) -> t.Callable[[ItemSprite], None]:
    def converter(sprite: ItemSprite, /) -> None:
        image = sprite.image

        if image.mode != "RGBA":
            image = image.convert("RGBA")

        w = width or image.width
        h = height or image.height

        if image.size != (w, h):
            image = image.resize((w, h))

        sprite.image = image

        if sprite.attachment is None and is_attachable(type):
            sprite.attachment = create_synthetic_attachments(w, h, type)

    return converter


def to_pack_renderer_v1(data: ItemPackVer1, /, fetch: ImageFetcher) -> PackRenderer:
    key = assert_type(str, data["config"]["key"])
    base_url = assert_type(str, data["config"]["base_url"])
    sprites: dict[ID, ItemSprite] = {}

    for item_dict in data["items"]:
        img_url = js_format(assert_type(str, item_dict["image"]), url=base_url)
        attachment = to_attachments(item_dict.get("attachment"))
        converter = make_converter(
            item_dict.get("width", 0),
            item_dict.get("height", 0),
            Type.of_name(item_dict["type"]),
        )
        meta = Metadata("url", "single", img_url)
        sprite = SingleResolver(fetch, meta, attachment, converter)
        sprites[item_dict["id"]] = sprite

    return PackRenderer(key, sprites)


def to_pack_renderer_v2(data: ItemPackVer2 | ItemPackVer3, /, fetch: ImageFetcher) -> PackRenderer:
    key = assert_type(str, data["key"])
    spritesheet_url = assert_type(str, data["spritesSheet"])
    spritesheet_map = data["spritesMap"]
    sheet_meta = Metadata("url", "single", spritesheet_url)
    spritesheet = SingleResolver(fetch, sheet_meta, None)
    sprites: dict[ID, ItemSprite] = {}

    for item_dict in data["items"]:
        attachment = to_attachments(item_dict.get("attachment"))
        sheet_key = assert_type(str, item_dict["name"]).replace(" ", "")
        rect = bounding_box(spritesheet_map[sheet_key])
        converter = make_converter(
            item_dict.get("width", 0),
            item_dict.get("height", 0),
            Type.of_name(item_dict["type"]),
        )
        sprite = SpritesheetResolver(spritesheet, rect, attachment, converter)
        sprites[item_dict["id"]] = sprite

    return PackRenderer(key, sprites)
