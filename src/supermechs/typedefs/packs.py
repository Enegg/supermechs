import typing as t

from typing_extensions import NotRequired

from ..typeshed import LiteralURL
from .game_types import LiteralElement, LiteralType, RawStatsMapping
from .graphics import RawPlane2D, RawPoint2D, RawTorsoAttachments

# fmt: off
__all__ = (
    "TiersMixin",
    "ItemDictVer1", "ItemPackVer1",
    "ItemDictVer2", "ItemPackVer2",
    "ItemDictVer3", "ItemPackVer3",
    "AnyItemDict", "AnyItemPack"
)
# fmt: on

LiteralTag = t.Literal["sword", "melee", "roller"]


class TiersMixin(t.TypedDict, total=False):
    common: RawStatsMapping
    max_common: RawStatsMapping
    rare: RawStatsMapping
    max_rare: RawStatsMapping
    epic: RawStatsMapping
    max_epic: RawStatsMapping
    legendary: RawStatsMapping
    max_legendary: RawStatsMapping
    mythical: RawStatsMapping
    max_mythical: RawStatsMapping
    divine: RawStatsMapping


class SpritesSheetMixin(t.TypedDict):
    spritesSheet: LiteralURL
    spritesMap: dict[str, RawPlane2D]


class ItemDictBase(t.TypedDict):
    id: int
    name: str
    type: LiteralType
    element: LiteralElement
    transform_range: str
    tags: NotRequired[list[LiteralTag]]
    width: NotRequired[int]
    height: NotRequired[int]
    attachment: NotRequired[RawPoint2D | RawTorsoAttachments]


# -------------------------------------- v1 --------------------------------------
# https://gist.githubusercontent.com/ctrlraul/3b5669e4246bc2d7dc669d484db89062/raw
# "version": "1" or non-existent
# "config" with "base_url"
# "image" per item (usually name without spaces + .png)


class ItemDictVer1(ItemDictBase):
    stats: RawStatsMapping
    image: str


class ConfigVer1(t.TypedDict):
    key: str
    name: str
    description: str
    base_url: LiteralURL


class ItemPackVer1(t.TypedDict):
    version: NotRequired[t.Literal["1"]]
    config: ConfigVer1
    items: list[ItemDictVer1]


# -------------------------------------- v2 --------------------------------------
# https://gist.githubusercontent.com/ctrlraul/22b71089a0dd7fef81e759dfb3dda67b/raw
# "version": "2"
# no "config"
# spritesheets


class ItemDictVer2(ItemDictBase):
    stats: RawStatsMapping


class ItemPackVer2(SpritesSheetMixin):
    version: t.Literal["2"]
    key: str
    name: str
    description: str
    items: list[ItemDictVer2]


# -------------------------------------- v3 --------------------------------------
# https://raw.githubusercontent.com/Enegg/Item-packs/master/items.json
# "version": "3" or "standalone"
# lacks tags and attachments


class ItemDictVer3(ItemDictBase, TiersMixin):
    pass


class ItemPackVer3(SpritesSheetMixin):
    version: t.Literal["3"]
    key: str
    name: str
    description: str
    items: list[ItemDictVer3]


AnyItemDict = ItemDictVer1 | ItemDictVer2 | ItemDictVer3
AnyItemPack = ItemPackVer1 | ItemPackVer2 | ItemPackVer3
