"""
YOLO object detector abstraction.

Wraps Ultralytics YOLO behind a small, stable interface:

    detector.detect(frame) -> list[Detection]

so the rest of the pipeline (tracker, estimation, service layer, tests)
never imports `ultralytics` directly. This makes it trivial to swap in a
different model later, and lets tests run with `MockDetector`
(see `detection/mock_detector.py`) without any model weights, GPU, or
`ultralytics`/`torch` installed at all.

Model in use: **YOLOv8n** (`yolov8n.pt`), see `detection/classes.py` for
exactly which classes it supports.
"""
from __future__ import annotations

from typing import Protocol

import numpy as np

from ai_vision.detection.classes import class_name_for_id
from ai_vision.schemas.detection import BoundingBox, Detection


class Detector(Protocol):
    """Structural interface every detector implementation must satisfy."""

    def detect(self, frame: np.ndarray) -> list[Detection]:
        ...


def filter_by_confidence(detections: list[Detection], threshold: float) -> list[Detection]:
    """Discard detections below `threshold`. Pure function, easy to unit-test."""
    return [d for d in detections if d.confidence >= threshold]


def filter_by_class(detections: list[Detection], allowed_classes: tuple[str, ...]) -> list[Detection]:
    """If `allowed_classes` is non-empty, keep only detections in it. Empty = keep all."""
    if not allowed_classes:
        return detections
    allowed = set(allowed_classes)
    return [d for d in detections if d.class_name in allowed]


class YoloDetector:
    """
    Ultralytics-YOLO-backed detector.

    `ultralytics`/`torch` are imported lazily (inside __init__), so simply
    importing this module never requires them -- only actually
    instantiating a YoloDetector does. Every other module in this
    codebase, including tests, depends on the `Detector` protocol and
    `Detection` schema instead, not this class.
    """

    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        confidence_threshold: float = 0.5,
        class_filter: tuple[str, ...] = (),
        device: str = "cpu",
    ):
        try:
            from ultralytics import YOLO
        except ImportError as exc:  # pragma: no cover - exercised only without ultralytics
            raise RuntimeError(
                "ultralytics is required for YoloDetector. "
                "Install it with `pip install ultralytics`, or use MockDetector "
                "for development/testing without model weights."
            ) from exc

        self.confidence_threshold = confidence_threshold
        self.class_filter = class_filter
        self.device = device
        self._model = YOLO(model_path)

    def detect(self, frame: np.ndarray) -> list[Detection]:
        """Run inference on a single BGR frame and return filtered Detection objects."""
        results = self._model.predict(
            source=frame,
            conf=self.confidence_threshold,
            device=self.device,
            verbose=False,
        )
        detections: list[Detection] = []
        if not results:
            return detections

        result = results[0]
        boxes = getattr(result, "boxes", None)
        if boxes is None:
            return detections

        for box in boxes:
            cls_id = int(box.cls[0])
            class_name = class_name_for_id(cls_id) or self._model.names.get(cls_id, str(cls_id))
            confidence = float(box.conf[0])
            x1, y1, x2, y2 = (float(v) for v in box.xyxy[0])
            detections.append(
                Detection(
                    class_name=class_name,
                    confidence=confidence,
                    bbox=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2),
                )
            )

        detections = filter_by_confidence(detections, self.confidence_threshold)
        detections = filter_by_class(detections, self.class_filter)
        return detections
