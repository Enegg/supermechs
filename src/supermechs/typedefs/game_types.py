from __future__ import annotations

import typing as t

# fmt: off
__all__ = (
    "LiteralType", "LiteralElement",
    "AnyMechStatKey", "AnyStatKey",
    "RawMechStatsMapping", "RawStatsMapping",
)
# fmt: on

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

# fmt: off
AnyMechStatKey = t.Literal[
    "weight", "health",
    "eneCap", "eneReg",
    "heaCap", "heaCol",
    "phyRes", "expRes", "eleRes",
    "bulletsCap", "rocketsCap",
    "walk", "jump"
]
AnyStatKey = AnyMechStatKey | t.Literal[
    "phyDmg", "phyResDmg",
    "expDmg", "heaDmg", "heaCapDmg", "heaColDmg", "expResDmg",
    "eleDmg", "eneDmg", "eneCapDmg", "eneRegDmg", "eleResDmg",
    "range", "push", "pull", "recoil", "retreat", "advance",
    "uses", "backfire", "heaCost", "eneCost", "bulletsCost", "rocketsCost"
]
# fmt: on


class RawMechStatsMapping(t.TypedDict, total=False):
    """Data as received from source."""

    weight: int | None
    health: int | None
    eneCap: int | None
    eneReg: int | None
    heaCap: int | None
    heaCol: int | None
    phyRes: int | None
    expRes: int | None
    eleRes: int | None
    bulletsCap: int | None
    rocketsCap: int | None
    walk: int | None
    jump: int | None


class RawStatsMapping(RawMechStatsMapping, total=False):
    """Data as received from source."""

    phyDmg: list[int | None]
    phyResDmg: int | None
    eleDmg: list[int | None]
    eneDmg: int | None
    eneCapDmg: int | None
    eneRegDmg: int | None
    eleResDmg: int | None
    expDmg: list[int | None]
    heaDmg: int | None
    heaCapDmg: int | None
    heaColDmg: int | None
    expResDmg: int | None
    # walk, jump
    range: list[int | None]
    push: int | None
    pull: int | None
    recoil: int | None
    advance: int | None
    retreat: int | None
    uses: int | None
    backfire: int | None
    heaCost: int | None
    eneCost: int | None
    bulletsCost: int | None
    rocketsCost: int | None
