"""
Central configuration for the AI Vision module.

Every tunable value used anywhere in `ai_vision/` (confidence threshold,
direction region boundaries, distance-calibration constants, tracker
settings, camera defaults, backend URL, ...) lives here and ONLY here.
No other file should hardcode a threshold, model path, or camera index --
they should import `get_vision_settings()` instead.

Values are loaded from environment variables (via a `.env` file in
development, same pattern as the existing backend's `app/config.py`), with
sensible defaults so the module runs out of the box.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class VisionSettings(BaseSettings):
    """All configuration for the AI Vision pipeline."""

    # ------------------------------------------------------------------
    # Device / backend integration
    # ------------------------------------------------------------------
    device_id: str = "STICK_001"
    backend_base_url: str = "http://127.0.0.1:8000"
    # Populate the backend's top-level `risk_level` field from our
    # non-authoritative `risk_hint` when posting events. Default is False:
    # the Safety Engine module is the intended owner of `risk_level`, and
    # until it exists we prefer to leave it null rather than imply AI
    # Vision made the safety decision. See integration_notes.md.
    populate_backend_risk_level_from_hint: bool = False

    # ------------------------------------------------------------------
    # Camera
    # ------------------------------------------------------------------
    # "webcam", "video", or "image". The actual index/path is passed
    # separately (CLI arg or CameraConfig) so it is never hardcoded here.
    default_camera_source_type: str = "webcam"
    default_webcam_index: int = 0
    camera_frame_width: int = 640
    camera_frame_height: int = 480
    # Process every Nth frame (1 = process every frame).
    frame_skip: int = 1

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------
    model_path: str = "models/yolov8n.pt"
    confidence_threshold: float = 0.5
    # If set, only these class names are kept after detection. Empty tuple
    # = keep every class the model supports. See detection/classes.py for
    # the exact mobility-relevant subset used by default.
    class_filter: tuple[str, ...] = ()
    device: str = "cpu"  # "cpu" or "cuda:0" -- CPU must always work.

    # ------------------------------------------------------------------
    # Direction estimation
    # ------------------------------------------------------------------
    # Fraction of frame width. An object whose bbox-center x falls below
    # `direction_left_boundary` is LEFT, above `direction_right_boundary`
    # is RIGHT, otherwise CENTER.
    direction_left_boundary: float = 0.33
    direction_right_boundary: float = 0.66

    # ------------------------------------------------------------------
    # Distance estimation (monocular, pinhole-camera approximation)
    # ------------------------------------------------------------------
    # distance_m = (focal_length_px * real_object_height_m) / bbox_height_px
    # `focal_length_px` must be obtained via calibration (see
    # estimation/distance.py docstring). This default is a placeholder
    # for a 640px-wide webcam-class lens and MUST be re-calibrated for
    # the real hardware camera before distances are trusted.
    focal_length_px: float = 700.0

    # ------------------------------------------------------------------
    # Tracking
    # ------------------------------------------------------------------
    # Max IoU-distance-normalized frames a track can go unmatched before
    # being dropped.
    tracker_max_missed_frames: int = 10
    # Minimum IoU to associate a new-frame detection with an existing track.
    tracker_min_iou: float = 0.3

    # ------------------------------------------------------------------
    # Movement analysis
    # ------------------------------------------------------------------
    # Minimum number of distance samples in a track's history required
    # before classifying movement (never classify from a single frame).
    movement_min_history: int = 3
    # Minimum meters of net change across the history window to call it
    # "moving" rather than "stationary" (filters out estimation noise).
    movement_distance_delta_threshold_m: float = 0.15
    # How many recent samples to consider when judging trend.
    movement_history_window: int = 5

    model_config = SettingsConfigDict(env_prefix="AI_VISION_", env_file=".env", extra="ignore")


@lru_cache
def get_vision_settings() -> VisionSettings:
    """Cached settings instance (mirrors app/config.py's pattern)."""
    return VisionSettings()
