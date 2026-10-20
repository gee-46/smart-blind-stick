# DrishtiGuard Device Communication Protocol Specification

> **Version:** 1.0.0-hw  
> **Source of Truth:** FastAPI Backend (`app/main.py`)

---

## 1. Overview

The DrishtiGuard smart stick communicates with the backend via two complementary channels:
1. **HTTP/REST Ingestion (Reliable & Fire-and-Forget)**: Periodic full-sensor telemetry check-ins, event creation, emergency SOS dispatch, and ESP32-CAM frame uploads.
2. **WebSocket Real-Time Relay (Bidirectional & Low Latency)**: Real-time sensor streaming, push notifications, and heartbeat pings between paired sticks and guardian mobile apps.

---

## 2. Authentication & Provisioning Architecture

### 2.1 Device Registration & API Key Issuance
Before a stick can access authenticated features, it is registered once:
- **Endpoint**: `POST /api/device/register`
- **Request Body**:
  ```json
  {
    "device_id": "STICK_001"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "device_id": "STICK_001",
    "api_key": "sec_49d8a3bf2e9c148a071d2b3c4f5e6a7b",
    "message": "Store this API key securely. It will not be shown again."
  }
  ```
- **Security Rule**: The backend stores **only the SHA-256 hash** of the API key (`Device.api_key_hash`). The plaintext key is returned exactly once.
- **Conflict Handling**: Re-registering an already-registered device returns `409 Conflict` to prevent overwriting keys in active hardware.

---

## 3. Telemetry Ingestion Contract

### `POST /api/device/data`
Periodic check-in sent every 3000ms by the ESP32 main controller.

#### Request Headers:
```http
Content-Type: application/json
X-API-Key: <plaintext_device_key> (Optional during bring-up, required for secure WS)
```

#### Request Payload:
```json
{
  "device_id": "STICK_001",
  "battery": 84.5,
  "latitude": 15.849723,
  "longitude": 74.497712,
  "status": "safe",
  "gps_available": true,
  "altitude": 645.2,
  "speed_kmh": 1.4,
  "satellites": 7,
  "fix_quality": 1
}
```

#### Fields Description:
| Field | Type | Description | Zero Demo Data Constraint |
| :--- | :--- | :--- | :--- |
| `device_id` | String | Unique stick identifier (max 64 chars) | Required |
| `battery` | Float / Null | Battery percentage (0.0 to 100.0) | `null` if ADC sensing is disconnected or uncalibrated. Never fake 100%. |
| `latitude` | Float | GPS latitude (-90.0 to 90.0) | Real GPS reading. Never output (0,0) as valid. |
| `longitude` | Float | GPS longitude (-180.0 to 180.0)| Real GPS reading. |
| `status` | String | Operating status: `safe`, `obstacle_critical`, `fall_detected` | Driven by real sensors. |
| `gps_available` | Boolean | `true` if valid GPS fix, `false` otherwise | Mandatory flag. |
| `altitude` | Float / Null | Elevation in meters above sea level | `null` if unavailable from NMEA sentence. |
| `speed_kmh` | Float / Null | Ground speed in km/h | `null` if unavailable. |
| `satellites` | Integer / Null| Satellites used in fix (>= 3 for valid lock) | Actual satellite count from receiver. |
| `fix_quality` | Integer / Null| NMEA GGA quality indicator (0=No Fix, 1=GPS, 2=DGPS) | Real fix quality. |

#### Response (200 OK):
```json
{
  "success": true,
  "status": "ok",
  "device_id": "STICK_001",
  "battery": 84.5,
  "last_seen": "2026-10-20T17:40:00Z",
  "is_online": true,
  "message": "Device data received"
}
```

---

## 4. Emergency SOS Event Protocol

### `POST /api/sos`
Triggered immediately when the physical hardware SOS button is long-pressed (1.2s) or a candidate fall is confirmed.

#### Request Payload:
```json
{
  "device_id": "STICK_001",
  "reason": "physical_button_pressed",
  "latitude": 15.849723,
  "longitude": 74.497712
}
```

#### Behavior & Idempotency:
- Records row in `sos_events` table.
- Dispatches emergency alert notifications to all registered emergency contacts (`app/models/guardian.py:EmergencyContact`).
- Broadcasts real-time `sos` message over WebSocket to paired guardians.
- If GPS coordinates are unavailable at the time of SOS, `latitude` and `longitude` are omitted/null; the backend preserves the last known valid location without overwriting it with zeroes.

---

## 5. Multi-Module Incident Events

### `POST /api/events`
Generic event ingestion pipeline for AI Vision, Sensor Fusion, and Safety Engine.

#### Request Payload:
```json
{
  "device_id": "STICK_001",
  "source": "ai_vision",
  "event_type": "object_detected",
  "risk_level": "high",
  "message": "Car approaching from right",
  "extra": {
    "object": "car",
    "direction": "right",
    "confidence": 0.91,
    "distance_m": 2.4
  }
}
```

---

## 6. Real-Time WebSocket Protocol

### `WS /ws/device/{device_id}`

Supports two client modes:
1. **Guardian Mobile App Mode**:
   - Connection URL: `/ws/device/{device_id}?token=<jwt_access_token>`
   - Authenticated via JWT bearer token. Guardian must own the device in `guardian_devices`.
   - Read-only subscriber receiving live `location_update`, `battery_update`, `event`, and `sos` notifications.
2. **Physical Hardware Stick Mode**:
   - Connection URL: `/ws/device/{device_id}` (no query token)
   - First message handshake:
     ```json
     {"type": "auth", "api_key": "<plaintext_key>"}
     ```
   - Server validates hash and replies:
     ```json
     {"type": "auth_success", "device_id": "STICK_001"}
     ```
   - Subsequent stick-to-server messages:
     - `{"type": "heartbeat"}` -> Server replies `{"type": "heartbeat_ack", "timestamp": "..."}`
     - `{"type": "location_update", ...}` -> Server relays to paired guardians.
     - `{"type": "sos", ...}` -> Server relays emergency alert.

---

## 7. Camera AI Vision Inference Protocol

### `POST /api/vision/infer`
Receives genuine JPEG camera frames from the ESP32-CAM companion node.

#### Request Format:
- `Content-Type`: `multipart/form-data`
- Field `file`: JPEG binary image (OV2640 buffer)
- Field `device_id`: Associated stick ID (e.g. `STICK_001`)

#### Response (200 OK):
```json
{
  "model_version": "YOLOv8n-COCO",
  "status": "success",
  "timestamp": "2026-10-20T17:42:10.124Z",
  "device_id": "STICK_001",
  "detections": [
    {
      "class_name": "car",
      "confidence": 0.884,
      "direction": "center",
      "box": {
        "x1": 84.0,
        "y1": 120.5,
        "x2": 260.0,
        "y2": 310.2
      }
    }
  ],
  "latency_ms": 38.4
}
```

#### Vision Unavailable State (When camera fails or weights are missing):
```json
{
  "model_version": "YOLOv8n-COCO",
  "status": "vision_unavailable",
  "timestamp": "2026-10-20T17:42:10.124Z",
  "device_id": "STICK_001",
  "detections": [],
  "latency_ms": 0.0,
  "message": "Vision inference model not loaded or unavailable."
}
```
*(Zero Demo Data Rule: Never generates fake bounding boxes or fabricated detections).*
