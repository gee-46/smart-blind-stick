"""
Frame preprocessing utilities.

Kept deliberately separate from detection (see project spec section 5):
this module only validates, resizes, and paces frames, and tracks FPS. It
knows nothing about YOLO or any model.
"""
from __future__ import annotations

import time
from collections import deque

import numpy as np

try:
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None


def is_valid_frame(frame: np.ndarray | None) -> bool:
    """A frame is valid if it exists, is 3-dimensional, and has non-zero size."""
    if frame is None:
        return False
    if not isinstance(frame, np.ndarray):
        return False
    if frame.ndim != 3 or frame.shape[2] not in (1, 3, 4):
        return False
    if frame.shape[0] == 0 or frame.shape[1] == 0:
        return False
    return True


def resize_frame(frame: np.ndarray, width: int, height: int) -> np.ndarray:
    """Resize a frame to the given dimensions. Raises on an invalid frame."""
    if not is_valid_frame(frame):
        raise ValueError("Cannot resize an invalid frame.")
    if cv2 is None:
        raise RuntimeError("OpenCV is required for resizing.")
    if frame.shape[1] == width and frame.shape[0] == height:
        return frame
    return cv2.resize(frame, (width, height), interpolation=cv2.INTER_LINEAR)


class FrameSkipper:
    """
    Decides whether the current frame should be processed, based on a
    configurable `skip` factor (1 = process every frame, N = process 1
    out of every N frames). Keeps preprocessing pacing independent of the
    camera source itself.
    """

    def __init__(self, skip: int = 1):
        if skip < 1:
            raise ValueError("skip must be >= 1")
        self.skip = skip
        self._counter = 0

    def should_process(self) -> bool:
        should = self._counter % self.skip == 0
        self._counter += 1
        return should

    def reset(self) -> None:
        self._counter = 0


class FPSCounter:
    """Rolling-window FPS calculator based on wall-clock timestamps."""

    def __init__(self, window_size: int = 30):
        if window_size < 1:
            raise ValueError("window_size must be >= 1")
        self.window_size = window_size
        self._timestamps: deque[float] = deque(maxlen=window_size)

    def tick(self, now: float | None = None) -> float:
        """Record a frame timestamp and return the current rolling FPS (0.0 until 2+ samples)."""
        now = time.monotonic() if now is None else now
        self._timestamps.append(now)
        if len(self._timestamps) < 2:
            return 0.0
        elapsed = self._timestamps[-1] - self._timestamps[0]
        if elapsed <= 0:
            return 0.0
        return (len(self._timestamps) - 1) / elapsed

    def reset(self) -> None:
        self._timestamps.clear()


def preprocess_frame(
    frame: np.ndarray, width: int, height: int
) -> np.ndarray:
    """Validate + resize in one step. Raises ValueError on an invalid frame."""
    if not is_valid_frame(frame):
        raise ValueError("Invalid frame: expected a non-empty HxWx{1,3,4} ndarray.")
    return resize_frame(frame, width, height)
