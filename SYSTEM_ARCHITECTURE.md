# DrishtiGuard System Architecture & End-to-End Data Flow

```mermaid
flowchart TD
    subgraph HARDWARE_STICK ["Physical Smart Blind Stick"]
        TFLUNA["TF-Luna LiDAR\n(20Hz UART2)"]
        NEOGPS["NEO-6M GPS\n(1Hz UART1)"]
        MPU["MPU6050 IMU\n(50Hz I2C)"]
        BAT["Battery ADC Divider\n(GPIO 34)"]
        SOS_BTN["Physical SOS Button\n(GPIO 4 Active LOW)"]
        
        ESP32["ESP32 DevKit V1\nMain Controller"]
        
        HAPTIC["Vibration Motor\n(MOSFET PWM)"]
        BUZZER["Active Buzzer\n(Transistor)"]
        DFPLAYER["DFPlayer Mini + Speaker\n(Voice Prompts)"]
        
        TFLUNA -->|Distance & Flux| ESP32
        NEOGPS -->|NMEA Sentences| ESP32
        MPU -->|Accel & Gyro| ESP32
        BAT -->|Analog Voltage| ESP32
        SOS_BTN -->|Hardware Press| ESP32
        
        ESP32 -->|Immediate Local Feedback| HAPTIC
        ESP32 -->|Immediate Local Feedback| BUZZER
        ESP32 -->|Immediate Voice Alerts| DFPLAYER
    end

    subgraph VISION_NODE ["AI Vision Companion Node"]
        CAM_MODULE["AI-Thinker ESP32-CAM\n(OV2640 Sensor)"]
    end

    subgraph BACKEND_PLATFORM ["FastAPI Central Backend & Database"]
        REST_API["REST Endpoints\n/api/device/data\n/api/events\n/api/sos\n/api/guardian/*"]
        VISION_ENDPOINT["Vision Inference\n/api/vision/infer"]
        YOLO["YOLOv8n Inference Engine\n(CPU/GPU Pipeline)"]
        SQLITE[("SQLite Database\nSmart_blind_stick.db")]
        WS_HUB["WebSocket Manager\n/ws/device/{device_id}"]
        HEARTBEAT_SCANNER["Heartbeat Monitor\nOffline Transition Watcher"]
        
        VISION_ENDPOINT --> YOLO
        YOLO --> REST_API
        REST_API --> SQLITE
        REST_API --> WS_HUB
        SQLITE <--> HEARTBEAT_SCANNER
        HEARTBEAT_SCANNER --> WS_HUB
    end

    subgraph GUARDIAN_CLIENTS ["Guardian Client Applications"]
        EXPO_APP["React Native Expo Mobile App\n(Android / iOS / Web)"]
        WEB_QR["Mobile Access QR Portal\n(Web Companion)"]
    end

    ESP32 -->|Periodic HTTP Check-in & Events| REST_API
    CAM_MODULE -->|JPEG Frame Upload| VISION_ENDPOINT
    WS_HUB -->|Real-Time Push Updates| EXPO_APP
    EXPO_APP <-->|JWT Authenticated REST| REST_API
    WEB_QR -.->|Launches App / Web URL| EXPO_APP
```

---

## 1. Architectural Layers & Responsibilities

### 1.1 Local Autonomous Safety Layer (Hard Real-Time)
- **Zero Cloud Dependency for Immediate Safety**: The user walking with the stick must never be endangered by Wi-Fi disconnection or cloud network latency.
- If an obstacle appears within 50cm, the TF-Luna driver on the ESP32 activates the vibration motor and active buzzer within **< 50 milliseconds**.
- If a candidate fall is confirmed by the MPU6050 pipeline, immediate local vocal guidance ("Fall detected") and haptic pulses trigger instantaneously.

### 1.2 Telemetry & Dispatch Layer (Soft Real-Time)
- The ESP32 collects valid sensor telemetry, validates ranges, rejects stale readings, and posts JSON payloads to `/api/device/data` every 3000ms.
- An **offline bounded event queue** buffers up to 10 critical alerts (SOS and confirmed falls) if Wi-Fi is temporarily lost, flushing them automatically upon reconnection.

### 1.3 Vision Companion Node
- The ESP32-CAM runs as an independent companion node on the stick body.
- It captures JPEG frames and POSTs them to `/api/vision/infer`.
- The FastAPI server runs YOLOv8n, tracks approaching objects across consecutive frames, and generates high-risk warnings if vehicles are approaching.

### 1.4 Guardian App & Real-Time Sync Layer
- The React Native Expo mobile application connects to the backend via JWT-authenticated REST APIs and a persistent WebSocket stream.
- The backend relays genuine sensor events to paired guardians in real-time.

---

## 2. Zero-Demo-Data Principles Across the System

| System State | Legacy Prototype Behavior | DrishtiGuard Real-Hardware Behavior |
| :--- | :--- | :--- |
| **No stick paired to guardian** | Displayed fake stick with canned 90% battery | Renders genuine empty state: `"No device paired yet"` |
| **Device powered off / offline**| Statically showed "Online" if backend was running| Checks `last_seen` timestamp. If > 30s: shows `"⚪ OFFLINE"` with last known info |
| **GPS receiver has no satellite fix**| Published fake coordinates `(15.85, 74.50)` | Reports `gps_available = false`, map shows `"No data available"` or `"GPS fix unavailable"` |
| **Battery ADC sensing unpopulated** | Fabricated random fluctuating percentage | Reports `battery = null`, battery card shows `"No data available"` |
| **No incident events in database** | Displayed fabricated fake alerts list | Renders `"No events recorded"` |
| **Camera disconnected or weights missing** | Fabricated synthetic object detections | Returns `"vision_unavailable"`, displays `"Vision unavailable"` |
