"""
fusion.py
---------
The core sensor fusion module. This is what your 3 teammates (AI/vision,
alert/haptics, mobile app) will import data from.

Covers:
  - Task 4: Detect obstacles
  - Task 5: Calculate obstacle distance
  - Task 6: Detect obstacle direction
  - Task 7: Detect ground/head-level obstacles
  - Task 8: Combine LiDAR (forward) + ToF (ground) data
  - Task 9: Generate standard obstacle data for other modules

NOTE: with the actual hardware (1x TF-Mini S LiDAR forward, 1x VL53L1X ToF
angled down), the two sensors normally cover DIFFERENT zones
(chest_head vs ground), so "fusion" mostly means combining them into one
coherent report rather than resolving conflicting readings of the same
obstacle. The agreement/disagreement logic below still applies and becomes
useful automatically if the team adds more sensors later (e.g. side LiDARs).
"""

import time
from dataclasses import dataclass, asdict
from typing import List, Optional

from sensors import SensorReading, Direction, HeightLevel
from filters import OutlierRejectingFilter

# --- Safety thresholds (cm) -------------------------------------------------
# Tune these during real-world testing.
DANGER_THRESHOLD_CM = 60
CAUTION_THRESHOLD_CM = 150

# How close two sensors' readings need to be (in cm) to be considered
# "the same physical obstacle" during fusion.
AGREEMENT_TOLERANCE_CM = 40


def classify_status(distance_cm: Optional[float]) -> str:
    """Task 4 (part of): turn a distance into safe/caution/danger."""
    if distance_cm is None:
        return "safe"  # nothing detected
    if distance_cm <= DANGER_THRESHOLD_CM:
        return "danger"
    if distance_cm <= CAUTION_THRESHOLD_CM:
        return "caution"
    return "safe"


@dataclass
class FusedObstacle:
    """
    The STANDARDIZED output object other modules will consume.
    This is Task 9 — keep this shape stable since your teammates'
    code (AI engine, alert engine, mobile app) will depend on it.
    """
    direction: str          # "left" | "center" | "right"
    height_level: str       # "ground" | "waist" | "chest_head"
    distance_cm: float
    status: str              # "safe" | "caution" | "danger"
    confidence: float        # 0.0 - 1.0
    sensor_types: List[str]  # which sensor types contributed, e.g. ["ultrasonic", "ir"]
    timestamp: float

    def to_dict(self):
        return asdict(self)


class SensorFusionEngine:
    """
    Owns one filter per physical sensor, reads them all each cycle,
    fuses agreeing readings into single obstacles, and outputs a
    standardized obstacle list.
    """

    def __init__(self, sensors, filter_window=5):
        """
        sensors: list of sensor objects (UltrasonicSensor / IRSensor instances)
        """
        self.sensors = sensors
        # one filter instance PER sensor (keyed by sensor_id) - important,
        # don't share filters across sensors or they'll blend unrelated data.
        self.filters = {
            s.sensor_id: OutlierRejectingFilter(window_size=filter_window)
            for s in sensors
        }

    def read_all_filtered(self) -> List[SensorReading]:
        """Read every sensor once and apply its dedicated noise filter."""
        filtered_readings = []
        for sensor in self.sensors:
            raw_reading = sensor.read()
            filtered_distance = self.filters[sensor.sensor_id].update(raw_reading.distance_cm)
            raw_reading.distance_cm = filtered_distance
            filtered_readings.append(raw_reading)
        return filtered_readings

    def fuse(self, readings: Optional[List[SensorReading]] = None) -> List[FusedObstacle]:
        """
        Task 6, 7, 8: group readings by (direction, height_level) zone,
        then combine same-zone readings into one fused obstacle.
        """
        if readings is None:
            readings = self.read_all_filtered()

        # Group readings by physical zone on the stick
        zones = {}
        for r in readings:
            key = (r.direction, r.height_level)
            zones.setdefault(key, []).append(r)

        fused_obstacles = []
        for (direction, height_level), zone_readings in zones.items():
            obstacle = self._fuse_zone(direction, height_level, zone_readings)
            if obstacle is not None:
                fused_obstacles.append(obstacle)

        return fused_obstacles

    def _fuse_zone(self, direction, height_level, zone_readings: List[SensorReading]) -> Optional[FusedObstacle]:
        """
        Task 8: Combine ultrasonic + IR data for a single zone.

        Logic:
          - If only one sensor has data in this zone, use it with lower confidence.
          - If multiple sensors have data and they roughly AGREE (within
            AGREEMENT_TOLERANCE_CM), average them with HIGH confidence
            (this is the false-alarm reduction the fusion engine exists for).
          - If multiple sensors DISAGREE significantly, trust the sensor
            type that's more reliable for that height level (IR for ground,
            ultrasonic for waist/chest) but lower the confidence, since
            disagreement usually means one sensor is seeing noise/glare.
        """
        valid = [r for r in zone_readings if r.distance_cm is not None]

        if not valid:
            return None  # clear path in this zone, nothing to report

        if len(valid) == 1:
            r = valid[0]
            distance = r.distance_cm
            confidence = 0.6  # single sensor, moderate confidence
            sensor_types = [r.sensor_type]
        else:
            distances = [r.distance_cm for r in valid]
            spread = max(distances) - min(distances)

            if spread <= AGREEMENT_TOLERANCE_CM:
                # Sensors agree -> high confidence, average their readings
                distance = round(sum(distances) / len(distances), 1)
                confidence = 0.95
            else:
                # Sensors disagree -> trust the more appropriate sensor type
                preferred_type = "tof" if height_level == HeightLevel.GROUND else "lidar"
                preferred = [r for r in valid if r.sensor_type == preferred_type]
                chosen = preferred[0] if preferred else valid[0]
                distance = chosen.distance_cm
                confidence = 0.5  # disagreement = lower trust

            sensor_types = list({r.sensor_type for r in valid})

        return FusedObstacle(
            direction=direction.value if isinstance(direction, Direction) else direction,
            height_level=height_level.value if isinstance(height_level, HeightLevel) else height_level,
            distance_cm=distance,
            status=classify_status(distance),
            confidence=confidence,
            sensor_types=sensor_types,
            timestamp=time.time(),
        )

    def get_standard_output(self) -> dict:
        """
        Task 9: Generate standard obstacle data for other modules.
        This is the JSON-serializable payload the alert engine, AI engine,
        and mobile app should all read from (e.g. via a shared queue, MQTT
        topic, or local socket — see README for integration notes).
        """
        obstacles = self.fuse()
        overall_status = "safe"
        if any(o.status == "danger" for o in obstacles):
            overall_status = "danger"
        elif any(o.status == "caution" for o in obstacles):
            overall_status = "caution"

        return {
            "timestamp": time.time(),
            "overall_status": overall_status,
            "obstacle_count": len(obstacles),
            "obstacles": [o.to_dict() for o in obstacles],
        }
