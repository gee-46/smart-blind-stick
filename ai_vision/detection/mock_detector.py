"""
Mock detector for development and testing without model weights, GPU, or
`ultralytics`/`torch` installed (see project spec section 17).

`MockDetector` satisfies the same `Detector` protocol as `YoloDetector`
(`.detect(frame) -> list[Detection]`), so `VisionService` and every
downstream stage (tracker, distance, direction, movement) can be
exercised end-to-end in unit tests using only this class.
"""
from __future__ import annotations

import numpy as np

from ai_vision.schemas.detection import BoundingBox, Detection


class MockDetector:
    """Returns a pre-programmed, fixed sequence of detections, one call at a time.

    If more calls are made than there are programmed frames, the last
    frame's detections are repeated (useful for "hold this object steady"
    tests). If constructed with no frames at all, always returns [].
    """

    def __init__(self, scripted_detections: list[list[Detection]] | None = None):
        self._script = scripted_detections or []
        self._call_index = 0

    def detect(self, frame: np.ndarray) -> list[Detection]:
        if not self._script:
            return []
        index = min(self._call_index, len(self._script) - 1)
        self._call_index += 1
        return list(self._script[index])


def make_detection(
    class_name: str,
    confidence: float,
    bbox: tuple[float, float, float, float],
) -> Detection:
    """Convenience constructor: make_detection("person", 0.9, (100, 50, 200, 400))."""
    x1, y1, x2, y2 = bbox
    return Detection(
        class_name=class_name,
        confidence=confidence,
        bbox=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2),
    )
