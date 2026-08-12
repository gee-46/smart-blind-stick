"""
Direction estimation.

Divides the camera frame horizontally into LEFT | CENTER | RIGHT regions
and classifies an object by where its bounding-box center falls. Region
boundaries are configurable fractions of frame width (see
`ai_vision/config.py`), not hardcoded here.
"""
from __future__ import annotations

from ai_vision.schemas.detection import BoundingBox, Direction


def estimate_direction(
    bbox: BoundingBox,
    frame_width: int,
    left_boundary: float = 0.33,
    right_boundary: float = 0.66,
) -> Direction:
    """
    Classify direction from a bbox's horizontal center.

    `left_boundary` / `right_boundary` are fractions of `frame_width`
    (0.0-1.0). Centers below `left_boundary * frame_width` are LEFT,
    centers above `right_boundary * frame_width` are RIGHT, everything
    else is CENTER.
    """
    if frame_width <= 0:
        raise ValueError("frame_width must be > 0")
    if not (0.0 <= left_boundary < right_boundary <= 1.0):
        raise ValueError("Require 0.0 <= left_boundary < right_boundary <= 1.0")

    center_x_fraction = bbox.center_x / frame_width
    if center_x_fraction < left_boundary:
        return Direction.LEFT
    if center_x_fraction > right_boundary:
        return Direction.RIGHT
    return Direction.CENTER
