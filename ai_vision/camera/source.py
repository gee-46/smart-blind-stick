"""
Camera input abstraction.

Provides a single, uniform interface -- `.read()` / `.release()` -- over
four different frame sources, so the rest of the pipeline never needs to
know or care where frames are coming from:

    - a live webcam / USB camera / future Raspberry Pi camera (by index)
    - a video file (mp4, avi, ...)
    - a single static image (repeated, useful for quick tests/demos)
    - a mock generator (synthetic frames, for hardware-free development)

Nothing in this file (or anywhere else in `ai_vision/`) hardcodes camera
index `0`. The source is always explicit, via `CameraConfig`.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterator

import numpy as np

try:
    import cv2
except ImportError:  # pragma: no cover - exercised only when opencv is absent
    cv2 = None


class CameraSourceType(str, Enum):
    WEBCAM = "webcam"
    VIDEO_FILE = "video"
    IMAGE = "image"
    MOCK = "mock"


@dataclass
class CameraConfig:
    """Describes where frames come from. Nothing here is hardcoded upstream."""

    source_type: CameraSourceType
    # Webcam device index (e.g. 0, 1, ...) OR a USB/RTSP path string on
    # platforms where OpenCV needs a path instead of an int. Ignored for
    # VIDEO_FILE / IMAGE / MOCK.
    device_index: int = 0
    # Path to a video file or image file. Required for VIDEO_FILE / IMAGE.
    path: str | None = None
    width: int = 640
    height: int = 480
    # Loop a finite source (video file / single image) instead of
    # exhausting it after one pass. Useful for demos.
    loop: bool = False


class CameraSource:
    """
    Uniform camera/video/image/mock frame source.

    Usage:
        camera = CameraSource(CameraConfig(source_type=CameraSourceType.WEBCAM, device_index=0))
        frame = camera.read()   # np.ndarray (BGR) or None if exhausted/unavailable
        camera.release()

    Also usable as a context manager and as an iterator:
        with CameraSource(config) as camera:
            for frame in camera:
                ...
    """

    def __init__(self, config: CameraConfig):
        self.config = config
        self._cap = None
        self._single_image: np.ndarray | None = None
        self._image_served = False
        self._mock_frame_count = 0
        self._open()

    def _open(self) -> None:
        cfg = self.config
        if cfg.source_type == CameraSourceType.MOCK:
            return  # nothing to open; frames are synthesized in read()

        if cfg.source_type == CameraSourceType.IMAGE:
            if cv2 is None:
                raise RuntimeError("OpenCV is required to read image files.")
            if not cfg.path:
                raise ValueError("CameraConfig.path is required for IMAGE source.")
            image = cv2.imread(cfg.path)
            if image is None:
                raise FileNotFoundError(f"Could not read image at '{cfg.path}'.")
            self._single_image = image
            return

        if cv2 is None:
            raise RuntimeError("OpenCV is required for webcam/video sources.")

        if cfg.source_type == CameraSourceType.WEBCAM:
            self._cap = cv2.VideoCapture(cfg.device_index)
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg.width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.height)
        elif cfg.source_type == CameraSourceType.VIDEO_FILE:
            if not cfg.path:
                raise ValueError("CameraConfig.path is required for VIDEO_FILE source.")
            self._cap = cv2.VideoCapture(cfg.path)
        else:  # pragma: no cover - defensive
            raise ValueError(f"Unsupported source_type: {cfg.source_type}")

        if not self._cap.isOpened():
            raise RuntimeError(
                f"Failed to open camera source '{cfg.source_type}' "
                f"(index={cfg.device_index}, path={cfg.path})."
            )

    def read(self) -> np.ndarray | None:
        """Return the next frame (BGR np.ndarray), or None if unavailable/exhausted."""
        cfg = self.config

        if cfg.source_type == CameraSourceType.MOCK:
            return self._read_mock()

        if cfg.source_type == CameraSourceType.IMAGE:
            if self._image_served and not cfg.loop:
                return None
            self._image_served = True
            return None if self._single_image is None else self._single_image.copy()

        if self._cap is None:
            return None
        ok, frame = self._cap.read()
        if not ok:
            if cfg.source_type == CameraSourceType.VIDEO_FILE and cfg.loop:
                self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frame = self._cap.read()
                if ok:
                    return frame
            return None
        return frame

    def _read_mock(self) -> np.ndarray:
        """Synthesize a deterministic solid-color frame for hardware-free dev/tests."""
        self._mock_frame_count += 1
        frame = np.full(
            (self.config.height, self.config.width, 3),
            fill_value=(self._mock_frame_count * 7) % 256,
            dtype=np.uint8,
        )
        return frame

    def release(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    # -- convenience -----------------------------------------------------
    def __enter__(self) -> "CameraSource":
        return self

    def __exit__(self, *exc_info) -> None:
        self.release()

    def __iter__(self) -> Iterator[np.ndarray]:
        while True:
            frame = self.read()
            if frame is None:
                return
            yield frame
