"""
Optional visualization overlay (project spec section 16).

Draws each tracked detection's box + label ("CAR 94% ID:7 2.1m RIGHT
APPROACHING") onto a frame using OpenCV. Entirely optional -- the rest of
the pipeline (`VisionService`, camera, detector, tracker, estimation) has
no dependency on this module and runs perfectly headless, which is
required for future embedded/Raspberry-Pi deployment with no display
attached.
"""
from __future__ import annotations

import numpy as np

try:
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None

from ai_vision.schemas.detection import AIVisionOutput, TrackedDetection

_BOX_COLOR = (0, 200, 0)
_TEXT_COLOR = (255, 255, 255)


def _label_lines(detection: TrackedDetection) -> list[str]:
    movement = detection.movement.value if hasattr(detection.movement, "value") else detection.movement
    direction = detection.direction.value if hasattr(detection.direction, "value") else detection.direction
    distance_str = f"{detection.distance_m:.1f}m" if detection.distance_m is not None else "?m"
    return [
        f"{detection.object.upper()} {detection.confidence * 100:.0f}%",
        f"ID:{detection.track_id} {distance_str}",
        f"{direction.upper()} {movement.upper()}",
    ]


def draw_overlay(frame: np.ndarray, output: AIVisionOutput) -> np.ndarray:
    """Return a copy of `frame` with detection boxes + labels drawn on it."""
    if cv2 is None:
        raise RuntimeError("OpenCV is required for visualization.")

    canvas = frame.copy()
    for detection in output.detections:
        box = detection.bbox
        pt1 = (int(box.x1), int(box.y1))
        pt2 = (int(box.x2), int(box.y2))
        cv2.rectangle(canvas, pt1, pt2, _BOX_COLOR, 2)

        lines = _label_lines(detection)
        text_y = max(15, int(box.y1) - 10)
        for i, line in enumerate(lines):
            y = text_y - (len(lines) - 1 - i) * 15
            cv2.putText(canvas, line, (int(box.x1), y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, _TEXT_COLOR, 1, cv2.LINE_AA)

    return canvas


def draw_fps(frame: np.ndarray, fps: float) -> np.ndarray:
    """Overlay an FPS counter in the top-left corner. Returns a copy."""
    if cv2 is None:
        raise RuntimeError("OpenCV is required for visualization.")
    canvas = frame.copy()
    cv2.putText(canvas, f"FPS: {fps:.1f}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA)
    return canvas
