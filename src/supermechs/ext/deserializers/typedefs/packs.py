import typing as t
from typing_extensions import NotRequired

from .graphics import ItemImageParams, RawBox2D

from supermechs.typeshed import LiteralURL

# fmt: off
__all__ = (
    "TiersMixin", "RawStatsMapping",
    "ItemDictVer1", "ItemPackVer1",
    "ItemDictVer2", "ItemPackVer2",
    "ItemDictVer3", "ItemPackVer3",
    "AnyItemDict", "AnyItemPack", "PackMetadata"
)
# fmt: on

LiteralTag = t.Literal["sword", "melee", "roller"]
LiteralType = t.Literal[
    "TORSO",
    "LEGS",
    "DRONE",
    "SIDE_WEAPON",
    "TOP_WEAPON",
    "TELEPORTER",
    "CHARGE_ENGINE",
    "GRAPPLING_HOOK",
    "MODULE",
]
LiteralElement = t.Literal["PHYSICAL", "EXPLOSIVE", "ELECTRIC", "COMBINED"]
_nint = int | None


class RawStatsMapping(t.TypedDict, total=False):
    """Data as received from source."""

    weight: _nint
    health: _nint
    eneCap: _nint
    eneReg: _nint
    heaCap: _nint
    heaCol: _nint
    phyRes: _nint
    expRes: _nint
    eleRes: _nint
    bulletsCap: _nint
    rocketsCap: _nint
    walk: _nint
    jump: _nint
    phyDmg: list[_nint]
    phyResDmg: _nint
    eleDmg: list[_nint]
    eneDmg: _nint
    eneCapDmg: _nint
    eneRegDmg: _nint
    eleResDmg: _nint
    expDmg: list[_nint]
    heaDmg: _nint
    heaCapDmg: _nint
    heaColDmg: _nint
    expResDmg: _nint
    # walk, jump
    range: list[_nint]
    push: _nint
    pull: _nint
    recoil: _nint
    advance: _nint
    retreat: _nint
    uses: _nint
    backfire: _nint
    heaCost: _nint
    eneCost: _nint
    bulletsCost: _nint
    rocketsCost: _nint


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
    spritesMap: dict[str, RawBox2D]


class ItemDictBase(ItemImageParams):
    id: int
    name: str
    type: LiteralType
    element: LiteralElement
    transform_range: str
    tags: NotRequired[list[LiteralTag]]


class PackMetadata(t.TypedDict):
    key: str
    name: str
    description: str


# -------------------------------------- v1 --------------------------------------
# - "config" with "base_url"
# - "image" per item (usually name without spaces + .png)


class ItemDictVer1(ItemDictBase):
    stats: RawStatsMapping
    image: str


class ConfigVer1(PackMetadata):
    base_url: LiteralURL


class ItemPackVer1(t.TypedDict):
    version: NotRequired[t.Literal["1"]]
    config: ConfigVer1
    items: list[ItemDictVer1]


# -------------------------------------- v2 --------------------------------------
# no "config"
# spritesheets


class ItemDictVer2(ItemDictBase):
    stats: RawStatsMapping


class ItemPackVer2(PackMetadata, SpritesSheetMixin):
    version: t.Literal["2"]
    items: list[ItemDictVer2]


# -------------------------------------- v3 --------------------------------------


class ItemDictVer3(ItemDictBase, TiersMixin):
    pass


class ItemPackVer3(PackMetadata, SpritesSheetMixin):
    version: t.Literal["3"]
    items: list[ItemDictVer3]


AnyItemDict = ItemDictVer1 | ItemDictVer2 | ItemDictVer3
AnyItemPack = ItemPackVer1 | ItemPackVer2 | ItemPackVer3
