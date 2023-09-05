import typing as t

from .typedefs.graphics import AnyRawAttachment, RawPlane2D, RawPoint2D, RawTorsoAttachments
from .typedefs.packs import AnyItemPack, ItemPackVer1, ItemPackVer2, ItemPackVer3
from .utils import js_format

from supermechs.enums import Type
from supermechs.errors import MalformedData
from supermechs.rendering import (
    AnyAttachment,
    ItemSprite,
    PackRenderer,
    Point2D,
    SingleResolver,
    SpritesheetResolver,
    TorsoAttachments,
    create_synthetic_attachment,
    is_attachable,
)
from supermechs.typedefs import ID
from supermechs.utils import assert_type

if t.TYPE_CHECKING:
    from PIL.Image import Image

ImageFetcher = t.Callable[[str], t.Awaitable["Image"]]


def to_point2d(data: RawPoint2D, /) -> Point2D:
    return Point2D(assert_type(int, data["x"]), assert_type(int, data["y"]))


def to_torso_attachments(data: RawTorsoAttachments, /) -> TorsoAttachments:
    return {key: to_point2d(mapping) for key, mapping in data.items()}


def to_attachments(data: AnyRawAttachment, /) -> AnyAttachment:
    match data:
        case {"x": int() as x, "y": int() as y}:
            return Point2D(x, y)

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
    """Create an instance of the class by fetching all images."""

    if "version" not in data or data["version"] == "1":
        return to_pack_renderer_v1(data, fetch)

    elif data["version"] in ("2", "3"):
        return to_pack_renderer_v2(data, fetch)

    else:
        raise ValueError(f"Unknown pack version: {data['version']}")


def make_converter(width: int, height: int, type: Type) -> t.Callable[[ItemSprite[str]], None]:
    def converter(sprite: ItemSprite[str], /) -> None:
        image = sprite.image

        if image.mode != "RGBA":
            image = image.convert("RGBA")

        w = width or image.width
        h = height or image.height

        if image.size != (w, h):
            image = image.resize((w, h))

        sprite.image = image

        if sprite.attachment is None and is_attachable(type):
            sprite.attachment = create_synthetic_attachment(w, h, type)

    return converter


def to_pack_renderer_v1(data: ItemPackVer1, /, fetch: ImageFetcher) -> PackRenderer:
    key = assert_type(str, data["config"]["key"])
    base_url = assert_type(str, data["config"]["base_url"])

    sprites: dict[ID, ItemSprite[str]] = {}

    for item_dict in data["items"]:
        img_url = js_format(assert_type(str, item_dict["image"]), url=base_url)
        attachment = to_attachments(item_dict.get("attachment"))
        converter = make_converter(
            item_dict.get("width", 0),
            item_dict.get("height", 0),
            Type.of_name(item_dict["type"])
        )
        sprite = SingleResolver(fetch, img_url, attachment, converter)
        sprites[item_dict["id"]] = sprite

    return PackRenderer(key, sprites)


def to_pack_renderer_v2(data: ItemPackVer2 | ItemPackVer3, /, fetch: ImageFetcher) -> PackRenderer:
    key = assert_type(str, data["key"])
    spritesheet_url = assert_type(str, data["spritesSheet"])
    spritesheet_map = data["spritesMap"]
    spritesheet = SingleResolver(fetch, spritesheet_url, None)
    sprites: dict[ID, ItemSprite[str]] = {}

    for item_dict in data["items"]:
        attachment = to_attachments(item_dict.get("attachment"))
        sheet_key = assert_type(str, item_dict["name"]).replace(" ", "")
        rect = bounding_box(spritesheet_map[sheet_key])
        converter = make_converter(
            item_dict.get("width", 0),
            item_dict.get("height", 0),
            Type.of_name(item_dict["type"])
        )
        sprite = SpritesheetResolver(spritesheet, rect, attachment, converter)
        sprites[item_dict["id"]] = sprite

    return PackRenderer(key, sprites)
