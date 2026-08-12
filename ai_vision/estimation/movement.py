"""
Movement analysis.

Uses a track's recent distance history (populated by the tracker across
frames) to classify movement. Never classifies from a single frame --
see project spec section 11.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ai_vision.schemas.detection import Movement


@dataclass
class DistanceSample:
    timestamp: float  # seconds, monotonic or unix -- only relative order matters
    distance_m: float


@dataclass
class TrackHistory:
    """Rolling history of distance samples for one tracked object."""

    track_id: int
    samples: list[DistanceSample] = field(default_factory=list)

    def add(self, sample: DistanceSample, max_len: int = 30) -> None:
        self.samples.append(sample)
        if len(self.samples) > max_len:
            self.samples.pop(0)


def classify_movement(
    history: list[DistanceSample],
    min_history: int = 3,
    distance_delta_threshold_m: float = 0.15,
    window: int = 5,
) -> Movement:
    """
    Classify movement from a chronological list of distance samples.

    Rules:
      - Fewer than `min_history` samples -> UNKNOWN (never guess from one
        or two frames; estimation noise is significant at that scale).
      - Otherwise, look at the most recent `window` samples, compare the
        first and last: if the net change is smaller than
        `distance_delta_threshold_m`, the object is STATIONARY (this
        absorbs monocular-estimation jitter).
      - If distance is decreasing beyond the threshold -> APPROACHING.
      - If distance is increasing beyond the threshold -> MOVING_AWAY.
      - (MOVING is reserved for future lateral-motion detection, once
        bbox-center trajectory is also considered -- not derivable from
        distance alone today.)
    """
    if min_history < 2:
        raise ValueError("min_history must be >= 2 (a trend needs at least 2 points)")
    if len(history) < min_history:
        return Movement.UNKNOWN

    recent = history[-window:] if window > 0 else history
    if len(recent) < 2:
        return Movement.UNKNOWN

    first_distance = recent[0].distance_m
    last_distance = recent[-1].distance_m
    delta = last_distance - first_distance

    if abs(delta) < distance_delta_threshold_m:
        return Movement.STATIONARY
    if delta < 0:
        return Movement.APPROACHING
    return Movement.MOVING_AWAY
