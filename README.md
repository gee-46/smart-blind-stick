# 🦯 Smart Blind Stick

## AI-Powered Smart Mobility System Using IoT, Sensors, GPS & Computer Vision

> An intelligent assistive mobility system designed to improve the safety, independence, and navigation of visually impaired individuals through real-time sensing, AI-based object detection, GPS tracking, and emergency assistance.

---

## 📌 Overview

The **Smart Blind Stick** is an upgraded mobility aid that combines traditional obstacle detection with modern technologies such as:

* Artificial Intelligence
* Computer Vision
* IoT
* Ultrasonic Sensors
* IR Sensors
* IMU
* GPS
* Real-Time Event Processing
* Safety & Risk Assessment
* Emergency Assistance

The system is designed to detect obstacles at different levels, understand the surrounding environment, estimate object movement and approximate distance, track the user's location, and provide intelligent alerts.

Instead of simply detecting:

> **"Obstacle detected"**

the system aims to understand:

> **What is the object? Where is it? How far is it? Is it moving? Is it approaching? How dangerous is the situation?**

---

# ❗ Problem Statement

Traditional white canes are useful for detecting obstacles near ground level but have limitations when dealing with:

* Head-level obstacles
* Overhanging objects
* Moving vehicles
* Bicycles and motorcycles
* Objects outside the physical reach of the cane
* Complex environments requiring contextual understanding

Traditional canes also do not provide:

* Real-time GPS tracking
* Emergency SOS functionality
* Guardian monitoring
* AI-based environmental understanding
* Intelligent risk assessment

Therefore, there is a need for an affordable and intelligent assistive mobility system that combines **physical sensing, computer vision, GPS, IoT, and safety intelligence**.

---

# 💡 Proposed Solution

The Smart Blind Stick combines multiple sensing and intelligence layers into a single system.

```text
                         SMART BLIND STICK
                                │
             ┌──────────────────┼──────────────────┐
             │                  │                  │
             ▼                  ▼                  ▼
       Sensor Fusion        AI Vision          GPS + IoT
             │                  │                  │
             └──────────────────┼──────────────────┘
                                ▼
                         Safety Engine
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
                Vibration     Audio        SOS
                    │           │           │
                    └───────────┼───────────┘
                                ▼
                              USER
```

The system combines information from multiple sources before generating safety decisions.

---

# 🎯 Objectives

* Detect obstacles at multiple heights and distances.
* Identify objects using computer vision.
* Estimate object direction and approximate distance.
* Track objects across frames.
* Detect moving and approaching objects.
* Combine AI and sensor information.
* Generate intelligent safety decisions.
* Provide vibration and audio alerts.
* Track the user's GPS location.
* Provide emergency SOS functionality.
* Maintain an affordable and scalable architecture.

---

# 🚀 Key Features

## 1. AI Vision

The AI Vision module provides real-time environmental understanding.

### Implemented

* Real-time camera input
* Webcam support
* Video input
* Image input
* Mock input
* YOLOv8n object detection
* Confidence filtering
* Class filtering
* Object tracking
* Stable tracking IDs
* LEFT / CENTER / RIGHT direction estimation
* Monocular distance estimation
* Movement detection
* Approaching vehicle detection
* Structured Pydantic output
* Backend event adapter

### Mobility-Relevant Classes

The current implementation uses relevant COCO classes:

* Person
* Bicycle
* Car
* Motorcycle
* Bus
* Truck
* Traffic Light
* Stop Sign
* Bench
* Dog
* Cat
* Chair

### AI Vision Pipeline

```text
Camera
   ↓
Frame Capture
   ↓
Preprocessing
   ↓
YOLOv8n Detection
   ↓
Confidence Filtering
   ↓
Object Tracking
   ↓
Direction Estimation
   ↓
Distance Estimation
   ↓
Movement Analysis
   ↓
Approaching Object Detection
   ↓
Structured AI Output
   ↓
Safety Engine
```

---

# 2. Sensor Fusion

The Sensor Fusion module will combine data from:

* Ultrasonic sensors
* IR sensors
* IMU
* Distance measurements
* Direction information

```text
Ultrasonic
     +
IR Sensors
     +
IMU
     ↓
Sensor Fusion
     ↓
Unified Environmental Information
```

### Status

**Pending**

---

# 3. Safety & Risk Assessment

The Safety Engine will combine information from:

* AI Vision
* Sensor Fusion
* Distance
* Direction
* Movement
* GPS/context

The final system will classify situations as:

```text
SAFE
LOW
MEDIUM
HIGH
CRITICAL
```

### Important Design Principle

AI Vision provides an advisory **`risk_hint`**.

It does **not** independently determine the final `risk_level`.

The Safety Engine will make the final decision using multiple inputs.

### Status

**Pending**

---

# 4. GPS Tracking

The backend currently supports:

* Real-time location
* Location history
* GPS availability
* Last known location
* Latitude/longitude tracking
* Mock GPS
* Real GPS client support

Compatible GPS hardware can provide NMEA-0183 data to the backend.

### Status

**Backend implemented; physical hardware integration pending.**

---

# 5. Emergency SOS

The system provides an SOS mechanism for emergency situations.

Potential triggers:

* Manual SOS button
* Fall detection
* Critical safety event
* Automatic emergency trigger

SOS information can include:

* Device ID
* Location
* Emergency reason
* Timestamp

### Status

**Backend SOS foundation implemented; complete safety/emergency integration pending.**

---

# 6. Guardian / Mobile Application

A future guardian/mobile interface will provide:

* Live location
* Device status
* Emergency notifications
* Event history
* Safety status
* Guardian monitoring

### Status

**Pending**

---

# 🏗️ System Architecture

```text
                         SMART BLIND STICK
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
       Ultrasonic / IR       Camera             GPS
              │                 │                 │
              ▼                 ▼                 │
       Sensor Fusion        AI Vision              │
              │                 │                 │
              └─────────────────┼─────────────────┘
                                ▼
                         Safety Engine
                                │
                    ┌───────────┼───────────┐
                    │           │           │
                    ▼           ▼           ▼
                 Vibration    Audio        SOS
                                │
                                ▼
                         FastAPI Backend
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
                 Database    GPS Data     Events
                                │
                                ▼
                       Guardian / Mobile
```

---

# 🔄 Safety Decision Flow

```text
AI Vision
    │
    ├── Object
    ├── Distance
    ├── Direction
    ├── Movement
    └── Confidence
           │
           ▼
     Sensor Fusion
           │
    ┌──────┼──────┐
    ▼      ▼      ▼
Ultrasonic IR     IMU
    │      │      │
    └──────┼──────┘
           ▼
      Safety Engine
           │
           ▼
     Risk Assessment
           │
    ┌──────┼──────┐
    ▼      ▼      ▼
Vibration Audio   SOS
```

---

# 🧩 Backend Architecture

The backend follows a layered architecture:

```text
API Layer
    ↓
Service Layer
    ↓
Database Models
    ↓
SQLite / PostgreSQL
```

FastAPI routes remain thin while business logic is handled by service modules.

This allows the AI Vision, Sensor Fusion, and Safety Engine modules to communicate through defined interfaces.

---

# 🛠️ Technology Stack

### AI / Machine Learning

* Python
* PyTorch
* Ultralytics YOLO
* YOLOv8n
* Computer Vision
* Object Tracking
* Monocular Distance Estimation

### Computer Vision

* OpenCV
* NumPy

### Backend

* FastAPI
* Pydantic
* SQLAlchemy

### Database

* SQLite
* PostgreSQL-ready architecture

### IoT / Hardware

* ESP32 / Raspberry Pi
* Ultrasonic Sensors
* IR Sensors
* IMU
* GPS
* Camera
* Vibration Motor
* Buzzer / Audio

### Testing

* pytest
* FastAPI TestClient
* Mock data
* Device simulator

### Development

* Git
* GitHub
* VS Code
* Python Virtual Environment

---

# 📂 Project Structure

```text
smart-blind-stick/
│
├── app/
│   ├── main.py
│   ├── config.py
│   │
│   ├── api/
│   │   ├── device.py
│   │   ├── location.py
│   │   ├── events.py
│   │   └── sos.py
│   │
│   ├── models/
│   │   ├── device.py
│   │   ├── location.py
│   │   └── event.py
│   │
│   ├── schemas/
│   │   ├── device.py
│   │   ├── location.py
│   │   └── event.py
│   │
│   ├── services/
│   │   ├── device_service.py
│   │   ├── location_service.py
│   │   ├── event_service.py
│   │   └── notification_service.py
│   │
│   └── database/
│       ├── base.py
│       └── database.py
│
├── ai_vision/
│   ├── camera/
│   ├── detection/
│   ├── estimation/
│   ├── schemas/
│   ├── services/
│   └── config.py
│
├── tests/
│
├── scripts/
│   ├── simulate_device.py
│   ├── gps_reader.py
│   └── gps_device_client.py
│
├── models/
│   └── README.md
│
├── integration_notes.md
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── run.py
```

---

# 🌿 GitHub Branch Structure

```text
main
 │
 └── develop
      │
      ├── feature/mobile-iot
      │
      ├── feature/ai-vision
      │
      ├── feature/sensor-fusion
      │
      └── feature/safety-emergency
```

| Branch                     | Responsibility                                                 |
| -------------------------- | -------------------------------------------------------------- |
| `feature/mobile-iot`       | Backend, IoT communication, GPS, events, SOS                   |
| `feature/ai-vision`        | Computer vision and AI                                         |
| `feature/sensor-fusion`    | Ultrasonic, IR, IMU and sensor processing                      |
| `feature/safety-emergency` | Risk assessment, alerts, fall detection and emergency handling |

---

# ✅ Work Completed

## Backend / Mobile-IoT

* [x] FastAPI backend
* [x] SQLite + SQLAlchemy
* [x] Device communication
* [x] Device status monitoring
* [x] GPS location tracking
* [x] Location history
* [x] Event ingestion
* [x] Event filtering
* [x] SOS endpoint
* [x] Notification abstraction
* [x] Mock device simulator
* [x] Swagger documentation
* [x] Real GPS client support
* [x] Automated testing
* [x] **35/35 backend tests passing**

## AI Vision

* [x] Camera input
* [x] Webcam / video / image / mock modes
* [x] YOLOv8n
* [x] Confidence filtering
* [x] Class filtering
* [x] Object tracking
* [x] Stable track IDs
* [x] Direction estimation
* [x] Monocular distance estimation
* [x] Movement detection
* [x] Approaching vehicle detection
* [x] Structured Pydantic output
* [x] Backend adapter
* [x] **94/94 AI Vision tests passing**
* [x] AI Vision documentation

---

# 📊 Current Development Status

| Module                 | Status                          |
| ---------------------- | ------------------------------- |
| Backend / IoT          | 🟢 Core implementation complete |
| AI Vision              | 🟢 Core implementation complete |
| Sensor Fusion          | 🔴 Pending                      |
| Safety & Emergency     | 🔴 Pending                      |
| Hardware Integration   | 🔴 Pending                      |
| Mobile / Guardian App  | 🔴 Pending                      |
| End-to-End Integration | 🔴 Pending                      |

### Overall Project

**Approximately 40% complete**

The current project has two major software foundations:

> **Backend / IoT + AI Vision**

The remaining work focuses mainly on sensor intelligence, safety decision-making, hardware integration, mobile/guardian functionality, and complete system validation.

---

# 🔜 Pending Work

## Sensor Fusion

* [ ] Ultrasonic sensor integration
* [ ] IR sensor integration
* [ ] IMU integration
* [ ] Multi-sensor obstacle representation
* [ ] Sensor confidence handling
* [ ] Real hardware testing

## Safety & Emergency

* [ ] Risk assessment engine
* [ ] Multi-source risk calculation
* [ ] Alert priority system
* [ ] Fall detection
* [ ] Emergency event handling
* [ ] Automatic SOS triggers
* [ ] Notification integration

## Hardware

* [ ] ESP32 / Raspberry Pi integration
* [ ] Camera mounting
* [ ] Sensor mounting
* [ ] GPS hardware
* [ ] Vibration motor
* [ ] Buzzer / audio
* [ ] Rechargeable battery
* [ ] 3D-printed enclosure
* [ ] Physical prototype

## Mobile / Guardian Application

* [ ] Live location
* [ ] Device status
* [ ] Emergency notifications
* [ ] Event history
* [ ] Guardian monitoring
* [ ] Backend integration

## Final Integration

* [ ] AI Vision + Sensor Fusion
* [ ] AI Vision + Safety Engine
* [ ] Sensor Fusion + Safety Engine
* [ ] Safety Engine + Backend
* [ ] Backend + Mobile App
* [ ] Hardware + Software
* [ ] End-to-end testing
* [ ] Real-world navigation testing
* [ ] Performance benchmarking
* [ ] Final deployment

---

# 🔌 API

The backend currently exposes:

| Method | Endpoint                            | Description      |
| ------ | ----------------------------------- | ---------------- |
| POST   | `/api/device/data`                  | Device check-in  |
| GET    | `/api/device/status/{device_id}`    | Device status    |
| GET    | `/api/location/{device_id}`         | Latest location  |
| GET    | `/api/location/{device_id}/history` | Location history |
| POST   | `/api/events`                       | Event ingestion  |
| GET    | `/api/events/{device_id}`           | Event history    |
| POST   | `/api/sos`                          | SOS              |
| GET    | `/health`                           | Health check     |

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

---

# 🔗 Module Integration Contract

The modules communicate through the backend event system.

```json
{
  "device_id": "STICK_001",
  "source": "sensor_fusion | ai_vision | safety_engine",
  "event_type": "obstacle | object_detected | danger",
  "risk_level": "low | medium | high | critical",
  "message": "Human-readable summary",
  "extra": {
    "module_specific": "data"
  }
}
```

### AI Vision Output

```json
{
  "device_id": "STICK_001",
  "source": "ai_vision",
  "event_type": "object_detected",
  "message": "Vehicle approaching from right",
  "extra": {
    "object": "car",
    "distance": 2.1,
    "direction": "right",
    "movement": "approaching",
    "confidence": 0.94
  }
}
```

The AI module may generate a `risk_hint`, but the **Safety Engine is responsible for the final `risk_level`**.

---

# ⚙️ Installation

## Clone

```bash
git clone https://github.com/gee-46/smart-blind-stick.git
cd smart-blind-stick
```

## Create Virtual Environment

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Environment Configuration

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Linux/macOS:

```bash
cp .env.example .env
```

---

# ▶️ Running the Backend

```bash
python run.py
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

---

# 🧪 Testing

Run:

```bash
pytest
```

Current results:

```text
Backend:    35/35 passing
AI Vision:  94/94 passing
```

The AI Vision test suite uses mocks and fixtures and does not require physical hardware.

---

# 🤖 AI Vision Performance

Current development baseline:

```text
Model:              YOLOv8n
Device:             CPU
FPS:                ~10
Average inference:  ~99 ms/frame
```

Performance depends on the system hardware, input resolution, model configuration, and environment.

---

# ⚠️ Current Limitations

* Monocular distance estimation is approximate.
* Detection depends on the trained YOLO classes.
* Low-light conditions may reduce detection accuracy.
* Occlusion can affect tracking.
* CPU inference has lower FPS than GPU inference.
* Real-world camera calibration is still required.
* Approaching-object detection depends on reliable temporal tracking.
* Continuous AI-to-backend event throttling is pending.
* Physical hardware validation is pending.
* `risk_hint` is advisory and is not the final safety classification.

---

# 🔮 Future Improvements

* Depth cameras
* Stereo vision
* LiDAR integration
* Improved monocular depth estimation
* Custom obstacle detection datasets
* Edge AI optimization
* TensorRT / OpenVINO optimization
* Advanced object tracking
* Improved low-light detection
* Voice-based navigation
* Offline navigation
* Guardian monitoring
* Cloud analytics
* Predictive safety models

---

# 💰 Target Cost

The project aims to maintain an affordable prototype cost of approximately:

**< ₹3000**

Actual cost will depend on the final hardware configuration, including:

* Microcontroller
* Camera
* GPS
* Sensors
* Battery
* Communication module
* Enclosure

---

# 🌍 Social Impact

The Smart Blind Stick aims to improve:

* Mobility
* Independence
* Environmental awareness
* Personal safety
* Emergency response
* Accessibility

The goal is to **augment the traditional white cane with intelligent technology**, not replace it.

---

# 📜 Development Status

**Status: Active Development**

### Current Milestone

> **Core Backend + AI Vision completed.**

### Next Milestone

> **Sensor Fusion + Safety Engine integration.**

---

## 👥 Team Development

The project follows a feature-branch development workflow.

Each module is developed independently and integrated through `develop`.

```text
feature/mobile-iot
        │
        ├─────────────┐
        │             │
feature/ai-vision   feature/sensor-fusion
        │             │
        └──────┬──────┘
               │
               ▼
       Safety & Integration
               │
               ▼
            develop
               │
               ▼
             main
```

---

# ⭐ Built With

Python • FastAPI • OpenCV • YOLO • PyTorch • SQLAlchemy • Pydantic • NumPy • pytest

---

## 🦯 Smart Blind Stick

**Smarter sensing. Intelligent vision. Safer mobility.**
