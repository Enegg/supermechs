from typing import Literal, TypeAlias

from typing_extensions import NotRequired, TypedDict

from .graphics import ItemImageParams, SpritesSheetMixin

from supermechs.typeshed import LiteralURL

__all__ = (
    "AnyItemDict",
    "AnyItemPack",
    "ItemDictVer1",
    "ItemDictVer2",
    "ItemDictVer3",
    "ItemPackVer1",
    "ItemPackVer2",
    "ItemPackVer3",
    "PackMetadata",
    "RawStatsMapping",
)

LiteralTag: TypeAlias = Literal["sword", "melee", "roller"]
LiteralType: TypeAlias = Literal[
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
LiteralElement: TypeAlias = Literal["PHYSICAL", "EXPLOSIVE", "ELECTRIC", "COMBINED"]
_nint: TypeAlias = int | None


class RawStatsMapping(TypedDict, total=False):
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


class ItemDictBase(ItemImageParams):
    id: int
    name: str
    type: LiteralType
    element: LiteralElement
    transform_range: str
    tags: NotRequired[list[LiteralTag]]


class PackMetadata(TypedDict):
    key: str
    name: str
    description: str


# ----------------------------------------------- v1 -----------------------------------------------


class ItemDictVer1(ItemDictBase):
    stats: RawStatsMapping
    image: str


class ConfigVer1(PackMetadata):
    base_url: LiteralURL


class ItemPackVer1(TypedDict):
    version: NotRequired[Literal["1"]]
    config: ConfigVer1
    items: list[ItemDictVer1]


# ----------------------------------------------- v2 -----------------------------------------------


class ItemDictVer2(ItemDictBase):
    stats: RawStatsMapping


class ItemPackVer2(PackMetadata, SpritesSheetMixin):
    version: Literal["2"]
    items: list[ItemDictVer2]


# ----------------------------------------------- v3 -----------------------------------------------


class ItemDictVer3(ItemDictBase, total=False):
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


class ItemPackVer3(PackMetadata, SpritesSheetMixin):
    version: Literal["3"]
    items: list[ItemDictVer3]


AnyItemDict: TypeAlias = ItemDictVer1 | ItemDictVer2 | ItemDictVer3
AnyItemPack: TypeAlias = ItemPackVer1 | ItemPackVer2 | ItemPackVer3
