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

- Device communication (check-in: battery, GPS, status)
- Device online/offline monitoring
- GPS location tracking + history
- Generic event ingestion (sensor fusion / AI vision / safety engine)
- Incident history with filtering (event type, risk level, date)
- SOS endpoint with a swappable notification-service abstraction
- Mock device simulator (test the whole backend without hardware)
- Full REST API with interactive docs
- Automated tests (pytest) — no hardware required

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

| Method | Endpoint                                | Description                          |
|--------|------------------------------------------|---------------------------------------|
| POST   | `/api/device/data`                      | Device check-in (battery, GPS, status) |
| GET    | `/api/device/status/{device_id}`        | Device online/offline status          |
| GET    | `/api/location/{device_id}`             | Latest known location                 |
| GET    | `/api/location/{device_id}/history`     | Location history                      |
| POST   | `/api/events`                           | Submit an event (any module)          |
| GET    | `/api/events/{device_id}`               | Incident history (filterable)         |
| POST   | `/api/sos`                              | Trigger an SOS                        |
| GET    | `/health`                               | Health check                          |

### Event filtering

`GET /api/events/{device_id}` supports optional query params:
`event_type`, `risk_level`, `date` (ISO `YYYY-MM-DD`), `limit`.

## Database Schema

- **Device** — `device_id` (unique), `battery`, `status`, cached last
  latitude/longitude, `gps_available`, `last_seen`, `created_at`
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

Tests use a separate SQLite test database and FastAPI's `TestClient`, so
no hardware or running server is required. Covers device check-in/status,
GPS storage/history, event creation/filtering/retrieval, SOS, and
validation errors (invalid data, unknown device).

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

1. Other team members start against `POST /api/events` using the
   contract above — they can develop and test their modules against this
   backend today, using `scripts/simulate_device.py` as a reference for
   how to call the API.
2. Add a lightweight auth/API-key check on device-facing endpoints before
   any real deployment.
3. Replace `MockNotificationService` with a real SMS/Firebase/WhatsApp
   integration once the safety-emergency module defines exact alerting
   requirements.
4. Add a WebSocket or polling endpoint if the future mobile app needs
   live updates instead of request/response polling.
5. When ready, swap `DATABASE_URL` to PostgreSQL for a shared team
   development database.
