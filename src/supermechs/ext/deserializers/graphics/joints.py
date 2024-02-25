from collections import abc

from ..errors import DataError
from ..typedefs.graphics import (
    AnyRawAttachment,
    RawPoint2D,
    RawTorsoAttachments,
)
from ..utils import assert_key

from supermechs.enums.item import Type
from supermechs.graphics.joints import JointLayer, JointLayerType, Joints, Point2D

__all__ = ("create_synthetic_joints", "to_point2d", "to_torso_joints")


def to_point2d(data: RawPoint2D, /) -> Point2D:
    return Point2D(
        assert_key(int, data, "x"),
        assert_key(int, data, "y"),
    )


_KEY_TO_JOINT: abc.Mapping[str, JointLayerType] = {
    "leg1": JointLayer.RIGHT_LEG,
    "leg2": JointLayer.LEFT_LEG,
    "side1": (JointLayer.RIGHT_SIDE_WEAPON, 0),
    "side3": (JointLayer.RIGHT_SIDE_WEAPON, 1),
    "side2": (JointLayer.LEFT_SIDE_WEAPON, 0),
    "side4": (JointLayer.LEFT_SIDE_WEAPON, 1),
    "top1": (JointLayer.RIGHT_TOP_WEAPON, 0),
    "top2": (JointLayer.LEFT_TOP_WEAPON, 0),
}


def to_torso_joints(data: RawTorsoAttachments, /) -> Joints:
    return {_KEY_TO_JOINT[key]: to_point2d(mapping) for key, mapping in data.items()}


def to_joints(data: AnyRawAttachment, /) -> Joints:
    match data:
        case {"x": int() as x, "y": int() as y}:
            return {JointLayer.TORSO: Point2D(x, y)}

        case None:
            return {}

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
            return to_torso_joints(data)

        case _:
            raise DataError


def create_synthetic_joints(width: int, height: int, type: Type) -> Joints:
    """Create a joint off given image size.

    Note: likely won't work well for scope-like items.

    https://github.com/ctrlraul/supermechs-workshop/blob/6fe2e0a29bd4776f50f893d2ab0722020279e2d3/src/items/ItemsManager.ts#L286-L325
    """
    if type is Type.TORSO:
        return {
            JointLayer.RIGHT_LEG:              Point2D(width * 0.40, height * 0.9),
            JointLayer.LEFT_LEG:               Point2D(width * 0.80, height * 0.9),
            (JointLayer.RIGHT_SIDE_WEAPON, 0): Point2D(width * 0.25, height * 0.6),
            (JointLayer.RIGHT_SIDE_WEAPON, 1): Point2D(width * 0.20, height * 0.3),
            (JointLayer.LEFT_SIDE_WEAPON, 0):  Point2D(width * 0.75, height * 0.6),
            (JointLayer.LEFT_SIDE_WEAPON, 1):  Point2D(width * 0.80, height * 0.3),
            (JointLayer.RIGHT_TOP_WEAPON, 0):  Point2D(width * 0.25, height * 0.1),
            (JointLayer.LEFT_TOP_WEAPON, 0):   Point2D(width * 0.75, height * 0.1),
            JointLayer.HAT:                    Point2D(width * 0.50, height * 0.1),
            JointLayer.CHARGE:                 Point2D(width * 0.10, height * 0.5),
        }  # fmt: skip

    if type is Type.LEGS:
        return {
            JointLayer.TORSO:     Point2D(width * 0.5, height * 0.1),
            # not all legs can jump but whatever
            JointLayer.JUMP_JETS: Point2D(width * 0.5, height),
        }  # fmt: skip

    if type is Type.SIDE_WEAPON:
        return {JointLayer.TORSO: Point2D(width * 0.3, height * 0.5)}

    if type is Type.TOP_WEAPON:
        return {JointLayer.TORSO: Point2D(width * 0.3, height * 0.8)}

    return {}
