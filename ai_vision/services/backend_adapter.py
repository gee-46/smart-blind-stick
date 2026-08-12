"""
Backend integration adapter.

Converts `AIVisionOutput` (this module's own schema) into the event shape
the existing FastAPI backend (`feature/mobile-iot`, `POST /api/events`)
expects. We do NOT import or modify anything from `app/` (that code lives
on a different branch) -- instead this module defines a small local
mirror of the backend's `EventIn` contract, sourced from
`feature/mobile-iot`'s README ("Integration Contract for Teammates") and
`app/schemas/event.py`, and validates against that mirror. This keeps AI
Vision developable and testable in complete isolation from the backend
branch, per project spec section 25 ("do not modify unrelated backend
code").

IMPORTANT -- risk_level vs risk_hint:
The backend's generic Event has a top-level `risk_level` field, and the
example in the existing README populates it directly from AI Vision
(e.g. `"risk_level": "high"`). However, the AI Vision spec is explicit
that this module must NOT make the final safety decision -- only the
Safety Engine (`feature/safety-emergency`) should. To resolve this
without blocking downstream integration:

  - By default (`populate_backend_risk_level_from_hint=False` in
    VisionSettings), `risk_level` is left `None` in the event we build,
    and our advisory opinion travels ONLY inside `extra.risk_hint`,
    clearly labeled as non-final.
  - Teams that want to demo/integration-test end-to-end *before* the
    Safety Engine exists can flip that setting to True, which mirrors
    the current README example exactly (risk_hint copied into
    risk_level) -- but this is explicitly a temporary stand-in, not a
    design endorsement. See `integration_notes.md` for the full
    rationale to raise with the Safety Engine's author.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ai_vision.schemas.detection import AIVisionOutput, TrackedDetection


class BackendEventIn(BaseModel):
    """
    Local mirror of `app.schemas.event.EventIn` from `feature/mobile-iot`.

    Deliberately duplicated (not imported) so this branch has zero
    dependency on backend code. Keep in sync manually if the backend
    contract changes -- see the docstring above for the source of truth.
    """

    model_config = ConfigDict(extra="forbid")

    device_id: str = Field(..., min_length=1, max_length=64)
    source: str
    event_type: str
    risk_level: str | None = None
    message: str | None = Field(default=None, max_length=512)
    extra: dict[str, Any] | None = None


_MOVEMENT_TO_MESSAGE = {
    "approaching": "approaching",
    "moving_away": "moving away",
    "stationary": "stationary",
    "moving": "moving",
    "unknown": "detected",
}


def _direction_phrase(direction: str) -> str:
    if direction == "center":
        return "ahead"
    return f"on the {direction}" if direction else ""


def build_message(detection: TrackedDetection) -> str:
    """Human-readable summary, e.g. 'Vehicle approaching from right'."""
    obj = detection.object.capitalize()
    movement_word = _MOVEMENT_TO_MESSAGE.get(
        detection.movement.value if hasattr(detection.movement, "value") else detection.movement,
        "detected",
    )
    direction = detection.direction.value if hasattr(detection.direction, "value") else detection.direction

    if movement_word == "approaching":
        return f"{obj} approaching from {direction}"
    if movement_word == "detected":
        return f"{obj} detected {_direction_phrase(direction)}"
    return f"{obj} {movement_word} {_direction_phrase(direction)}"


def to_backend_event(
    detection: TrackedDetection,
    device_id: str,
    populate_risk_level_from_hint: bool = False,
) -> BackendEventIn:
    """Convert a single TrackedDetection into a backend-compatible event."""
    risk_hint_value = (
        detection.risk_hint.value if hasattr(detection.risk_hint, "value") else detection.risk_hint
    )
    direction_value = detection.direction.value if hasattr(detection.direction, "value") else detection.direction
    movement_value = detection.movement.value if hasattr(detection.movement, "value") else detection.movement

    return BackendEventIn(
        device_id=device_id,
        source="ai_vision",
        event_type="object_detected",
        risk_level=risk_hint_value if populate_risk_level_from_hint else None,
        message=build_message(detection),
        extra={
            "track_id": detection.track_id,
            "object": detection.object,
            "confidence": round(detection.confidence, 4),
            "distance_m": detection.distance_m,
            "direction": direction_value,
            "movement": movement_value,
            "risk_hint": risk_hint_value,
        },
    )


def to_backend_events(
    output: AIVisionOutput,
    device_id: str,
    populate_risk_level_from_hint: bool = False,
) -> list[BackendEventIn]:
    """Convert every detection in an AIVisionOutput into backend events."""
    return [
        to_backend_event(det, device_id, populate_risk_level_from_hint)
        for det in output.detections
    ]


def post_events_to_backend(
    events: list[BackendEventIn],
    base_url: str,
    timeout_seconds: float = 3.0,
) -> list[dict[str, Any]]:
    """
    Optional convenience: POST each event to the running backend's
    `/api/events`. Not required for tests (they exercise the pure
    conversion functions above) and not called anywhere by default --
    only invoked explicitly by demo scripts if a backend URL is
    configured and reachable.
    """
    import requests  # local import: keep this module importable without `requests` at test time

    results = []
    for event in events:
        response = requests.post(
            f"{base_url.rstrip('/')}/api/events",
            json=event.model_dump(exclude_none=True),
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        results.append(response.json())
    return results
