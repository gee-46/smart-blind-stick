"""
main.py
-------
Demo entry point for the sensor fusion module.

Runs in SIMULATION mode automatically if the hardware libraries
(pyserial, adafruit_vl53l1x) aren't available -- e.g. testing on your
laptop before wiring the physical stick.

Current hardware layout (update if the team adds more sensors):

    TF-Mini S LiDAR   - center, chest/head height -> forward long-range hazards
    VL53L1X ToF       - center, ground level       -> drop-offs/steps/potholes

INTEGRATION: every cycle, the latest obstacle data is written to a shared
JSON file (OUTPUT_FILE_PATH below) that the other modules (alert engine,
mobile app / Guardian backend) can read from. Since everything runs on
one Raspberry Pi, this avoids the overhead of sockets/MQTT for a
single-device setup. Confirm the exact path with your team.
"""

import json
import time

from sensors import TFMiniLidar, VL53L1XSensor, Direction, HeightLevel
from fusion import SensorFusionEngine

# Shared file other modules read from. Change this path if the team
# agrees on a different location (e.g. a shared /data folder).
OUTPUT_FILE_PATH = "/tmp/obstacle_data.json"


def build_sensor_array(simulate=True):
    return [
        TFMiniLidar("lidar_center_chest", Direction.CENTER, HeightLevel.CHEST_HEAD,
                    serial_port="/dev/serial0", baudrate=115200, simulate=simulate),
        VL53L1XSensor("tof_center_ground", Direction.CENTER, HeightLevel.GROUND,
                      i2c_address=0x29, simulate=simulate),
    ]


def write_output(output: dict, path: str = OUTPUT_FILE_PATH):
    """
    Write the latest fused obstacle data to a shared file.
    Writes to a temp file first, then renames it into place -- this
    avoids other modules ever reading a half-written/corrupted file
    (atomic on POSIX systems, which the Pi's Linux OS is).
    """
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w") as f:
        json.dump(output, f, indent=2)
    import os
    os.replace(tmp_path, path)


def run(loop_interval_s=0.2, iterations=10, write_to_file=True):
    sensors = build_sensor_array(simulate=True)  # flip to False on real hardware
    engine = SensorFusionEngine(sensors, filter_window=5)

    for i in range(iterations):
        output = engine.get_standard_output()
        print(f"\n--- Cycle {i + 1} ---")
        print(json.dumps(output, indent=2))

        if write_to_file:
            write_output(output)

        time.sleep(loop_interval_s)


if __name__ == "__main__":
    run()
