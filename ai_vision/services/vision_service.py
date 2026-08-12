"""
Vision service: orchestrates the full pipeline for one frame.

    frame -> preprocess -> detect -> confidence filter -> track
          -> direction -> distance -> movement history -> risk_hint
          -> AIVisionOutput

This is the single place that wires every stage together, so
`scripts/run_camera_demo.py` and tests only need to talk to
`VisionService.process_frame()`.
"""
from __future__ import annotations

import time
from typing import Protocol

import numpy as np

from ai_vision.camera.preprocessing import preprocess_frame
from ai_vision.detection.classes import VEHICLE_CLASSES
from ai_vision.detection.tracker import Track, Tracker
from ai_vision.estimation.direction import estimate_direction
from ai_vision.estimation.distance import DistanceEstimationError, DistanceEstimator
from ai_vision.estimation.movement import DistanceSample, TrackHistory, classify_movement
from ai_vision.schemas.detection import (
    AIVisionOutput,
    BoundingBox,
    Detection,
    Direction,
    Movement,
    RiskHint,
    TrackedDetection,
)


class DetectorLike(Protocol):
    def detect(self, frame: np.ndarray) -> list[Detection]:
        ...


def compute_risk_hint(class_name: str, movement: Movement, distance_m: float | None) -> RiskHint | None:
    """
    Advisory-only heuristic (NOT a safety decision -- see module
    docstring in ai_vision/__init__.py and backend_adapter.py). Provided
    purely so the Safety Engine has an optional starting signal; it is
    free to ignore this entirely.
    """
    is_vehicle = class_name in VEHICLE_CLASSES

    if movement == Movement.APPROACHING and is_vehicle:
        if distance_m is not None and distance_m <= 3.0:
            return RiskHint.HIGH
        return RiskHint.MEDIUM
    if movement == Movement.APPROACHING:
        return RiskHint.MEDIUM
    if distance_m is not None and distance_m <= 1.5:
        return RiskHint.MEDIUM
    return RiskHint.LOW


class VisionService:
    """Stateful pipeline: holds the tracker and per-track distance history across frames."""

    def __init__(
        self,
        detector: DetectorLike,
        frame_width: int = 640,
        frame_height: int = 480,
        confidence_threshold: float = 0.5,
        direction_left_boundary: float = 0.33,
        direction_right_boundary: float = 0.66,
        focal_length_px: float = 700.0,
        reference_heights_m: dict[str, float] | None = None,
        tracker_min_iou: float = 0.3,
        tracker_max_missed_frames: int = 10,
        movement_min_history: int = 3,
        movement_distance_delta_threshold_m: float = 0.15,
        movement_history_window: int = 5,
    ):
        from ai_vision.detection.classes import DEFAULT_REFERENCE_HEIGHTS_M

        self.detector = detector
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.confidence_threshold = confidence_threshold
        self.direction_left_boundary = direction_left_boundary
        self.direction_right_boundary = direction_right_boundary

        self.distance_estimator = DistanceEstimator(
            focal_length_px=focal_length_px,
            reference_heights_m=reference_heights_m or DEFAULT_REFERENCE_HEIGHTS_M,
        )
        self.tracker = Tracker(min_iou=tracker_min_iou, max_missed_frames=tracker_max_missed_frames)

        self.movement_min_history = movement_min_history
        self.movement_distance_delta_threshold_m = movement_distance_delta_threshold_m
        self.movement_history_window = movement_history_window

        self._track_histories: dict[int, TrackHistory] = {}

    def process_frame(self, frame: np.ndarray, timestamp: float | None = None) -> AIVisionOutput:
        """Run the full pipeline on one already-captured frame."""
        timestamp = time.monotonic() if timestamp is None else timestamp

        processed = preprocess_frame(frame, self.frame_width, self.frame_height)
        raw_detections = self.detector.detect(processed)
        raw_detections = [d for d in raw_detections if d.confidence >= self.confidence_threshold]

        tracks = self.tracker.update(raw_detections)

        tracked_detections: list[TrackedDetection] = []
        for track in tracks:
            if track.missed_frames > 0:
                # Not seen this frame (tracker kept it alive within grace
                # period) -- don't emit output for it this frame.
                continue
            tracked_detections.append(self._build_tracked_detection(track, timestamp))

        return AIVisionOutput(detections=tracked_detections)

    def _build_tracked_detection(self, track: Track, timestamp: float) -> TrackedDetection:
        direction = estimate_direction(
            track.bbox,
            self.frame_width,
            self.direction_left_boundary,
            self.direction_right_boundary,
        )

        try:
            distance_m = self.distance_estimator.estimate(track.class_name, track.bbox)
        except DistanceEstimationError:
            distance_m = None

        history = self._track_histories.setdefault(track.track_id, TrackHistory(track_id=track.track_id))
        if distance_m is not None:
            history.add(DistanceSample(timestamp=timestamp, distance_m=distance_m))

        movement = classify_movement(
            history.samples,
            min_history=self.movement_min_history,
            distance_delta_threshold_m=self.movement_distance_delta_threshold_m,
            window=self.movement_history_window,
        )

        risk_hint = compute_risk_hint(track.class_name, movement, distance_m)

        return TrackedDetection(
            track_id=track.track_id,
            object=track.class_name,
            confidence=track.confidence,
            bbox=track.bbox,
            distance_m=distance_m,
            direction=direction,
            movement=movement,
            risk_hint=risk_hint,
        )

    def reset(self) -> None:
        self.tracker.reset()
        self._track_histories.clear()
