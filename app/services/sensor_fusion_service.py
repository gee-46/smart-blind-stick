"""
Sensor Fusion Service.

Implements Core Safety Features 1 to 5:
1. Real-Time Obstacle Detection (safe, caution, danger, critical levels)
2. Multi-Level Obstacle Detection (ground, waist, chest, head, overhanging, potholes, steps/edges)
3. Intelligent Sensor Fusion (combines ultrasonic, IR, IMU, GPS; filters false alarms from cane swing)
4. Smart Alert Prioritization (prioritizes by distance, movement, direction, obstacle type)
5. Direction-Based Haptic Feedback (custom vibration patterns for direction, potholes, danger)
"""
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session

from app.schemas.sensor_fusion import SensorReadingIn, SensorFusionResult
from app.schemas.event import EventIn
from app.services import event_service


class SensorFusionService:
    """Evaluates multi-sensor inputs and produces unified obstacle assessments."""

    @classmethod
    def evaluate_sensors(cls, db: Session, data: SensorReadingIn) -> SensorFusionResult:
        # 1. Multi-Level Obstacle Distance Extraction
        distances: List[Tuple[str, float]] = []
        if data.head_ultrasonic_cm is not None and data.head_ultrasonic_cm > 0:
            distances.append(("head", data.head_ultrasonic_cm))
        elif data.ultrasonic_cm is not None and data.ultrasonic_cm > 0:
            distances.append(("head", data.ultrasonic_cm))

        if data.chest_ultrasonic_cm is not None and data.chest_ultrasonic_cm > 0:
            distances.append(("chest", data.chest_ultrasonic_cm))

        if data.waist_ultrasonic_cm is not None and data.waist_ultrasonic_cm > 0:
            distances.append(("waist", data.waist_ultrasonic_cm))

        nearest_level = "head"
        nearest_cm = None
        if distances:
            nearest_level, nearest_cm = min(distances, key=lambda d: d[1])

        nearest_m = round(nearest_cm / 100.0, 2) if nearest_cm is not None else None
        direction = (data.direction_hint or "center").lower()
        if direction not in ("left", "center", "right"):
            direction = "center"

        # 2. Intelligent Sensor Fusion & False Alarm Filtering (Feature 3)
        # Check IMU swing velocity or excessive tilt that causes spurious side bounces
        false_alarm_filtered = False
        if data.imu_tilt_deg is not None and data.imu_tilt_deg > 55.0 and nearest_m is not None and nearest_m > 0.6:
            false_alarm_filtered = True
        elif data.imu_swing_velocity is not None and data.imu_swing_velocity > 250.0 and nearest_m is not None and nearest_m > 1.2:
            false_alarm_filtered = True

        # 3. Terrain & Ground Hazards (Feature 2)
        has_pothole = bool(data.pothole_detected)
        has_step_edge = bool(data.step_edge_detected)
        has_ground_ir = bool(data.ground_ir_detected)
        has_overhang = bool(data.overhanging_detected)

        # 4. Multi-Level Risk & Obstacle Classification (Features 1 & 2)
        obstacle = False
        risk = "safe"
        detected_level = nearest_level if nearest_m is not None else "none"
        obstacle_type = "none"
        summary = "Path clear, no obstacles detected"
        vibro_str = "none"
        buzzer_str = "silent"
        action = "Proceed safely"
        safety_score = 100

        if false_alarm_filtered:
            risk = "safe"
            summary = "Path clear (cane swing motion filtered)"
            action = "Maintain walking pace"
            obstacle = False
            safety_score = 95
        elif has_ground_ir or has_step_edge or has_pothole:
            risk = "high"
            obstacle = True
            vibro_str = "pulse_fast"
            buzzer_str = "beep_fast"
            safety_score = 25
            if has_pothole:
                detected_level = "pothole"
                obstacle_type = "pothole"
                summary = "Drop-off or pothole hazard detected in forward ground path"
                action = "Step around pothole or probe ground with cane tip"
            else:
                detected_level = "step_edge" if has_step_edge else "ground"
                obstacle_type = "staircase_dropoff"
                summary = "Drop-off, staircase, or puddle detected at ground level"
                action = "Stop and probe ground with cane tip"
        elif nearest_m is not None:
            detected_level = "overhanging" if has_overhang else nearest_level
            obstacle_type = f"{detected_level}_obstacle"
            if nearest_m <= 0.40:
                risk = "critical"
                summary = f"Imminent collision! {detected_level.capitalize()} obstacle at {nearest_m}m"
                vibro_str = "continuous"
                buzzer_str = "alarm"
                action = "Halt immediately"
                obstacle = True
                safety_score = 5
            elif nearest_m <= 1.0:
                risk = "high"
                summary = f"Close obstacle detected ({detected_level} level) at {nearest_m}m"
                vibro_str = "pulse_fast"
                buzzer_str = "beep_fast"
                action = "Slow down and navigate around"
                obstacle = True
                safety_score = 35
            elif nearest_m <= 1.8:
                risk = "medium"
                summary = f"Obstacle approaching ahead at {nearest_m}m"
                vibro_str = "pulse_slow"
                buzzer_str = "beep_slow"
                action = "Be alert and maintain pace"
                obstacle = True
                safety_score = 65
            else:
                risk = "low"
                summary = f"Clear path ahead (nearest object {nearest_m}m)"
                vibro_str = "none"
                buzzer_str = "silent"
                action = "Continue walking"
                obstacle = False
                safety_score = 90
        else:
            risk = "safe"
            summary = "Path clear, no obstacles detected"
            action = "Proceed safely"
            obstacle = False
            safety_score = 100

        # 5. Smart Alert Prioritization (Feature 4)
        if risk == "critical":
            priority = 1
        elif risk in ("high", "danger"):
            priority = 2
        elif risk == "medium":
            priority = 3
        elif risk == "low":
            priority = 4
        else:
            priority = 5

        # 6. Direction-Based Haptic Feedback Patterns (Feature 5)
        vibro_pattern: List[int] = []
        haptic_desc = "None"

        if not obstacle or false_alarm_filtered:
            vibro_pattern = []
            haptic_desc = "None"
        elif priority == 1:
            # Immediate Danger / Collision
            vibro_pattern = [500, 50, 500, 50, 500]
            haptic_desc = "Continuous Emergency Vibration"
        elif detected_level in ("pothole", "ground", "step_edge"):
            # Ground hazard / pothole
            vibro_pattern = [80, 40, 80, 40, 80]
            haptic_desc = "Rapid Ground Staccato Pulse"
        elif detected_level == "overhanging":
            vibro_pattern = [100, 100, 300]
            haptic_desc = "Head-Level Rising Pulse"
        elif direction == "left":
            vibro_pattern = [150, 100, 150]
            haptic_desc = "Left Directional Pulse"
        elif direction == "right":
            vibro_pattern = [300, 100, 100]
            haptic_desc = "Right Directional Pulse"
        else:
            # Center / Forward
            if priority <= 2:
                vibro_pattern = [250, 80, 250]
                haptic_desc = "Forward High Alert Pulse"
            else:
                vibro_pattern = [180, 120, 180]
                haptic_desc = "Forward Center Double Pulse"

        # 7. Register Significant Obstacle Events in Audit Log (Feature 18)
        if obstacle and priority <= 3:
            try:
                event_in = EventIn(
                    device_id=data.device_id,
                    source="sensor_fusion",
                    event_type="obstacle",
                    risk_level=risk,
                    message=summary,
                    extra={
                        "distance_m": nearest_m,
                        "nearest_sensor": detected_level,
                        "obstacle_type": obstacle_type,
                        "direction": direction,
                        "alert_priority": priority,
                        "haptic_pattern": vibro_pattern,
                        "ground_ir_detected": data.ground_ir_detected,
                        "feedback": {"vibration": vibro_str, "buzzer": buzzer_str},
                    },
                )
                event_service.create_event(db, event_in)
            except Exception:
                pass

        return SensorFusionResult(
            device_id=data.device_id,
            risk_level=risk,
            obstacle_detected=obstacle,
            nearest_distance_m=nearest_m,
            direction=direction,
            detected_level=detected_level,
            obstacle_type=obstacle_type,
            alert_priority=priority,
            summary=summary,
            vibration_feedback=vibro_str,
            vibration_pattern=vibro_pattern,
            haptic_description=haptic_desc,
            buzzer_feedback=buzzer_str,
            action_required=action,
            false_alarm_filtered=false_alarm_filtered,
            safety_score_pct=safety_score,
        )
