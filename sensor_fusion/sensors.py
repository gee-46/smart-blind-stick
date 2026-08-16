"""
sensors.py
----------
Low-level sensor interfaces for the Smart Blind Stick.

Matches ACTUAL hardware from the component list:
  - TF-Mini S Micro LiDAR  -> forward-facing, up to 12m, UART/serial interface
  - VL53L1X Time-of-Flight -> angled down at tip, up to 4m, I2C interface

Handles:
  - Task 1: Process ultrasonic sensor data  (LiDAR fills this role here)
  - Task 2: Process IR sensor data          (VL53L1X ToF fills this role -
            it's a laser/IR time-of-flight sensor, not analog IR, so the
            interface is I2C, not an ADC)

Supports real Raspberry Pi hardware AND a simulation mode so you can
develop/test the fusion logic before the stick is physically wired up.

NOTE ON DIRECTION: current hardware is ONE forward LiDAR + ONE downward
ToF sensor -- there's no left/right array. Both sensors are tagged
Direction.CENTER for now. If the team later adds side sensors, just
add more sensor instances with LEFT/RIGHT direction -- the fusion engine
already groups by (direction, height_level) so no fusion.py changes needed.
"""

import time
import random
from dataclasses import dataclass, field
from enum import Enum

# --- Hardware library imports (only needed in real, non-simulated mode) ----
try:
    import serial  # for TF-Mini S (pyserial)
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

try:
    import board
    import busio
    import adafruit_vl53l1x
    VL53L1X_AVAILABLE = True
except ImportError:
    VL53L1X_AVAILABLE = False

HARDWARE_AVAILABLE = SERIAL_AVAILABLE and VL53L1X_AVAILABLE


class Direction(str, Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class HeightLevel(str, Enum):
    GROUND = "ground"          # drop-offs / stairs / potholes (VL53L1X)
    WAIST = "waist"
    CHEST_HEAD = "chest_head"  # forward long-range hazards (TF-Mini S)


@dataclass
class SensorReading:
    """A single raw reading from one sensor."""
    sensor_id: str
    sensor_type: str          # "lidar" or "tof"
    direction: Direction
    height_level: HeightLevel
    distance_cm: float        # raw distance in cm (None if no valid reading)
    timestamp: float = field(default_factory=time.time)


class TFMiniLidar:
    """
    TF-Mini S Micro LiDAR.
    Forward-facing, long-range (up to 12m). Talks over UART/serial,
    NOT GPIO trigger/echo timing -- it streams distance data continuously
    in fixed-format frames over a serial port.

    Wiring: TF-Mini S TX -> Pi RX (GPIO15), 5V, GND.
    On the Pi you may need to disable the serial console and enable
    the UART hardware port (raspi-config -> Interface Options -> Serial).
    """

    FRAME_HEADER = 0x59
    MAX_RANGE_CM = 1200  # 12m

    def __init__(self, sensor_id, direction: Direction, height_level: HeightLevel,
                 serial_port="/dev/serial0", baudrate=115200,
                 simulate=not HARDWARE_AVAILABLE):
        self.sensor_id = sensor_id
        self.direction = direction
        self.height_level = height_level
        self.simulate = simulate

        if not self.simulate:
            self.ser = serial.Serial(serial_port, baudrate, timeout=0.1)

    def read(self) -> SensorReading:
        distance = self._simulate_distance() if self.simulate else self._read_hardware()
        return SensorReading(
            sensor_id=self.sensor_id,
            sensor_type="lidar",
            direction=self.direction,
            height_level=self.height_level,
            distance_cm=distance,
        )

    def _read_hardware(self):
        # TF-Mini S sends 9-byte frames: 0x59 0x59 distL distH strengthL
        # strengthH temp_L temp_H checksum
        if self.ser.in_waiting < 9:
            return None
        data = self.ser.read(9)
        if len(data) < 9 or data[0] != self.FRAME_HEADER or data[1] != self.FRAME_HEADER:
            self.ser.reset_input_buffer()
            return None
        distance_cm = data[2] + (data[3] << 8)
        if distance_cm <= 0 or distance_cm > self.MAX_RANGE_CM:
            return None
        return float(distance_cm)

    def _simulate_distance(self):
        if random.random() < 0.15:
            return None  # simulate clear path / no return signal
        return round(random.uniform(30, 1000), 1)


class VL53L1XSensor:
    """
    VL53L1X Time-of-Flight sensor.
    Angled downward at the tip of the cane, up to 4m range.
    Talks over I2C (address 0x29 by default).

    This is what fills the "ground-level / IR" role in the original
    task list -- it uses an infrared laser internally, but the
    programming interface is I2C, not an analog IR voltage reading.
    """

    MAX_RANGE_CM = 400  # 4m

    def __init__(self, sensor_id, direction: Direction, height_level: HeightLevel,
                 i2c_address=0x29, timing_budget_ms=50,
                 simulate=not HARDWARE_AVAILABLE):
        self.sensor_id = sensor_id
        self.direction = direction
        self.height_level = height_level
        self.simulate = simulate

        if not self.simulate:
            i2c = busio.I2C(board.SCL, board.SDA)
            self.sensor = adafruit_vl53l1x.VL53L1X(i2c, address=i2c_address)
            self.sensor.distance_mode = 2  # long-range mode
            self.sensor.timing_budget = timing_budget_ms
            self.sensor.start_ranging()

    def read(self) -> SensorReading:
        distance = self._simulate_distance() if self.simulate else self._read_hardware()
        return SensorReading(
            sensor_id=self.sensor_id,
            sensor_type="tof",
            direction=self.direction,
            height_level=self.height_level,
            distance_cm=distance,
        )

    def _read_hardware(self):
        if not self.sensor.data_ready:
            return None
        distance_cm = self.sensor.distance  # library returns cm directly
        self.sensor.clear_interrupt()
        if distance_cm is None or distance_cm <= 0 or distance_cm > self.MAX_RANGE_CM:
            return None
        return round(distance_cm, 1)

    def _simulate_distance(self):
        if random.random() < 0.1:
            return None
        return round(random.uniform(5, 400), 1)
