# Model Weights

Model weight files are **not** committed to Git (see `.gitignore`) --
they're binary, large-ish, and trivially re-downloadable.

## Model in use

**YOLOv8n** (`yolov8n.pt`), Ultralytics' smallest/fastest pretrained
checkpoint, trained on **COCO** (80 classes). Chosen specifically for
real-time CPU inference on modest/edge hardware -- see
`ai_vision/detection/classes.py` for the exact class list this model
supports (verified against the actual checkpoint, not assumed).

Measured on this development machine (single CPU core, 640x480 input,
`yolov8n.pt`, no GPU): **~10 FPS / ~99ms per frame** end-to-end
(preprocessing + inference + tracking + distance + direction +
movement). See `README.md`'s "Performance" section for the full
methodology and how to reproduce this measurement, and for the honest
caveat that a single shared CPU core in a sandboxed dev environment is
not representative of final embedded hardware.

## How to obtain it

### Option A -- automatic (recommended)

Do nothing. The first time `YoloDetector` is instantiated with
`model_path="yolov8n.pt"` (just the filename, no folder), Ultralytics
downloads it automatically from the official Ultralytics GitHub release
assets and caches it in the current working directory.

### Option B -- explicit local copy (used by this project's scripts/tests)

This project's `.env.example` points `AI_VISION_MODEL_PATH` at
`models/yolov8n.pt` so the weights live in a predictable, gitignored
location instead of scattering `.pt` files around the repo root:

```bash
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
mv yolov8n.pt models/yolov8n.pt
```

or download it directly:

```bash
curl -L -o models/yolov8n.pt \
  https://github.com/ultralytics/assets/releases/download/v8.4.0/yolov8n.pt
```

## Swapping models

Any Ultralytics-compatible YOLO checkpoint works -- just point
`AI_VISION_MODEL_PATH` at it. Larger checkpoints (`yolov8s.pt`,
`yolov8m.pt`, ...) trade FPS for accuracy; re-measure performance (see
README) before assuming a larger model is still real-time on the target
hardware. If you switch to a checkpoint trained on different classes
(e.g. a custom dataset), **update `ai_vision/detection/classes.py`** to
match -- do not assume it still supports the COCO class list documented
there.
