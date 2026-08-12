# Smart Blind Stick — Mobile & IoT Backend

Python backend for the **Smart Blind Stick Using IoT, Sensors, GPS and AI**
final-year project. This module (`feature/mobile-iot`) provides the
backend foundation — device communication, GPS tracking, event ingestion,
and SOS handling — that the other three modules connect to:

- `feature/sensor-fusion` — ultrasonic, IR, IMU processing
- `feature/ai-vision` — camera + object detection
- `feature/safety-emergency` — risk assessment, alerts, fall detection, SOS

This module does **not** implement those three modules. It only exposes
the API contract they will send data to.

## Features

**Milestone 1 (REST foundation)**
- Device communication (check-in: battery, GPS, status)
- Device online/offline monitoring
- GPS location tracking + history, real GPS hardware support (NEO-6M/NMEA)
- Generic event ingestion (sensor fusion / AI vision / safety engine)
- Incident history with filtering (event type, risk level, date)
- SOS endpoint with a swappable notification-service abstraction
- Mock device simulator (test the whole backend without hardware)
- Full REST API with interactive docs

**Milestone 2 (real-time layer)**
- Device authentication: registration issues a hashed, one-time-shown API key
- WebSocket device connection (`/ws/device/{device_id}`) with mandatory
  auth handshake before any data is accepted
- Heartbeat: lightweight liveness pings over WS + a background task that
  detects and broadcasts online/offline transitions
- Live GPS updates over WebSocket (same validation/storage as the REST
  check-in, just pushed in real time)
- Real-time event streaming (sensor fusion / AI vision / safety engine
  events broadcast to watchers as they happen)
- SOS over WebSocket
- Monitor/dashboard WebSockets (`/ws/monitor/{device_id}` and
  `/ws/monitor` for all devices) for a future mobile app or dashboard to
  watch live

- Automated tests (pytest) — no hardware required, 78 tests total

## Architecture

```text
Smart Stick (hardware or simulator)
            |
            v
        FastAPI  (app/api/*.py)      <- thin HTTP layer, validation via Pydantic
            |
            v
        Services (app/services/*.py) <- business logic
            |
            v
        SQLAlchemy models (app/models/*.py)
            |
            v
        SQLite  (swap DATABASE_URL for PostgreSQL later — no code changes)
```

Routes never touch the database directly — everything goes through the
service layer, so business logic is testable and reusable independent of
FastAPI.

## Project Structure

```text
smart-blind-stick/
├── app/
│   ├── main.py              # FastAPI app, router wiring, startup
│   ├── config.py            # Environment-based settings
│   ├── api/                 # HTTP route handlers
│   │   ├── device.py
│   │   ├── location.py
│   │   ├── events.py
│   │   └── sos.py
│   ├── models/               # SQLAlchemy ORM models
│   │   ├── device.py
│   │   ├── location.py
│   │   └── event.py          # Event + SOSEvent
│   ├── schemas/               # Pydantic request/response schemas
│   │   ├── device.py
│   │   ├── location.py
│   │   └── event.py
│   ├── services/               # Business logic
│   │   ├── device_service.py
│   │   ├── location_service.py
│   │   ├── event_service.py
│   │   └── notification_service.py
│   └── database/
│       ├── base.py           # Declarative Base
│       └── database.py       # Engine, session, get_db, init_db
├── tests/                     # pytest test suite
├── scripts/
│   └── simulate_device.py    # Mock device simulator
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── run.py
```

## Installation

```bash
python -m venv .venv
```

Activate it:

- Windows: `.venv\Scripts\activate`
- macOS/Linux: `source .venv/bin/activate`

Install dependencies:

```bash
pip install -r requirements.txt
```

Copy the environment file (optional — sensible defaults are built in):

```bash
cp .env.example .env
```

## Running

```bash
python run.py
```

The API will be available at `http://127.0.0.1:8000`, and interactive
API docs (Swagger UI) at:

```text
http://127.0.0.1:8000/docs
```

## API Endpoints

### REST

| Method | Endpoint                                | Description                          |
|--------|------------------------------------------|---------------------------------------|
| POST   | `/api/device/data`                      | Device check-in (battery, GPS, status) — unauthenticated, unchanged since Milestone 1 |
| POST   | `/api/device/register`                  | Register a device, issue its API key (Milestone 2, shown once) |
| GET    | `/api/device/status/{device_id}`        | Device online/offline status          |
| GET    | `/api/location/{device_id}`             | Latest known location                 |
| GET    | `/api/location/{device_id}/history`     | Location history                      |
| POST   | `/api/events`                           | Submit an event (any module)          |
| GET    | `/api/events/{device_id}`               | Incident history (filterable)         |
| POST   | `/api/sos`                              | Trigger an SOS                        |
| GET    | `/health`                               | Health check                          |

### WebSocket (Milestone 2)

| Endpoint                          | Who connects           | Auth required |
|------------------------------------|--------------------------|----------------|
| `WS /ws/device/{device_id}`       | The smart stick itself   | Yes — first message must be `{"type": "auth", "api_key": "..."}` |
| `WS /ws/monitor/{device_id}`      | Dashboard watching one device | No (see Security notes) |
| `WS /ws/monitor`                  | Dashboard watching all devices | No (see Security notes) |

**Device → server message types** (after auth): `heartbeat`,
`location_update`, `event`, `sos`. Each is acknowledged
(`heartbeat_ack`, `location_update_ack`, `event_ack`, `sos_ack`) and, for
`location_update`/`event`/`sos`, broadcast live to any monitors watching
that device. Malformed messages get an `{"type": "error", ...}` reply —
the connection is never dropped for a bad message, only for a failed
auth handshake.

**Server → monitor broadcast types**: `location_update`, `event`, `sos`,
`device_online`, `device_offline` (the last two come from the background
heartbeat scanner, not directly from the device).

See `app/api/ws.py` for the full message contract and every field.

### Event filtering

`GET /api/events/{device_id}` supports optional query params:
`event_type`, `risk_level`, `date` (ISO `YYYY-MM-DD`), `limit`.

### Security notes

- `/api/device/data` and `/api/events` remain **unauthenticated** by
  design for Milestone 2 — the former for backward compatibility with
  existing devices/tests, the latter because the other three modules
  (`sensor-fusion`, `ai-vision`, `safety-emergency`) are still finalizing
  their interfaces. Both are natural candidates for auth in a later
  milestone once those interfaces settle.
- The monitor WebSockets are also unauthenticated for now (anyone who
  can reach the server can watch live device data) — acceptable for a
  single-team dev/demo environment, but flagged here as a follow-up item
  before any real deployment (e.g. a simple shared dashboard token).
- API keys are never stored or logged in plaintext — only their SHA-256
  hash. If a key is lost, there's currently no rotation endpoint; the
  device would need a new `device_id` or a rotation endpoint added later.

## Database Schema

- **Device** — `device_id` (unique), `battery`, `status`, cached last
  latitude/longitude, `gps_available`, `last_seen`, `created_at`,
  `api_key_hash` (Milestone 2, null until registered), cached
  `last_fix_quality` / `last_satellites`
- **Location** — `device_id` (FK), `latitude`, `longitude`, `timestamp`
  (one row per check-in — full history)
- **Event** — `device_id` (FK), `source`, `event_type`, `risk_level`,
  `message`, `extra` (JSON, module-specific fields), `timestamp`
- **SOSEvent** — `device_id` (FK), `reason`, `latitude`, `longitude`,
  `notified`, `timestamp`

All development uses SQLite (`smart_blind_stick.db`, git-ignored). To
move to PostgreSQL later, only `DATABASE_URL` in `.env` needs to change,
e.g.:

```text
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/smart_blind_stick
```

## Testing

```bash
pytest
```

78 tests, no hardware or running server required (uses a separate SQLite
test database, FastAPI's `TestClient` for REST, and Starlette's
in-process `websocket_connect` for WebSocket tests). Covers device
check-in/status, GPS storage/history, real GPS field storage, NMEA
parsing, event creation/filtering/retrieval, SOS, validation errors,
device registration/API keys, WebSocket auth (success/failure/timeout
paths), heartbeat, live GPS updates, real-time event streaming, SOS over
WebSocket, monitor broadcasting (per-device and global), and connection
manager cleanup.

## WebSocket Quickstart

```python
import asyncio, json, websockets

async def main():
    # 1. Register once, save the key
    # curl -X POST http://127.0.0.1:8000/api/device/register \
    #      -d '{"device_id": "STICK_001"}'
    api_key = "...the key from registration..."

    async with websockets.connect("ws://127.0.0.1:8000/ws/device/STICK_001") as ws:
        await ws.send(json.dumps({"type": "auth", "api_key": api_key}))
        print(await ws.recv())  # {"type": "auth_success", ...}

        await ws.send(json.dumps({
            "type": "location_update", "battery": 82,
            "latitude": 15.85, "longitude": 74.50, "status": "moving"
        }))
        print(await ws.recv())  # {"type": "location_update_ack", ...}

asyncio.run(main())
```

To watch it live from a second connection:

```python
async with websockets.connect("ws://127.0.0.1:8000/ws/monitor/STICK_001") as monitor:
    print(await monitor.recv())  # monitor_connected
    print(await monitor.recv())  # the location_update, pushed live
```

## Real GPS Hardware

For an actual physical GPS module (NEO-6M or any NMEA-0183-compatible
chip) on a Raspberry Pi or microcontroller, use
`scripts/gps_device_client.py` instead of the mock simulator. It's a
drop-in hardware counterpart — it posts to the exact same
`/api/device/data` endpoint, so no backend changes are needed to go from
mock to real hardware.

**Wiring** (Raspberry Pi + NEO-6M example — see the full docstring in
`scripts/gps_reader.py` for exact pin numbers and `raspi-config` steps
to free up the UART):

```text
GPS module      Raspberry Pi
VCC        ->   5V (check your module's voltage — some need 3.3V)
GND        ->   GND
TX         ->   GPIO15 / RXD
RX         ->   GPIO14 / TXD
```

**Run it:**

```bash
python scripts/gps_device_client.py --device-id STICK_001
# custom serial port / baud rate / backend location:
python scripts/gps_device_client.py --port /dev/ttyUSB0 --baud 9600 --base-url http://192.168.1.50:8000
```

It reads real NMEA sentences off the serial port (`scripts/gps_reader.py`
parses GGA for position/altitude/satellites/fix-quality, and RMC for
ground speed), and only sends a check-in once it has an actual fix — if
the module is still acquiring satellites (common for the first
30–60 seconds, especially indoors), it logs "No GPS fix yet" and waits
rather than sending stale or zeroed coordinates.

The extra fields (`altitude`, `speed_kmh`, `satellites`, `fix_quality`)
are optional on `/api/device/data` and are stored on every `Location`
row and cached on the `Device` row — the mock simulator simply omits
them, so both paths work against the same backend and same tests.

**Testing without hardware attached:** `tests/test_gps_reader.py`
verifies the NMEA parsing itself (valid fix, no-fix, corrupted
checksums, speed attachment) using a fake in-memory serial stream — no
physical module required to run `pytest`.

## Mock Device Simulator

Since no physical hardware exists yet, `scripts/simulate_device.py`
mimics a smart stick sending periodic check-ins and occasional events.

Start the backend first, then in another terminal:

```bash
python scripts/simulate_device.py
```

Options:

```bash
python scripts/simulate_device.py --device-id STICK_002 --interval 3
python scripts/simulate_device.py --once            # single check-in, then exit
python scripts/simulate_device.py --base-url http://127.0.0.1:8000
```

GPS points are generated by a mock GPS function
(`app/services/location_service.py::generate_mock_gps_point`) — this is
explicitly **not** real GPS hardware, and is isolated in one function so
it's a one-line swap once real hardware is available.

## Integration Contract for Teammates

All three other modules send data through **the same two endpoints**:
`POST /api/device/data` (for stick position, if the module has GPS-aware
context) and, primarily, `POST /api/events`. Your module does not need
this backend to be running its other modules to be developed against.

The generic event shape:

```json
{
  "device_id": "STICK_001",
  "source": "sensor_fusion | ai_vision | safety_engine",
  "event_type": "obstacle | object_detected | danger | ...",
  "risk_level": "low | medium | high | critical",
  "message": "human-readable summary",
  "extra": { "...module-specific fields go here..." }
}
```

### `feature/sensor-fusion`

```json
{
  "device_id": "STICK_001",
  "source": "sensor_fusion",
  "event_type": "obstacle",
  "risk_level": "medium",
  "message": "Obstacle detected on left",
  "extra": {
    "distance": 1.4,
    "direction": "left",
    "level": "head",
    "confidence": 0.91
  }
}
```

### `feature/ai-vision`

```json
{
  "device_id": "STICK_001",
  "source": "ai_vision",
  "event_type": "object_detected",
  "risk_level": "high",
  "message": "Vehicle approaching from right",
  "extra": {
    "object": "vehicle",
    "distance": 2.1,
    "direction": "right",
    "movement": "approaching",
    "confidence": 0.94
  }
}
```

### `feature/safety-emergency`

```json
{
  "device_id": "STICK_001",
  "source": "safety_engine",
  "event_type": "danger",
  "risk_level": "critical",
  "message": "Vehicle approaching from right"
}
```

Anything module-specific (distance, direction, confidence, object,
level, ...) goes in `extra` — it's stored as JSON, so new fields never
require a database migration.

Safety-emergency can also call `POST /api/sos` directly if it decides an
SOS should be triggered automatically (e.g. after a fall-detection
event), using the same shape a manual SOS button press would use.

## Next Recommended Development Step

**Milestone 2 status: complete.** Device authentication, WebSocket
device connections, heartbeat monitoring, live GPS updates, real-time
event streaming, SOS over WebSocket, and monitor/dashboard streaming are
all implemented and tested (see "WebSocket (Milestone 2)" above).

Recommended next steps:

1. Other team members continue building against `POST /api/events`
   (still open, unauthenticated) — they can develop and test their
   modules against this backend today.
2. Secure `/api/events` and the monitor WebSockets once the other three
   modules' interfaces are finalized (see "Security notes" above).
3. Replace `MockNotificationService` with a real SMS/Firebase/WhatsApp
   integration once the safety-emergency module defines exact alerting
   requirements.
4. Add a key-rotation endpoint for devices that lose their API key.
5. Build the mobile/dashboard frontend against the now-available
   `/ws/monitor` endpoints (still out of scope for this branch).
6. When ready, swap `DATABASE_URL` to PostgreSQL for a shared team
   development database — note that the in-memory `ConnectionManager`
   would then need to move to a shared broker (e.g. Redis pub/sub) if
   the backend is horizontally scaled across multiple processes.
