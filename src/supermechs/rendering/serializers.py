import typing as t

import anyio

from ..enums import Type
from ..errors import MalformedData
from ..typedefs import (
    ID,
    AnyItemDict,
    AnyItemPack,
    AnyRawAttachment,
    ItemDictVer1,
    ItemDictVer2,
    ItemDictVer3,
    RawPoint2D,
    RawTorsoAttachments,
)
from ..typeshed import Coro
from ..utils import assert_type, js_format
from .attachments import (
    AnyAttachment,
    Point2D,
    TorsoAttachments,
    create_synthetic_attachment,
    is_attachable,
)
from .pack_renderer import PackRenderer, crop_from_spritesheet
from .sprites import ItemSprite

if t.TYPE_CHECKING:
    from PIL.Image import Image

ImageFetcher = t.Callable[[str], Coro["Image"]]


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


def oneshot(
    item_dict: AnyItemDict, image: "Image", sprites: t.MutableMapping[ID, ItemSprite]
) -> None:
    width = item_dict.get("width", image.width)
    height = item_dict.get("height", image.height)

    if image.mode != "RGBA":
        image = image.convert("RGBA")

    if image.size != (width, height):
        image = image.resize((width, height))

    attachment = to_attachments(item_dict.get("attachment"))
    type = Type[item_dict["type"]]
    sprite = ItemSprite(image, attachment)

    if attachment is None and is_attachable(type):
        sprite.attachment = create_synthetic_attachment(*image.size, type)

    sprites[item_dict["id"]] = sprite


async def to_pack_renderer(data: AnyItemPack, /, fetch: ImageFetcher) -> PackRenderer:
    """Create an instance of the class by fetching all images."""

    if "version" not in data or data["version"] == "1":
        key = assert_type(str, data["config"]["key"])
        base_url = assert_type(str, data["config"]["base_url"])

        results: list[tuple[AnyItemDict, Image]] = []

        async def async_worker(item_dict: ItemDictVer1) -> None:
            image = await fetch(js_format(assert_type(str, item_dict["image"]), url=base_url))
            results.append((item_dict, image))

        async with anyio.create_task_group() as tg:
            for item_dict in data["items"]:
                tg.start_soon(async_worker, item_dict)

        del base_url
        sprites: dict[ID, ItemSprite] = {}

        async with anyio.create_task_group() as tg:
            for item_dict, image in results:
                tg.start_soon(anyio.to_thread.run_sync, oneshot, item_dict, image, sprites)

        del results

    elif data["version"] in ("2", "3"):
        key = assert_type(str, data["key"])
        spritessheet_url = assert_type(str, data["spritesSheet"])
        spritessheet_map = data["spritesMap"]

        spritessheet = await fetch(spritessheet_url)
        del spritessheet_url
        sprites: dict[ID, ItemSprite] = {}

        def sprite_creator(item_dict: ItemDictVer2 | ItemDictVer3) -> None:
            sheet_key = assert_type(str, item_dict["name"]).replace(" ", "")
            image = crop_from_spritesheet(spritessheet, spritessheet_map[sheet_key])
            oneshot(item_dict, image, sprites)

        async with anyio.create_task_group() as tg:
            for item_dict in data["items"]:
                tg.start_soon(anyio.to_thread.run_sync, sprite_creator, item_dict)

        del spritessheet_map

    else:
        raise ValueError(f"Unknown pack version: {data['version']}")

    self = PackRenderer(key, sprites)
    # LOGGER.info(f"Pack {key!r} loaded {len(sprites)} sprites")
    return self
