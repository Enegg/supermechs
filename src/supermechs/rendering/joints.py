from collections import abc
from enum import auto, unique
from typing import NamedTuple, TypeAlias

from ..item import Type
from ..utils import PartialEnum

__all__ = ("JointLayer", "Joints", "Point2D", "align_joints")


@unique
class JointLayer(int, PartialEnum):
    """Enumeration of joint layers."""

    JUMP_JETS = auto()
    SIDE_WEAPON_2 = auto()
    SIDE_WEAPON_4 = auto()
    TOP_WEAPON_2 = auto()
    LEG_2 = auto()
    CHARGE = auto()
    TORSO = auto()
    HAT = auto()
    DRONE = auto()
    LEG_1 = auto()
    TOP_WEAPON_1 = auto()
    SIDE_WEAPON_1 = auto()
    SIDE_WEAPON_3 = auto()


class Point2D(NamedTuple):
    x: float = 0
    y: float = 0


Joints: TypeAlias = abc.Mapping[JointLayer, Point2D]


def create_synthetic_joints(width: int, height: int, type: Type) -> Joints:
    """Create a joint off given image size.

    Note: likely won't work well for scope-like items.

    https://github.com/ctrlraul/supermechs-workshop/blob/6fe2e0a29bd4776f50f893d2ab0722020279e2d3/src/items/ItemsManager.ts#L286-L325
    """
    if type is Type.TORSO:
        # fmt: off
        return {
            JointLayer.LEG_1:         Point2D(width * 0.40, height * 0.9),
            JointLayer.LEG_2:         Point2D(width * 0.80, height * 0.9),
            JointLayer.SIDE_WEAPON_1: Point2D(width * 0.25, height * 0.6),
            JointLayer.SIDE_WEAPON_2: Point2D(width * 0.75, height * 0.6),
            JointLayer.SIDE_WEAPON_3: Point2D(width * 0.20, height * 0.3),
            JointLayer.SIDE_WEAPON_4: Point2D(width * 0.80, height * 0.3),
            JointLayer.TOP_WEAPON_1:  Point2D(width * 0.25, height * 0.1),
            JointLayer.TOP_WEAPON_2:  Point2D(width * 0.75, height * 0.1),
            JointLayer.HAT:           Point2D(width * 0.50, height * 0.1),
            JointLayer.CHARGE:        Point2D(width * 0.10, height * 0.5),
        }
        # fmt: on

    if type is Type.LEGS:
        # fmt: off
        return {
            JointLayer.TORSO:     Point2D(width * 0.5, height * 0.1),
            # not all legs can jump but whatever
            JointLayer.JUMP_JETS: Point2D(width * 0.5, height),
        }
        # fmt: on

    if type is Type.SIDE_WEAPON:
        return {JointLayer.TORSO: Point2D(width * 0.3, height * 0.5)}

    if type is Type.TOP_WEAPON:
        return {JointLayer.TORSO: Point2D(width * 0.3, height * 0.8)}

    return {}


def align_joints(torso_joint: Point2D, item_joint: Point2D) -> Point2D:
    return Point2D(item_joint.x - torso_joint.x, item_joint.y - torso_joint.y)
