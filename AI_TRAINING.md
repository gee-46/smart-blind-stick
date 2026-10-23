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

While the standard COCO-trained YOLOv8n model supports 80 generic classes, DrishtiGuard filters and consolidates detections into the **10 Canonical Assistive Mobility Classes** defined in [ai_vision/detection/classes.py](file:///c:/Users/Dell/Downloads/smart-blind-stick-ai-vision/ai_vision/detection/classes.py):

| Canonical Class | COCO Source Labels | Priority | Default Reference Height ($H_{real}$) |
| :--- | :--- | :--- | :--- |
| **`person`** | `person` | High | 1.7 m |
| **`vehicle`** | `car`, `bus`, `truck` | Critical (approaching) | 1.6 m (car: 1.5m, bus: 3.2m, truck: 2.8m) |
| **`bicycle`** | `bicycle` | High | 1.1 m |
| **`motorcycle`** | `motorcycle` | High | 1.3 m |
| **`pole`** | `pole`, `traffic light`, `stop sign`, `fire hydrant`, `parking meter` | Medium | 2.6 m (sign: 2.1m, light: 3.0m) |
| **`tree`** | `tree`, `potted plant` | Medium | 3.2 m |
| **`staircase`** | `staircase`, `steps` | High | 1.4 m |
| **`door`** | `door` | Medium | 2.1 m |
| **`chair`** | `chair`, `bench`, `couch` | Low / Info | 0.9 m |
| **`wall`** | `wall`, `barrier` | High | 2.5 m |

---

## 3. Custom Training & Fine-Tuning Workflow

To fine-tune YOLOv8n on specialized assistive mobility datasets (incorporating ground-level hazards such as curbs, potholes, construction trenches, and descending stairs):

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

Complete `data.yaml` schema for Assistive Mobility + Ground Hazards:
```yaml
path: ./dataset
train: images/train
val: images/val
test: images/test

names:
  0: person
  1: vehicle
  2: bicycle
  3: motorcycle
  4: pole
  5: tree
  6: staircase
  7: door
  8: chair
  9: wall
  10: pothole
  11: curb
  12: dropoff
  13: construction_barrier
```

### 3.2 Reproducible Training Command
Run the training pipeline with fixed random seeds for strict determinism:
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

### 3.4 Model Deployment & Edge Export
1. **Local PyTorch Deployment**:
   ```bash
   cp runs/train/drishtiguard_custom/weights/best.pt models/yolov8n.pt
   ```
   Update `AI_VISION_MODEL_PATH` in `.env`:
   ```ini
   AI_VISION_MODEL_PATH=models/yolov8n.pt
   ```

2. **Edge Companion Export (ONNX / TFLite)**:
   For execution on low-power edge companion SBCs (Raspberry Pi, Orange Pi, or Jetson Nano):
   ```bash
   # Export to ONNX (for ONNX Runtime CPU/GPU execution)
   yolo export model=models/yolov8n.pt format=onnx imgsz=640 optimize=True

   # Export to TFLite (FP16 or INT8 quantization for edge mobile SBCs)
   yolo export model=models/yolov8n.pt format=tflite imgsz=640 int8=True
   ```

---

## 4. Distance Estimation vs. LiDAR Physical Truth

Camera-based distance estimation (monocular depth) is computed geometrically in [ai_vision/estimation/distance.py](file:///c:/Users/Dell/Downloads/smart-blind-stick-ai-vision/ai_vision/estimation/distance.py) using known real-world object reference heights and camera focal length:

$$D = \frac{f \times H_{real}}{h_{pixel}}$$

Where:
- $f$ is the calibrated camera focal length in pixels (~615 px for standard 640x480 OV2640 lens).
- $H_{real}$ is the canonical reference height for the recognized class in meters.
- $h_{pixel}$ is the bounding box height in image pixels ($y_{max} - y_{min}$).

### Closing Velocity & Motion Tracking
Closing velocity ($v = \frac{\Delta D}{\Delta t}$) is estimated across consecutive video frames in `ai_vision/estimation/motion.py`. Any vehicle or approaching obstacle closing at $> 0.5\text{ m/s}$ elevates priority to `CRITICAL (P1)` and triggers high-frequency tactile alerts.

> **SAFETY NOTICE:** Monocular camera distance estimation is an advisory heuristic subject to perspective distortion, camera tilt, and object truncation. **Only the TF-Luna LiDAR sensor measurements are treated as verified physical distance truth for immediate emergency obstacle stops.**

