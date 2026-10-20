# 🦯 Smart Blind Stick — Complete 23-Feature AI Vision & Mobility System

> An AI-powered assistive mobility system engineered for visually impaired individuals, combining multi-sensor IoT, computer vision, real-time GPS tracking, and intelligent guardian safety assistance.

---

## 📌 Complete Master Feature List (23 Features)

The application strictly implements and organizes **only these 23 features** across 6 core functional categories:

```text
========================================================================================
                          SMART BLIND STICK ARCHITECTURE
========================================================================================
  [1. Core Safety]          [2. AI & Intelligent]        [3. Navigation]
   • Real-Time Obstacles     • AI Object Recognition       • Voice Navigation
   • Multi-Level Detection   • Type Classification         • Safe Route Recommendation
   • Sensor Fusion           • Moving Object Tracking      • Geofencing Safe Zones
   • Alert Prioritization    • Fall Detection (IMU)
   • Directional Haptics     • Intelligent SOS System
----------------------------------------------------------------------------------------
  [4. Personalization]      [5. Mobile & Guardian]       [6. Innovative & Reliability]
   • Adaptive Alert System   • Live Stick Dashboard (PWA)  • Community Hazard Mapping
   • User Profiles           • Guardian Live Dashboard     • AI Voice Assistant
                             • Incident History Audit      • Offline Safety Mode
                                                           • Battery Intelligence
                                                           • Self-Diagnostic System
========================================================================================
```

---

## 🛡️ 1. Core Safety Features

### 1. Real-Time Obstacle Detection
* Continuously evaluates ultrasonic and IR telemetry with three risk zones:
  * **Safe** (> 1.8m): Green indicator, clear walking path.
  * **Caution** (0.8m – 1.8m): Amber indicator, spoken alert, medium pulse vibration.
  * **Danger / Imminent Collision** (< 0.8m / < 0.4m): Red emergency indicator, continuous tactile vibration, audible alarm buzzer.
* Interactive 360° sweeping Radar HUD on the Live Stick Mobile Companion (`/app`).

### 2. Multi-Level Obstacle Detection
* Evaluates distinct vertical sensor levels simultaneously:
  * **Ground-level**: Potholes, curbs, downward steps, edges, drop-offs.
  * **Waist-level**: Low barriers, fire hydrants, tables, desks.
  * **Chest-level**: Mid-height railings, posts, construction fences.
  * **Head-level**: Overhanging branches, signs, awnings, suspended obstructions.
* Visual elevation indicators highlight the exact level of impending hazards.

### 3. Intelligent Sensor Fusion
* Blends inputs from Ultrasonic sensors, Ground IR, 6-Axis IMU (accelerometer/gyro), and GPS data.
* **Cane Swing Filtering**: Detects natural arm pendulum sweeping (`imu_swing_velocity > 250°/s`) and orientation tilt (`imu_tilt_deg > 55°`) to eliminate spurious peripheral reflections.
* Computes an environmental **Path Safety Score** (0% to 100%).

### 4. Smart Alert Prioritization
* Prioritizes threats through a dynamic 5-level queue based on distance, trajectory, direction, and hazard severity:
  * `P1 - CRITICAL`: Imminent collision (< 0.4m) or moving vehicle on direct path.
  * `P2 - HIGH`: Potholes, drop-offs, close obstacles (< 1.0m).
  * `P3 - MEDIUM`: Cautionary obstacles (1.0m – 1.8m), overhanging tree branches.
  * `P4 - LOW`: Distant objects (> 1.8m).
  * `P5 - INFO`: Path clear, diagnostic notifications.

### 5. Direction-Based Haptic Feedback
* Generates distinct tactile vibration patterns (supported via Web Vibration API `navigator.vibrate` and physical ERM/LRA vibration actuators):
  * **Left Obstacle**: `[150, 100, 150]` (Left directional pulse)
  * **Right Obstacle**: `[300, 100, 100]` (Right directional pulse)
  * **Center Caution**: `[180, 120, 180]` (Balanced double pulse)
  * **Pothole / Drop-off**: `[80, 40, 80, 40, 80]` (Rapid ground staccato tap)
  * **Immediate Danger**: `[500, 50, 500, 50, 500]` (Continuous emergency vibration)

---

## 👁️ 2. AI and Intelligent Features

### 6. AI-Based Object Recognition
* Camera feed analyzed by YOLOv8n detector with monocular distance and bounding-box estimation.
* Detects and classifies the **10 target mobility categories**:
  1. `People` (`person`)
  2. `Vehicles` (`car`, `bus`, `truck`)
  3. `Bicycles` (`bicycle`)
  4. `Motorcycles` (`motorcycle`)
  5. `Poles` (`pole`, `traffic light`, `stop sign`, `fire hydrant`)
  6. `Trees` (`tree`, `potted plant`)
  7. `Staircases` (`staircase`, `steps`)
  8. `Doors` (`door`)
  9. `Chairs` (`chair`, `bench`, `couch`)
  10. `Walls` (`wall`, `barrier`)

### 7. Obstacle Type Classification
* Combines AI visual labels, distance in meters, and direction (Left / Center / Right) to generate clear spoken alerts (e.g. *"Caution: Chair, 1.2 meters, Left"*).

### 8. Moving Object Detection
* Tracks bounding box scale changes across successive frames:
  * Estimates closing velocity ($v = \frac{\Delta d}{\Delta t}$).
  * Identifies approaching vehicles/pedestrians ($v > 0.5\text{ m/s}$) on collision trajectories and triggers urgent priority alerts.

### 9. Fall Detection
* 3-phase IMU accelerometer & tilt state machine:
  1. Free-fall drop ($< 0.6g$)
  2. High-impact spike ($> 2.4g$)
  3. Post-impact resting posture ($> 40^\circ$ tilt)
* Initiates an acoustic and visual 20-second confirmation window before auto-escalating to SOS.

### 10. Intelligent SOS System
* Dual trigger: Manual physical SOS button or Automatic fall confirmation timeout.
* Dispatches alert with live GPS coordinates, Google Maps link, and notification history.
* Includes a 20-second **"I'm OK (Cancel Alarm)"** window to prevent false alarms.
* Guardian live tracking and resolution logging.

---

## 🧭 3. Navigation Features

### 11. Voice Navigation
* Turn-by-turn spoken guidance delivered via natural browser Speech Synthesis (`window.speechSynthesis`).
* Clear directional cues (e.g., *"Turn left in 15 meters onto Market Street"*, *"Continue straight for 60 meters on tactile pavement"*).

### 12. Safe Route Recommendation
* Generates pedestrian routes optimized for accessibility:
  * Avoids steep stairs in favor of gentle access ramps.
  * Avoids high-traffic arterial roads.
  * Bypasses active construction zones and reported potholes.
* Provides a route **Safety Index** (e.g., 96% Safe Route).

### 13. Geofencing
* Guardians can define safe geographic boundaries (Center coordinate + Radius, e.g. Home Safe Zone 350m).
* Real-time distance tracking using the Haversine formula; automatically logs breach alerts if the stick exits the perimeter.

---

## 👤 4. Personalization Features

### 14. Adaptive Alert System
* Dynamically tunes alert distance and filters based on user environment:
  * **Standard Mode** (2.2m threshold for normal daily walking)
  * **High Sensitivity Mode** (3.2m threshold for unfamiliar or dark routes)
  * **Crowded Street Mode** (filters distant static objects, focuses on obstacles $< 1.2\text{m}$ and moving vehicles)

### 15. User Profiles
* Complete personalized profile stored in database:
  * Alert distance threshold ($1.0\text{m} - 4.0\text{m}$)
  * Audio speech volume ($0\% - 100\%$)
  * Vibration intensity (`gentle`, `medium`, `intense`)
  * Navigation voice (`female_en`, `male_en`, `neutral`)
  * Walking speed (`slow`, `normal`, `fast`)
  * Emergency contact name, phone number, and relationship.

---

## 📱 5. Mobile Application and Monitoring Features

### 16. Live Stick Dashboard
* High-performance Progressive Web App (PWA) at `/app`.
* Real-time stick HUD: battery %, GPS fix type & satellite count, multi-sensor elevation readouts, online/offline status pill, and path safety score.

### 17. Guardian Dashboard
* Caregiver monitoring portal at `/dashboard`.
* Live interactive Leaflet map tracking stick position, breadcrumb trail, geofence boundary circle, and emergency resolution controls.

### 18. Incident History
* Persistent audit log recording safety-critical events:
  * Approaching vehicles
  * Ground potholes and drop-offs
  * Fall impact events
  * Manual SOS button presses
* Filterable by device ID, risk level, and timestamp.

---

## 🚀 6. Innovative and Reliability Features

### 19. Community Hazard Mapping
* Crowdsourced hazard database collecting anonymous reports of:
  * Potholes
  * Construction excavations
  * Blocked sidewalks / low-hanging branches
  * Dangerous road crossings
* Displayed as interactive hazard pins on the map and avoided during route generation.

### 20. AI Voice Assistant
* Spoken query assistant with speech recognition:
  * *"Where am I?"* $\rightarrow$ Spoken street coordinates and geofence status.
  * *"Is there anything ahead?"* $\rightarrow$ Spoken obstacle distance and elevation summary.
  * *"What is my battery level?"* $\rightarrow$ Spoken percentage, power mode, and hours remaining.

### 21. Offline Safety Mode
* Local microcontroller / in-browser fallback guarantees:
  * Obstacle distance radar, multi-level sensors, direction haptic pulses, and local fall detection remain 100% operational even without internet connectivity.

### 22. Battery Intelligence
* Adaptive power management:
  * **Normal Mode** ($>30\%$): All sensors, AI camera, and high-precision GPS active.
  * **Power-Saving Mode** ($15\% - 30\%$): Throttled GPS sampling interval, optimized AI processing.
  * **Critical-Battery Mode** ($<15\%$): Ultrasonic and haptics prioritized, vital reserves held for emergency SOS.

### 23. Self-Diagnostic System
* Automated startup test checking 7 critical components:
  1. Ultrasonic Array (Head / Chest / Waist)
  2. Ground IR Optical Sensor
  3. NEO-6M GPS Receiver
  4. ERM Haptic Vibration Motor
  5. MPU-6050 6-Axis IMU
  6. Li-Ion Battery BMS
  7. Cloud / Network Connectivity
* Generates component Pass/Fail report with spoken startup announcement.

---

## 🚀 Quick Start Guide

### 1. Start Backend & Open Web Interfaces

```bash
# Launch the backend server
python run.py
```

* **Live Stick Mobile Companion (PWA)**: [http://127.0.0.1:8000/app](http://127.0.0.1:8000/app)
* **Guardian Live Monitor Dashboard**:   [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard)
* **Interactive API Swagger Docs**:     [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Or run the Master System Launcher:
```bash
python run_all.py
```

### 2. Run Automated Test Suite (75 Tests)

```bash
.venv\Scripts\python.exe -m pytest -v
```

All 75 automated tests covering all 23 features pass with 100% green status.

---

## 📡 REST API Reference

| Category | Endpoint | Method | Description |
| :--- | :--- | :--- | :--- |
| **Core Safety** | `/api/sensors/data` | `POST` | Multi-level obstacle ingestion, intelligent fusion, direction haptics |
| **Emergency** | `/api/emergency/sos/manual` | `POST` | Trigger manual emergency SOS |
| **Emergency** | `/api/emergency/fall/detect` | `POST` | Report IMU fall telemetry & trigger countdown |
| **Emergency** | `/api/emergency/sos/cancel` | `POST` | Cancel false alarm ("I'm OK") |
| **Emergency** | `/api/emergency/sos/resolve` | `POST` | Guardian resolves emergency incident |
| **Navigation** | `/api/features/navigation/safe-route` | `POST` | Generate accessible safe pedestrian route |
| **Navigation** | `/api/features/geofences/{device_id}` | `GET/POST` | Manage safe zone perimeters |
| **Navigation** | `/api/features/geofences/check/{device_id}` | `POST` | Real-time boundary breach detector |
| **Personalization** | `/api/features/profile/{device_id}` | `GET/PUT` | User profile & adaptive sensitivity mode |
| **Hazards** | `/api/features/hazards` | `GET/POST` | Community hazard registry |
| **Assistant** | `/api/features/assistant/query` | `POST` | AI Voice Assistant spoken query processor |
| **Reliability** | `/api/features/battery/{device_id}` | `GET` | Battery intelligence status & runtime estimate |
| **Reliability** | `/api/features/diagnostics/run/{device_id}` | `POST` | Execute 7-component hardware self-test |
| **Incidents** | `/api/events/{device_id}` | `GET` | Audit trail of past incidents & hazard events |

---

## 🔌 Hardware Wiring Diagram (Microcontroller Bridge)

```text
       ESP32 / Arduino Microcontroller
    ┌───────────────────────────────────┐
    │  GPIO 5  ──────> Ultrasonic Trig  │
    │  GPIO 18 <────── Ultrasonic Echo  │
    │  GPIO 19 <────── Ground IR Sensor │
    │  GPIO 21 <────── SDA (MPU-6050)   │
    │  GPIO 22 <────── SCL (MPU-6050)   │
    │  GPIO 16 <────── RX2 (GPS TX)     │
    │  GPIO 17 ──────> TX2 (GPS RX)     │
    │  GPIO 4  ──────> ERM Haptic Motor │
    │  GPIO 2  ──────> Buzzer Alarm     │
    │  GPIO 34 <────── Li-Ion ADC Pin   │
    │  GPIO 15 <────── Pushbutton (SOS) │
    └───────────────────────────────────┘
```
