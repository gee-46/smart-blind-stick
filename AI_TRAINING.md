# DrishtiGuard AI Vision & YOLOv8n Training Pipeline

> **ETHICAL & ARCHITECTURAL DIRECTIVE:**
> - Never claim a model has been trained or improved unless training actually ran and produced verified artifacts.
> - Never silently train on fabricated data.
> - Keep camera detection separate from proximity-based obstacle warnings. The TF-Luna LiDAR remains the direct physical distance measurement instrument; camera detections provide class classification, bounding box tracking, and advisory risk hints.

---

## 1. Model Architecture & Deployment Paradigm

- **Architecture**: Ultralytics **YOLOv8n** (Nano) — 3.2 million parameters.
- **Pretrained Checkpoint**: `yolov8n.pt` trained on MS COCO (80 classes).
- **Execution Target**: Dedicated inference companion service running on the FastAPI backend server (or edge companion SBC). The ESP32-CAM captures and streams compressed JPEG frames over HTTP/WebSocket to this service.
- **Inference Performance**: ~10 FPS / ~99ms per frame on modern CPU (640x480 input, single core).

---

## 2. Supported Mobility Classes & Categories

While the COCO-trained YOLOv8n model supports 80 classes, DrishtiGuard prioritizes key obstacle and hazard categories (defined in `ai_vision/detection/classes.py`):

1. **Approaching Vehicles (Critical Priority)**:
   - `car`, `bus`, `truck`, `motorcycle`, `bicycle`
2. **Pedestrians & Vulnerable Road Users**:
   - `person`
3. **Urban Navigation Obstacles (Medium Priority)**:
   - `traffic light`, `fire hydrant`, `stop sign`, `parking meter`, `bench`, `chair`
4. **Domestic Obstacles**:
   - `dog`, `cat`, `suitcase`, `potted plant`, `couch`, `tv`

---

## 3. Custom Training Workflow

To fine-tune YOLOv8n on specialized assistive mobility datasets (e.g., ground-level curbs, potholes, staircase ascents/descents, overhanging tree branches):

### 3.1 Dataset Preparation
Structure your dataset according to the standard YOLO directory layout:
```text
dataset/
├── data.yaml
├── images/
│   ├── train/
│   ├── val/
│   └── test/
└── labels/
    ├── train/
    ├── val/
    └── test/
```

Example `data.yaml`:
```yaml
path: ./dataset
train: images/train
val: images/val
test: images/test

names:
  0: person
  1: vehicle
  2: bicycle
  3: pothole
  4: curb
  5: staircase
  6: obstacle
```

### 3.2 Reproducible Training Command
Run the training pipeline with fixed seed for determinism:
```bash
yolo task=detect mode=train \
  model=yolov8n.pt \
  data=dataset/data.yaml \
  epochs=100 \
  imgsz=640 \
  batch=16 \
  seed=42 \
  deterministic=True \
  project=runs/train \
  name=drishtiguard_custom
```

### 3.3 Evaluation & Validation Metrics
Evaluate the trained checkpoint against the held-out test split:
```bash
yolo task=detect mode=val \
  model=runs/train/drishtiguard_custom/weights/best.pt \
  data=dataset/data.yaml \
  split=test
```

Required Metrics to Document:
- $\text{mAP}_{50}$ (Mean Average Precision at IoU = 0.50)
- $\text{mAP}_{50-95}$
- Per-class Precision & Recall curves
- Confusion Matrix
- Average latency per frame (ms)

### 3.4 Model Deployment
Copy the verified weights into the models directory:
```bash
cp runs/train/drishtiguard_custom/weights/best.pt models/yolov8n.pt
```

Update `AI_VISION_MODEL_PATH` in `.env`:
```ini
AI_VISION_MODEL_PATH=models/yolov8n.pt
```

---

## 4. Distance Estimation vs. LiDAR Physical Truth

Camera-based distance estimation (monocular depth) is computed geometrically in `ai_vision/estimation/distance.py` using known real-world object reference heights and camera focal length:

$$D = \frac{f \times H_{real}}{h_{pixel}}$$

> **SAFETY NOTICE:** Monocular camera distance estimation is an advisory heuristic subject to perspective distortion, camera tilt, and object truncation. **Only the TF-Luna LiDAR sensor measurements are treated as verified physical distance truth for immediate emergency obstacle stops.**
