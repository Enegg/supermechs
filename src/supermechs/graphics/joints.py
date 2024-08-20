from collections import abc
from enum import auto, unique
from typing import Literal, NamedTuple, TypeAlias

from supermechs.enums._base import PartialEnum

__all__ = ("JointLayer", "Joints", "Point2D", "align_joints")


@unique
class JointLayer(int, PartialEnum):
    """Enumeration of joint layers."""

    JUMP_JETS = auto()
    LEFT_SIDE_WEAPON = auto()
    LEFT_TOP_WEAPON = auto()
    LEFT_LEG = auto()
    CHARGE = auto()
    TORSO = auto()
    HAT = auto()
    DRONE = auto()
    RIGHT_LEG = auto()
    RIGHT_TOP_WEAPON = auto()
    RIGHT_SIDE_WEAPON = auto()


class Point2D(NamedTuple):
    x: float = 0
    y: float = 0


VariadicJoint: TypeAlias = Literal[
    JointLayer.LEFT_SIDE_WEAPON,
    JointLayer.LEFT_TOP_WEAPON,
    JointLayer.RIGHT_SIDE_WEAPON,
    JointLayer.RIGHT_TOP_WEAPON,
]
JointLayerType: TypeAlias = JointLayer | tuple[VariadicJoint, int]
Joints: TypeAlias = abc.Mapping[JointLayerType, Point2D]


def align_joints(torso_joint: Point2D, item_joint: Point2D) -> Point2D:
    return Point2D(item_joint.x - torso_joint.x, item_joint.y - torso_joint.y)
