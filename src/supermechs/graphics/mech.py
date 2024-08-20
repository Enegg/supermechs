import typing
from collections import abc

from attrs import define, field

from .joints import JointLayer, JointLayerType, Joints

from supermechs.item import Item
from supermechs.mech import Mech
from supermechs.typeshed import T
from supermechs.utils import KeyAccessor

__all__ = ("MechGFX", "get_mech_gfx")

SpriteType: typing.TypeAlias = T | None
SpriteAccessor: typing.TypeAlias = KeyAccessor[JointLayer, SpriteType[T]]


@define
class JointData:
    joints: Joints


@define
class MechGFX(typing.Generic[T]):
    scale: float = 1.0
    _setup: abc.MutableMapping[JointLayerType, SpriteType[T]] = field(factory=dict, init=False)

    # fmt: off
    hat       = SpriteAccessor[T](JointLayer.HAT)
    drone     = SpriteAccessor[T](JointLayer.DRONE)
    torso     = SpriteAccessor[T](JointLayer.TORSO)
    right_leg = SpriteAccessor[T](JointLayer.RIGHT_LEG)
    left_leg  = SpriteAccessor[T](JointLayer.LEFT_LEG)
    # fmt: on

    def __setitem__(self, slot: JointLayerType, sprite: SpriteType[T], /) -> None:
        if sprite is None:
            del self[slot]

        else:
            self._setup[slot] = sprite

    def __getitem__(self, slot: JointLayerType, /) -> SpriteType[T]:
        return self._setup.get(slot)

    def __delitem__(self, slot: JointLayerType, /) -> None:
        self._setup.pop(slot, None)


def get_mech_gfx(mech: Mech, get_sprite: abc.Callable[[Item], T]) -> MechGFX[T]:  # noqa: C901
    gfx = MechGFX[T]()

    if mech.torso is not None:
        gfx.torso = get_sprite(mech.torso)

    if mech.legs is not None:
        gfx.left_leg = gfx.right_leg = get_sprite(mech.legs)

    for iterator, left_joint, right_joint in (
        (mech.side_weapons, JointLayer.LEFT_SIDE_WEAPON, JointLayer.RIGHT_SIDE_WEAPON),
        (mech.top_weapons, JointLayer.LEFT_TOP_WEAPON, JointLayer.RIGHT_TOP_WEAPON),
    ):
        for i, item in enumerate(iterator()):
            if item is None:
                continue

            joint = right_joint if i % 2 else left_joint

            gfx[joint, i // 2] = get_sprite(item)

    if mech.drone is not None:
        gfx.drone = get_sprite(mech.drone)

    if mech.perk is not None:
        # TODO: distinguishing perk types
        if "is_torso":
            gfx.torso = get_sprite(mech.perk)

        elif "is_hat":
            gfx.hat = get_sprite(mech.perk)

        elif "makes_small":
            gfx.scale = 0.5

        elif "makes_big":
            gfx.scale = 1.5

        else:
            msg = "Unknown perk kind"
            raise ValueError(msg)

    return gfx
