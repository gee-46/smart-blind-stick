"""
Object tracking.

Implements a small, dependency-free IoU (Intersection-over-Union) +
nearest-match tracker: each new frame's detections are matched against
existing tracks by bounding-box overlap, matched tracks keep their
`track_id`, unmatched detections start new tracks, and tracks that go
unmatched for too many consecutive frames are dropped.

Why a custom tracker instead of Ultralytics' built-in `model.track()`
(ByteTrack/BoT-SORT)? Two reasons:
  1. Testability -- this tracker is pure Python/dataclasses and can be
     unit-tested with `MockDetector` output, with no model weights,
     `ultralytics`, or `torch` involved at all.
  2. Decoupling -- keeping tracking as its own pipeline stage (taking a
     `list[Detection]` in, returning tracked objects out) means the
     detector can be swapped (different YOLO size, different framework)
     without touching tracking logic.

This is a deliberate simplification and is documented as a limitation
(see README "Limitations"): Ultralytics' ByteTrack/BoT-SORT are more
robust to occlusion and fast motion, and are a reasonable future
upgrade -- swap by replacing `Tracker.update()`'s internals, the
downstream interface (`TrackedObject`) does not need to change.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ai_vision.schemas.detection import BoundingBox, Detection


def compute_iou(a: BoundingBox, b: BoundingBox) -> float:
    """Intersection-over-Union of two bounding boxes, in [0.0, 1.0]."""
    inter_x1 = max(a.x1, b.x1)
    inter_y1 = max(a.y1, b.y1)
    inter_x2 = min(a.x2, b.x2)
    inter_y2 = min(a.y2, b.y2)

    inter_width = max(0.0, inter_x2 - inter_x1)
    inter_height = max(0.0, inter_y2 - inter_y1)
    intersection = inter_width * inter_height

    area_a = a.width * a.height
    area_b = b.width * b.height
    union = area_a + area_b - intersection

    if union <= 0:
        return 0.0
    return intersection / union


@dataclass
class Track:
    track_id: int
    class_name: str
    bbox: BoundingBox
    confidence: float
    previous_bbox: BoundingBox | None = None
    missed_frames: int = 0
    age_frames: int = 1


@dataclass
class TrackerState:
    tracks: dict[int, Track] = field(default_factory=dict)
    _next_id: int = 1


class Tracker:
    """
    Stateful IoU tracker. Call `update(detections)` once per frame, in
    order; it returns the current list of live `Track` objects (matched
    and newly created this frame). Tracks are only dropped, never
    reordered or re-numbered, so `track_id` is stable across the track's
    lifetime.
    """

    def __init__(self, min_iou: float = 0.3, max_missed_frames: int = 10):
        if not (0.0 <= min_iou <= 1.0):
            raise ValueError("min_iou must be in [0.0, 1.0]")
        if max_missed_frames < 0:
            raise ValueError("max_missed_frames must be >= 0")
        self.min_iou = min_iou
        self.max_missed_frames = max_missed_frames
        self._state = TrackerState()

    def update(self, detections: list[Detection]) -> list[Track]:
        unmatched_detections = list(range(len(detections)))
        matched_track_ids: set[int] = set()

        # Greedy matching: for each existing track, find the best-IoU
        # unmatched detection of the same class above the threshold.
        for track_id, track in list(self._state.tracks.items()):
            best_idx = None
            best_iou = self.min_iou
            for idx in unmatched_detections:
                det = detections[idx]
                if det.class_name != track.class_name:
                    continue
                iou = compute_iou(track.bbox, det.bbox)
                if iou >= best_iou:
                    best_iou = iou
                    best_idx = idx

            if best_idx is not None:
                det = detections[best_idx]
                track.previous_bbox = track.bbox
                track.bbox = det.bbox
                track.confidence = det.confidence
                track.missed_frames = 0
                track.age_frames += 1
                unmatched_detections.remove(best_idx)
                matched_track_ids.add(track_id)
            else:
                track.missed_frames += 1

        # Drop stale tracks.
        for track_id in list(self._state.tracks.keys()):
            if self._state.tracks[track_id].missed_frames > self.max_missed_frames:
                del self._state.tracks[track_id]

        # Start new tracks for leftover detections.
        for idx in unmatched_detections:
            det = detections[idx]
            new_id = self._state._next_id
            self._state._next_id += 1
            self._state.tracks[new_id] = Track(
                track_id=new_id,
                class_name=det.class_name,
                bbox=det.bbox,
                confidence=det.confidence,
            )

        return list(self._state.tracks.values())

    def reset(self) -> None:
        self._state = TrackerState()
