"""
Monocular distance estimation.

IMPORTANT / HONESTY NOTE (see project spec sections 9 and 22):
YOLO does NOT provide physical distance. This module produces an
*estimate* using the classic pinhole-camera approximation:

    distance_m = (focal_length_px * real_object_height_m) / bbox_height_px

This requires two things that are themselves approximations:
  1. `focal_length_px` -- a property of the specific physical camera,
     obtained by calibration (see `calibrate_focal_length` below). The
     default in `config.py` is a placeholder and MUST be re-calibrated
     for the actual hardware camera before distances are trusted.
  2. `real_object_height_m` -- an assumed *average* real-world height
     for the object's class (see `classes.DEFAULT_REFERENCE_HEIGHTS_M`),
     not a measurement of the specific detected instance. A child and an
     adult "person" are both assumed to be 1.7m tall by this method,
     which will visibly bias the estimate.

Consequently this estimate should be treated as approximate (typically
within a rough +/-20-30% band under good conditions, worse otherwise),
and is explicitly designed to be swapped out later for stereo camera,
depth camera, LiDAR, or sensor-fusion-provided distance -- see
`DistanceEstimator` docstring for how.
"""
from __future__ import annotations

from ai_vision.schemas.detection import BoundingBox


class DistanceEstimationError(ValueError):
    """Raised when a distance estimate cannot be computed (bad input/calibration)."""


class DistanceEstimator:
    """
    Monocular distance estimator.

    Swappable by design: any future stereo/depth/LiDAR/sensor-fusion
    distance source only needs to implement `.estimate(class_name, bbox)
    -> float | None` to be a drop-in replacement for this class -- nothing
    downstream (tracker, movement analysis, output schema) depends on
    *how* the distance was produced, only that it's a float in meters.
    """

    def __init__(
        self,
        focal_length_px: float,
        reference_heights_m: dict[str, float],
    ):
        if focal_length_px <= 0:
            raise DistanceEstimationError("focal_length_px must be > 0")
        self.focal_length_px = focal_length_px
        self.reference_heights_m = reference_heights_m

    def estimate(self, class_name: str, bbox: BoundingBox) -> float | None:
        """
        Return an estimated distance in meters, or None if this class has
        no configured reference height (uncalibrated for that class) --
        callers should treat None as "unknown", not zero.
        """
        reference_height = self.reference_heights_m.get(class_name)
        if reference_height is None:
            return None

        bbox_height_px = bbox.height
        if bbox_height_px <= 0:
            raise DistanceEstimationError(
                f"Invalid bbox height ({bbox_height_px}) for distance estimation."
            )

        distance_m = (self.focal_length_px * reference_height) / bbox_height_px

        # Sanity bounds: monocular estimates from a walking-stick-mounted
        # camera outside this range are almost certainly estimation noise
        # (e.g. a barely-clipped bbox) rather than a real distance.
        if distance_m <= 0 or distance_m > 200:
            raise DistanceEstimationError(
                f"Distance estimate {distance_m:.2f}m outside sane bounds (0, 200]."
            )

        return round(distance_m, 2)


def calibrate_focal_length(
    known_distance_m: float,
    known_object_height_m: float,
    observed_bbox_height_px: float,
) -> float:
    """
    Derive `focal_length_px` from a single calibration measurement:
    place an object of known real height at a known distance from the
    camera, measure its bbox height in pixels, and solve the pinhole
    formula for focal length:

        focal_length_px = (observed_bbox_height_px * known_distance_m) / known_object_height_m

    Run this once per physical camera (e.g. via a small calibration
    script) and store the result in `AI_VISION_FOCAL_LENGTH_PX` in `.env`.
    """
    if known_distance_m <= 0 or known_object_height_m <= 0 or observed_bbox_height_px <= 0:
        raise DistanceEstimationError("All calibration inputs must be > 0.")
    return (observed_bbox_height_px * known_distance_m) / known_object_height_m
