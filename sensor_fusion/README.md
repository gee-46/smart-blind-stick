# Sensor Fusion Module — Smart Blind Stick

Branch: `feature/sensor-fusion`

This module owns: reading the LiDAR + ToF sensors, filtering noise,
detecting obstacles, and producing a single standardized data feed that
the other 3 modules (AI/vision, alert engine, mobile app) consume.

## Actual hardware used

| Sensor | Role | Interface | Range | Mounted |
|---|---|---|---|---|
| TF-Mini S Micro LiDAR | Forward long-range hazard detection | UART/serial | up to 12m | chest/head height, forward-facing |
| VL53L1X Time-of-Flight | Drop-off / step / pothole detection | I2C | up to 4m | angled down at cane tip |
| MPU-6050 IMU | Orientation / fall detection | I2C | n/a | *not currently read by this module — likely owned by the fall-detection/safety teammate* |

⚠️ **Direction limitation:** there's currently only ONE forward sensor and
ONE downward sensor — no left/right array. Both are tagged `direction="center"`.
True left/right obstacle direction isn't physically possible with this
exact component list. Confirm with your team whether the AI/camera module
is expected to cover left/right, or whether side sensors should be added.
The code is structured so adding side sensors later is a one-line change
in `main.py` — no changes needed in `fusion.py`.

## Files

| File | Responsibility |
|---|---|
| `sensors.py` | Reads raw distance from TF-Mini S (serial) + VL53L1X (I2C), with simulation mode |
| `filters.py` | Removes noise/outliers from each sensor's raw stream |
| `fusion.py` | Combines sensors into fused obstacles, classifies safety, builds standard output |
| `main.py` | Example loop wiring it all together |

## How it works

1. Each physical sensor is mounted at a **direction** (left/center/right)
   and **height_level** (ground/waist/chest_head) on the stick.
2. Every cycle, each sensor is read and passed through its own noise filter.
3. Readings are grouped by `(direction, height_level)` zone.
4. If multiple sensors report the same zone and **agree** (within 40cm),
   they're fused into one high-confidence obstacle — this is what cuts
   down false alarms. If they disagree, the more trustworthy sensor type
   for that zone wins (IR for ground, ultrasonic for waist/chest) with
   lower confidence.
5. Each fused obstacle gets a status: `safe` / `caution` / `danger`
   based on distance thresholds (tune these in `fusion.py`).

## Standard Output Format (Task 9)

This is the contract the other 3 modules should build against:

```json
{
  "timestamp": 1234567890.12,
  "overall_status": "danger",
  "obstacle_count": 2,
  "obstacles": [
    {
      "direction": "center",
      "height_level": "waist",
      "distance_cm": 45.2,
      "status": "danger",
      "confidence": 0.95,
      "sensor_types": ["ultrasonic", "ir"],
      "timestamp": 1234567890.10
    }
  ]
}
```

**Integration (implemented):** `main.py` writes the latest output to
`/tmp/obstacle_data.json` every cycle (via `write_output()`). This is an
atomic write (temp file + rename) so other modules never read a
half-written file. Since everything runs on one Raspberry Pi, a shared
file avoids the overhead of sockets/MQTT.

Other modules just need to read and parse that file whenever they need
current data:

```python
import json
with open("/tmp/obstacle_data.json") as f:
    data = json.load(f)
```

Confirm the exact path with your team — change `OUTPUT_FILE_PATH` in
`main.py` if a different shared location is agreed on. Keep the JSON
shape stable — teammates should not need to change their code if you
tune thresholds or add sensors later.

## Running the demo

```bash
python3 main.py
```

Runs in **simulation mode** by default (random plausible sensor values),
so you can test/demo the logic before the stick is physically wired.

## Moving to real hardware

- In `main.py`, change `simulate=True` to `simulate=False` in `build_sensor_array()`.
- Install the hardware libraries: `pip install pyserial adafruit-circuitpython-vl53l1x`
- **TF-Mini S**: enable the Pi's hardware UART (`raspi-config` → Interface
  Options → Serial → disable login shell, enable hardware port), wire
  TX→GPIO15 (RX), 5V, GND.
- **VL53L1X**: enable I2C (`raspi-config` → Interface Options → I2C), wire
  SDA/SCL/3.3V/GND. Default address is `0x29`.
- Both `_read_hardware()` methods in `sensors.py` are real, working
  implementations (not placeholders) — test each sensor individually
  before trusting the fused output.

## Tuning

In `fusion.py`:
- `DANGER_THRESHOLD_CM` / `CAUTION_THRESHOLD_CM` — safety distance cutoffs
- `AGREEMENT_TOLERANCE_CM` — how close two sensors must agree to be fused
  as one obstacle
- `filter_window` (passed into `SensorFusionEngine`) — larger = smoother
  but slower to react to sudden new obstacles

## Testing without a partner's module ready

Each teammate can test against this module immediately by importing
`SensorFusionEngine` and calling `.get_standard_output()` — no need to
wait for real hardware or the other modules to be finished, since
simulation mode gives realistic-looking data out of the box.
