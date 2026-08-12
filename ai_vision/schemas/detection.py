"""
Pydantic schemas for the AI Vision module.

`AIVisionOutput` is the stable, documented interface between AI Vision and
the rest of the system (Safety Engine, backend). Treat it like a public
API contract: additive changes only (new optional fields), never rename
or remove a field without updating every consumer.

Field-level notes:
  - `risk_hint` is an *advisory* opinion from AI Vision only. It is never
    a final safety decision -- see the module docstring in
    `ai_vision/__init__.py`. The Safety Engine module owns the actual
    `risk_level` that eventually reaches the backend's Event table.
  - `distance_m` is a monocular *estimate*, not a measurement. See
    `ai_vision/estimation/distance.py`.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Direction(str, Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class Movement(str, Enum):
    STATIONARY = "stationary"
    MOVING = "moving"
    APPROACHING = "approaching"
    MOVING_AWAY = "moving_away"
    UNKNOWN = "unknown"


class RiskHint(str, Enum):
    """Non-authoritative. See module docstring."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class BoundingBox(BaseModel):
    """Pixel-space bounding box, [x1, y1, x2, y2], origin top-left."""

    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def width(self) -> float:
        return max(0.0, self.x2 - self.x1)

    @property
    def height(self) -> float:
        return max(0.0, self.y2 - self.y1)

    @property
    def center_x(self) -> float:
        return (self.x1 + self.x2) / 2.0

    @property
    def center_y(self) -> float:
        return (self.y1 + self.y2) / 2.0


class Detection(BaseModel):
    """A single raw detection from the detector, for one frame. No track_id yet."""

    class_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: BoundingBox


class TrackedDetection(BaseModel):
    """
    A detection enriched with tracking, distance, direction, and movement
    information -- one entry in `AIVisionOutput.detections`.
    """

    model_config = ConfigDict(use_enum_values=False)

    track_id: int
    object: str = Field(description="Class name, e.g. 'person', 'car'.")
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: BoundingBox
    distance_m: float | None = Field(default=None, description="Monocular estimate; may be None if uncalibrated.")
    direction: Direction
    movement: Movement = Movement.UNKNOWN
    risk_hint: RiskHint | None = Field(
        default=None,
        description="Advisory only. Never a final safety decision -- Safety Engine decides risk_level.",
    )


class AIVisionOutput(BaseModel):
    """The stable AI Vision -> Safety Engine / backend output schema."""

    source: str = "ai_vision"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    detections: list[TrackedDetection] = Field(default_factory=list)
