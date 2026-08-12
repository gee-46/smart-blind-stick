"""
Class definitions for the chosen detection model.

Model in use: **YOLOv8n** (`yolov8n.pt`), Ultralytics' smallest/fastest
pretrained checkpoint, trained on the **COCO** dataset (80 classes). It
was verified by actually loading the checkpoint and reading
`model.names` -- the list below is copied verbatim from that, not
guessed. If the configured model path is ever changed, re-verify this
list; do not assume another checkpoint supports the same classes.

We do NOT claim support for any class that is not in `COCO_CLASSES`
below. In particular, this model does NOT distinguish "vehicle" as a
single concept -- it separately detects `car`, `motorcycle`, `bus`, and
`truck`. Any place in this codebase that talks about "vehicles" means
"any of {car, motorcycle, bus, truck}", performed via `VEHICLE_CLASSES`.
"""
from __future__ import annotations

# Exact output of YOLOv8n.names (COCO 80-class), verified against the
# actual downloaded checkpoint on 2026-08-12.
COCO_CLASSES: dict[int, str] = {
    0: "person", 1: "bicycle", 2: "car", 3: "motorcycle", 4: "airplane",
    5: "bus", 6: "train", 7: "truck", 8: "boat", 9: "traffic light",
    10: "fire hydrant", 11: "stop sign", 12: "parking meter", 13: "bench",
    14: "bird", 15: "cat", 16: "dog", 17: "horse", 18: "sheep", 19: "cow",
    20: "elephant", 21: "bear", 22: "zebra", 23: "giraffe", 24: "backpack",
    25: "umbrella", 26: "handbag", 27: "tie", 28: "suitcase", 29: "frisbee",
    30: "skis", 31: "snowboard", 32: "sports ball", 33: "kite",
    34: "baseball bat", 35: "baseball glove", 36: "skateboard",
    37: "surfboard", 38: "tennis racket", 39: "bottle", 40: "wine glass",
    41: "cup", 42: "fork", 43: "knife", 44: "spoon", 45: "bowl",
    46: "banana", 47: "apple", 48: "sandwich", 49: "orange", 50: "broccoli",
    51: "carrot", 52: "hot dog", 53: "pizza", 54: "donut", 55: "cake",
    56: "chair", 57: "couch", 58: "potted plant", 59: "bed",
    60: "dining table", 61: "toilet", 62: "tv", 63: "laptop", 64: "mouse",
    65: "remote", 66: "keyboard", 67: "cell phone", 68: "microwave",
    69: "oven", 70: "toaster", 71: "sink", 72: "refrigerator", 73: "book",
    74: "clock", 75: "vase", 76: "scissors", 77: "teddy bear",
    78: "hair drier", 79: "toothbrush",
}

# Subset of COCO_CLASSES that is actually relevant to a pedestrian mobility
# aid. Used as the default `class_filter` recommendation (config.py leaves
# class_filter empty by default so nothing is silently hidden, but the
# demo scripts and vision_service use this list).
MOBILITY_RELEVANT_CLASSES: tuple[str, ...] = (
    "person",
    "bicycle",
    "car",
    "motorcycle",
    "bus",
    "truck",
    "traffic light",
    "stop sign",
    "bench",
    "dog",
    "cat",
    "chair",
)

# Classes grouped as "vehicle" for movement/approaching-vehicle logic.
VEHICLE_CLASSES: tuple[str, ...] = ("car", "motorcycle", "bus", "truck")

# Approximate real-world reference heights (meters), used only by the
# monocular distance estimator (estimation/distance.py). These are rough
# population averages, NOT measurements of any specific detected object --
# see that module's docstring for the accuracy implications.
DEFAULT_REFERENCE_HEIGHTS_M: dict[str, float] = {
    "person": 1.7,
    "bicycle": 1.1,
    "car": 1.5,
    "motorcycle": 1.3,
    "bus": 3.2,
    "truck": 2.8,
    "traffic light": 3.0,
    "stop sign": 2.1,
    "bench": 0.9,
    "dog": 0.5,
    "cat": 0.3,
    "chair": 0.9,
}


def class_name_for_id(class_id: int) -> str | None:
    """Look up a COCO class name by id, or None if unknown."""
    return COCO_CLASSES.get(class_id)
