"""Fall Detection Service.

Implements a multi-condition algorithmic fall evaluation pipeline based on IMU telemetry:
1. Free-Fall / Weightlessness Phase (SVM < FreeFall Threshold)
2. High Impact Spike (SVM > Impact Threshold)
3. Significant Post-Impact Tilt / Angle Change (Tilt > Angle Threshold)
4. Post-Impact Immobility / Rest State (Immobility Duration >= Rest Threshold)

FUTURE HARDWARE INTEGRATION:
Member 2 (Sensor Fusion) will provide real-time MPU6050 accelerometer/gyroscope streams
over I2C/MQTT. This service is designed to consume either pre-processed features or raw
accelerometer tri-axial vectors seamlessly.
"""
import math
from typing import Optional, Dict, Any, Tuple
from app.config import get_settings
from app.schemas.emergency import FallTelemetry, FallAssessmentResult


class FallDetectionService:
    """Evaluates sensor telemetry to classify falls vs. daily activities."""

    @staticmethod
    def calculate_signal_vector_magnitude(ax: float, ay: float, az: float) -> float:
        """Compute Signal Vector Magnitude (SVM) / total acceleration in g.
        
        SVM = sqrt(ax^2 + ay^2 + az^2)
        """
        return math.sqrt(ax**2 + ay**2 + az**2)

    @staticmethod
    def calculate_tilt_angle_deg(ax: float, ay: float, az: float) -> float:
        """Estimate inclination angle from the vertical axis in degrees.
        
        Assuming vertical axis is Z when standing upright (0 deg).
        """
        svm = math.sqrt(ax**2 + ay**2 + az**2)
        if svm == 0.0:
            return 0.0
        # Cosine of angle with Z axis
        cos_theta = max(min(az / svm, 1.0), -1.0)
        angle_rad = math.acos(cos_theta)
        return math.degrees(angle_rad)

    @classmethod
    def evaluate_telemetry(
        cls,
        telemetry: Optional[FallTelemetry],
        override_confidence: Optional[float] = None
    ) -> FallAssessmentResult:
        """Run multi-condition assessment on sensor readings.
        
        Returns structured FallAssessmentResult.
        """
        settings = get_settings()

        # If direct confidence was passed by an upstream AI or sensor fusion module:
        if override_confidence is not None:
            is_fall = override_confidence >= 0.70
            risk_score = round(override_confidence * 100, 1)
            return FallAssessmentResult(
                detected=is_fall,
                confidence=round(override_confidence, 2),
                reason=f"Direct sensor assessment: confidence {override_confidence:.2f}",
                risk_score=risk_score,
                conditions_met={"direct_confidence": is_fall},
                telemetry_values={"provided_confidence": override_confidence},
            )

        # Default telemetry if none provided (e.g. basic trigger)
        if telemetry is None:
            return FallAssessmentResult(
                detected=True,
                confidence=0.85,
                reason="Fall event received without detailed raw telemetry (default high risk)",
                risk_score=85.0,
                conditions_met={"generic_fall_event": True},
                telemetry_values={},
            )

        # 1. Compute or extract SVM Impact Magnitude
        computed_svm = cls.calculate_signal_vector_magnitude(
            telemetry.accel_x, telemetry.accel_y, telemetry.accel_z
        )
        impact_g = telemetry.impact_magnitude_g if telemetry.impact_magnitude_g is not None else computed_svm

        # 2. Compute or extract Tilt Angle
        computed_tilt = cls.calculate_tilt_angle_deg(
            telemetry.accel_x, telemetry.accel_y, telemetry.accel_z
        )
        tilt_deg = telemetry.tilt_angle_deg if telemetry.tilt_angle_deg is not None else computed_tilt

        # 3. Free fall indicator
        free_fall = (
            telemetry.free_fall_detected
            if telemetry.free_fall_detected is not None
            else (impact_g < settings.FALL_ACCEL_FREE_FALL_THRESHOLD)
        )

        # 4. Immobility duration
        immobility = telemetry.immobility_seconds if telemetry.immobility_seconds is not None else 3.0

        # Evaluate individual criteria
        cond_impact = impact_g >= settings.FALL_ACCEL_IMPACT_THRESHOLD
        cond_tilt = tilt_deg >= settings.FALL_TILT_THRESHOLD_DEGREES
        cond_immobility = immobility >= settings.FALL_IMMOBILITY_DURATION_SECONDS
        cond_free_fall = bool(free_fall)

        conditions_met = {
            "high_impact_spike": cond_impact,
            "post_impact_tilt": cond_tilt,
            "post_impact_immobility": cond_immobility,
            "free_fall_drop": cond_free_fall,
        }

        # Multi-factor score computation:
        # High impact (40%), Tilt (30%), Immobility (20%), Free-fall (10%)
        score = 0.0
        if cond_impact:
            # Scale impact score based on how much it exceeded the threshold
            impact_factor = min(impact_g / (settings.FALL_ACCEL_IMPACT_THRESHOLD * 1.5), 1.0)
            score += 0.40 * impact_factor
        if cond_tilt:
            tilt_factor = min(tilt_deg / 90.0, 1.0)
            score += 0.30 * tilt_factor
        if cond_immobility:
            score += 0.20
        if cond_free_fall:
            score += 0.10

        confidence = round(min(score, 1.0), 2)
        
        # A confirmed fall requires AT LEAST high impact AND (tilt change OR immobility)
        # OR a confidence score >= 0.65
        detected = (cond_impact and (cond_tilt or cond_immobility)) or (confidence >= 0.65)

        reasons = []
        if cond_impact:
            reasons.append(f"Impact spike ({impact_g:.2f}g >= {settings.FALL_ACCEL_IMPACT_THRESHOLD}g)")
        if cond_tilt:
            reasons.append(f"Significant tilt ({tilt_deg:.1f}° >= {settings.FALL_TILT_THRESHOLD_DEGREES}°)")
        if cond_immobility:
            reasons.append(f"Post-fall immobility ({immobility:.1f}s >= {settings.FALL_IMMOBILITY_DURATION_SECONDS}s)")
        if cond_free_fall:
            reasons.append("Free-fall weightlessness phase detected")

        if not detected:
            reason_str = "Normal activity: criteria for fall not satisfied."
            if not cond_impact:
                reason_str += f" Impact ({impact_g:.2f}g) below threshold."
        else:
            reason_str = "Fall confirmed: " + "; ".join(reasons)

        telemetry_values = {
            "impact_magnitude_g": round(impact_g, 2),
            "tilt_angle_deg": round(tilt_deg, 1),
            "immobility_seconds": round(immobility, 1),
            "free_fall_detected": cond_free_fall,
            "raw_accel": {
                "x": telemetry.accel_x,
                "y": telemetry.accel_y,
                "z": telemetry.accel_z
            },
        }

        return FallAssessmentResult(
            detected=detected,
            confidence=confidence,
            reason=reason_str,
            risk_score=round(confidence * 100, 1),
            conditions_met=conditions_met,
            telemetry_values=telemetry_values,
        )

    # -----------------------------------------------------------------------
    # Synthetic / Simulation Helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def generate_simulated_fall_telemetry() -> FallTelemetry:
        """Generate a synthetic sensor reading characteristic of a real human fall."""
        return FallTelemetry(
            accel_x=0.45,
            accel_y=0.85,
            accel_z=2.85,  # High impact spike along Z/Y
            impact_magnitude_g=3.01,
            tilt_angle_deg=72.5,  # Cane/stick lying flat on floor
            immobility_seconds=4.5,  # User immobile after landing
            free_fall_detected=True,
        )

    @staticmethod
    def generate_simulated_normal_walk_telemetry() -> FallTelemetry:
        """Generate a synthetic sensor reading characteristic of regular walking."""
        return FallTelemetry(
            accel_x=0.10,
            accel_y=0.15,
            accel_z=1.02,  # Normal ~1g gravity
            impact_magnitude_g=1.05,
            tilt_angle_deg=8.0,  # Stick held almost vertical
            immobility_seconds=0.0,
            free_fall_detected=False,
        )
