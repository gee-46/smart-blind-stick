"""
AI Vision module for the Smart Blind Stick project.

Pipeline:

    Camera -> Preprocessing -> YOLO Detection -> Confidence Filtering
           -> Object Tracking -> Distance Estimation -> Direction Estimation
           -> Movement Analysis -> Approaching-Object Detection
           -> Structured Output (Pydantic) -> Backend / Safety Engine adapter

This module produces *structured information* about obstacles (what, where,
how far, moving how). It intentionally does NOT decide what is dangerous —
that decision belongs to the Safety Engine (`feature/safety-emergency`).
Anywhere this module expresses a risk opinion, it is exposed as an
non-authoritative `risk_hint`, never a final `risk_level`.
"""

__version__ = "0.1.0"
