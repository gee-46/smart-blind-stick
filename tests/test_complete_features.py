"""Comprehensive Test Suite for Smart Blind Stick 23 Complete Features.

Validates:
1. Core Safety Features (Features 1-5):
   - 1. Real-Time Obstacle Detection
   - 2. Multi-Level Obstacle Detection
   - 3. Intelligent Sensor Fusion
   - 4. Smart Alert Prioritization
   - 5. Direction-Based Haptic Feedback
2. AI and Intelligent Features (Features 6-10):
   - 6. AI-Based Object Recognition
   - 7. Obstacle Type Classification
   - 8. Moving Object Detection
   - 9. Fall Detection
   - 10. Intelligent SOS System
3. Navigation Features (Features 11-13):
   - 11. Voice Navigation
   - 12. Safe Route Recommendation
   - 13. Geofencing
4. Personalization Features (Features 14-15):
   - 14. Adaptive Alert System
   - 15. User Profiles
5. Mobile Application and Monitoring Features (Features 16-18):
   - 16. Live Stick Dashboard
   - 17. Guardian Dashboard
   - 18. Incident History
6. Innovative and Reliability Features (Features 19-23):
   - 19. Community Hazard Mapping
   - 20. AI Voice Assistant
   - 21. Offline Safety Mode
   - 22. Battery Intelligence
   - 23. Self-Diagnostic System
"""
import pytest
from ai_vision.detection.classes import (
    TARGET_MOBILITY_CLASSES,
    normalize_target_class,
    DEFAULT_REFERENCE_HEIGHTS_M,
)


# ==============================================================================
# Category 1: Core Safety Features (Features 1 - 5)
# ==============================================================================
def test_feature_1_real_time_obstacle_levels(client):
    """Feature 1: Real-Time Obstacle Detection with safe, caution, and danger levels."""
    # Safe (> 1.8m)
    res_safe = client.post("/api/sensors/data", json={
        "device_id": "TEST_STICK", "ultrasonic_cm": 220.0
    })
    assert res_safe.status_code == 200
    assert res_safe.json()["risk_level"] == "low"
    assert res_safe.json()["safety_score_pct"] >= 90

    # Caution (0.8m to 1.8m)
    res_caution = client.post("/api/sensors/data", json={
        "device_id": "TEST_STICK", "ultrasonic_cm": 140.0
    })
    assert res_caution.status_code == 200
    assert res_caution.json()["risk_level"] == "medium"
    assert "Caution" in res_caution.json()["summary"] or "Obstacle" in res_caution.json()["summary"]

    # Danger / Critical (< 0.8m and < 0.4m)
    res_danger = client.post("/api/sensors/data", json={
        "device_id": "TEST_STICK", "ultrasonic_cm": 30.0
    })
    assert res_danger.status_code == 200
    assert res_danger.json()["risk_level"] == "critical"
    assert res_danger.json()["obstacle_detected"] is True


def test_feature_2_multi_level_obstacle_detection(client):
    """Feature 2: Multi-Level Obstacle Detection (ground, waist, chest, head, overhangs, potholes, steps)."""
    # Ground Pothole
    res_pothole = client.post("/api/sensors/data", json={
        "device_id": "TEST_STICK", "pothole_detected": True
    })
    assert res_pothole.status_code == 200
    data_p = res_pothole.json()
    assert data_p["detected_level"] == "pothole"
    assert data_p["obstacle_type"] == "pothole"
    assert data_p["risk_level"] == "high"

    # Ground Drop-off / Step Edge
    res_step = client.post("/api/sensors/data", json={
        "device_id": "TEST_STICK", "step_edge_detected": True
    })
    assert res_step.status_code == 200
    assert res_step.json()["detected_level"] == "step_edge"

    # Chest Level
    res_chest = client.post("/api/sensors/data", json={
        "device_id": "TEST_STICK", "chest_ultrasonic_cm": 75.0
    })
    assert res_chest.status_code == 200
    assert res_chest.json()["detected_level"] == "chest"

    # Head / Overhanging Object
    res_overhang = client.post("/api/sensors/data", json={
        "device_id": "TEST_STICK", "head_ultrasonic_cm": 80.0, "overhanging_detected": True
    })
    assert res_overhang.status_code == 200
    assert res_overhang.json()["detected_level"] == "overhanging"


def test_feature_3_sensor_fusion_false_alarm_filtering(client):
    """Feature 3: Intelligent Sensor Fusion filtering false alarms during cane swings."""
    # High swing angular velocity should filter out momentary side reflection
    res = client.post("/api/sensors/data", json={
        "device_id": "TEST_STICK",
        "ultrasonic_cm": 160.0,
        "imu_swing_velocity": 300.0,  # fast sweep
    })
    assert res.status_code == 200
    data = res.json()
    assert data["false_alarm_filtered"] is True
    assert data["obstacle_detected"] is False
    assert data["risk_level"] == "safe"


def test_feature_4_smart_alert_prioritization(client):
    """Feature 4: Smart Alert Prioritization (CRITICAL=1, HIGH=2, MEDIUM=3, LOW=4, INFO=5)."""
    # Critical Imminent Collision
    r1 = client.post("/api/sensors/data", json={"device_id": "TEST_STICK", "ultrasonic_cm": 25.0}).json()
    assert r1["alert_priority"] == 1

    # High Risk Ground Drop-off
    r2 = client.post("/api/sensors/data", json={"device_id": "TEST_STICK", "ground_ir_detected": True}).json()
    assert r2["alert_priority"] == 2

    # Medium Caution
    r3 = client.post("/api/sensors/data", json={"device_id": "TEST_STICK", "ultrasonic_cm": 150.0}).json()
    assert r3["alert_priority"] == 3


def test_feature_5_direction_based_haptic_feedback(client):
    """Feature 5: Direction-Based Haptic Feedback vibration patterns."""
    # Left Obstacle
    res_left = client.post("/api/sensors/data", json={
        "device_id": "TEST_STICK", "ultrasonic_cm": 85.0, "direction_hint": "left"
    }).json()
    assert res_left["direction"] == "left"
    assert res_left["vibration_pattern"] == [150, 100, 150]
    assert "Left" in res_left["haptic_description"]

    # Right Obstacle
    res_right = client.post("/api/sensors/data", json={
        "device_id": "TEST_STICK", "ultrasonic_cm": 85.0, "direction_hint": "right"
    }).json()
    assert res_right["direction"] == "right"
    assert res_right["vibration_pattern"] == [300, 100, 100]
    assert "Right" in res_right["haptic_description"]

    # Pothole Rapid Pattern
    res_pothole = client.post("/api/sensors/data", json={
        "device_id": "TEST_STICK", "pothole_detected": True
    }).json()
    assert res_pothole["vibration_pattern"] == [80, 40, 80, 40, 80]


# ==============================================================================
# Category 2: AI and Intelligent Features (Features 6 - 10)
# ==============================================================================
def test_feature_6_ai_target_classes():
    """Feature 6: AI-Based Object Recognition identifies all 10 canonical target categories."""
    expected_10 = (
        "person", "vehicle", "bicycle", "motorcycle", "pole",
        "tree", "staircase", "door", "chair", "wall"
    )
    for c in expected_10:
        assert c in TARGET_MOBILITY_CLASSES
        assert normalize_target_class(c) == c
        assert c in DEFAULT_REFERENCE_HEIGHTS_M

    # Verify COCO normalization
    assert normalize_target_class("car") == "vehicle"
    assert normalize_target_class("bus") == "vehicle"
    assert normalize_target_class("truck") == "vehicle"
    assert normalize_target_class("traffic light") == "pole"
    assert normalize_target_class("bench") == "chair"


def test_feature_7_and_8_obstacle_classification_and_moving_objects(client):
    """Features 7 & 8: Obstacle Type Classification & Approaching Moving Vehicle Alerts."""
    # Ensure device is registered first
    client.post("/devices/", json={"device_id": "TEST_STICK", "battery": 90.0})
    event_payload = {
        "device_id": "TEST_STICK",
        "source": "ai_vision",
        "event_type": "moving_vehicle_approaching",
        "risk_level": "high",
        "message": "Approaching vehicle detected 3.2m center",
        "extra": {
            "object_type": "vehicle",
            "distance_m": 3.2,
            "direction": "center",
            "movement": "approaching",
            "velocity_mps": 4.5,
        }
    }
    res = client.post("/api/events", json=event_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["extra"]["object_type"] == "vehicle"
    assert data["extra"]["movement"] == "approaching"


def test_feature_9_and_10_fall_detection_and_intelligent_sos(client):
    """Features 9 & 10: Fall Detection state machine and Intelligent SOS lifecycle."""
    # Register device
    client.post("/api/device/data", json={
        "device_id": "TEST_STICK", "battery": 90.0, "latitude": 12.9716, "longitude": 77.5946, "status": "safe"
    })
    # Trigger Fall Detection
    res_fall = client.post("/api/emergency/fall/detect", json={
        "device_id": "TEST_STICK",
        "accel_magnitude": 3.1,
        "tilt_degrees": 52.0,
        "fall_confidence": 0.95,
        "latitude": 12.9716,
        "longitude": 77.5946,
    })
    assert res_fall.status_code == 200
    fall_data = res_fall.json()
    assert fall_data["status"] == "fall_detected"
    assert fall_data["session"]["state"] in ("FALL_DETECTED", "PENDING_CONFIRMATION", "ACTIVE_SOS")
    assert fall_data["session"]["trigger_type"] == "AUTOMATIC_FALL"

    # User cancels false alarm during confirmation window ("I'm OK")
    res_cancel = client.post("/api/emergency/sos/cancel", json={
        "device_id": "TEST_STICK",
        "session_id": fall_data["session"]["session_id"],
        "reason": "False alarm, user recovered balance"
    })
    assert res_cancel.status_code == 200
    assert res_cancel.json()["state"] == "CANCELLED"

    # Manual SOS Button Trigger
    res_sos = client.post("/api/emergency/sos/manual", json={
        "device_id": "TEST_STICK",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "reason": "Manual SOS button pressed",
    })
    assert res_sos.status_code == 201
    sos_data = res_sos.json()
    assert sos_data["state"] == "ACTIVE_SOS"


# ==============================================================================
# Category 3: Navigation Features (Features 11 - 13)
# ==============================================================================
def test_feature_11_and_12_voice_navigation_and_safe_route(client):
    """Features 11 & 12: Voice Navigation & Safe Route Recommendation."""
    req_payload = {
        "device_id": "TEST_STICK",
        "start_lat": 12.9716,
        "start_lon": 77.5946,
        "dest_lat": 12.9750,
        "dest_lon": 77.5980,
        "dest_name": "City Metro Station",
        "avoid_stairs": True,
        "avoid_high_traffic": True,
        "avoid_construction": True,
    }
    res = client.post("/api/features/navigation/safe-route", json=req_payload)
    assert res.status_code == 200
    route = res.json()
    assert route["destination"] == "City Metro Station"
    assert route["safety_score_pct"] >= 90
    assert len(route["steps"]) >= 3
    # Step 1 has spoken turn-by-turn guidance
    assert len(route["steps"][0]["spoken_prompt"]) > 5


def test_feature_13_geofencing_management_and_check(client):
    """Feature 13: Geofencing safe zone definition and boundary breach check."""
    # Create Geofence
    zone_payload = {
        "name": "Community Library Zone",
        "center_latitude": 12.9716,
        "center_longitude": 77.5946,
        "radius_meters": 200.0,
        "is_active": True,
    }
    res_create = client.post("/api/features/geofences/TEST_STICK", json=zone_payload)
    assert res_create.status_code == 200
    zone_data = res_create.json()
    assert zone_data["name"] == "Community Library Zone"

    # Check Inside Boundary (at center)
    res_in = client.post("/api/features/geofences/check/TEST_STICK?lat=12.9716&lon=77.5946")
    assert res_in.status_code == 200
    assert res_in.json()["inside_geofence"] is True
    assert res_in.json()["breach_alert"] is False

    # Check Outside Boundary (10km away)
    res_out = client.post("/api/features/geofences/check/TEST_STICK?lat=13.0800&lon=77.6500")
    assert res_out.status_code == 200
    assert res_out.json()["inside_geofence"] is False
    assert res_out.json()["breach_alert"] is True


# ==============================================================================
# Category 4: Personalization Features (Features 14 - 15)
# ==============================================================================
def test_features_14_and_15_user_profiles_and_adaptive_alerts(client):
    """Features 14 & 15: User Profiles and Adaptive Alert System customization."""
    # Get profile
    res_get = client.get("/api/features/profile/TEST_STICK")
    assert res_get.status_code == 200
    profile = res_get.json()
    assert profile["device_id"] == "TEST_STICK"

    # Update profile & adaptive sensitivity mode
    updates = {
        "user_name": "Jordan Lee",
        "alert_distance_m": 2.8,
        "audio_volume": 90,
        "vibration_intensity": "intense",
        "navigation_voice": "male_en",
        "walking_speed": "fast",
        "adaptive_sensitivity": "crowded_street",
        "emergency_contact_name": "Sarah Lee",
        "emergency_contact_phone": "+1-555-0842",
    }
    res_put = client.put("/api/features/profile/TEST_STICK", json=updates)
    assert res_put.status_code == 200
    updated = res_put.json()
    assert updated["user_name"] == "Jordan Lee"
    assert updated["alert_distance_m"] == 2.8
    assert updated["adaptive_sensitivity"] == "crowded_street"
    assert updated["emergency_contact_name"] == "Sarah Lee"


# ==============================================================================
# Category 5: Mobile Application and Monitoring Features (Features 16 - 18)
# ==============================================================================
def test_feature_16_live_stick_dashboard_pwa(client):
    """Feature 16: Live Stick Dashboard served as high-performance PWA."""
    res = client.get("/app")
    assert res.status_code == 200
    assert "SmartStick" in res.text or "Smart Blind Stick" in res.text


def test_feature_17_guardian_dashboard(client):
    """Feature 17: Guardian Dashboard live monitoring portal."""
    res = client.get("/dashboard")
    assert res.status_code == 200
    assert "Guardian" in res.text or "Smart Blind Stick" in res.text


def test_feature_18_incident_history(client):
    """Feature 18: Incident History audit trail."""
    client.post("/api/device/data", json={
        "device_id": "TEST_STICK", "battery": 90.0, "latitude": 12.9716, "longitude": 77.5946, "status": "safe"
    })
    res = client.get("/api/events/TEST_STICK?limit=10")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


# ==============================================================================
# Category 6: Innovative and Reliability Features (Features 19 - 23)
# ==============================================================================
def test_feature_19_community_hazard_mapping(client):
    """Feature 19: Community Hazard Mapping (potholes, construction, blocked paths)."""
    # List hazards
    res_list = client.get("/api/features/hazards")
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # Report new hazard
    hazard_payload = {
        "hazard_type": "pothole",
        "title": "Broken storm drain curb",
        "description": "Exposed grate with 20cm gap",
        "severity": "high",
        "latitude": 12.9730,
        "longitude": 77.5950,
        "reported_by": "Pedestrian Anonymous",
    }
    res_create = client.post("/api/features/hazards", json=hazard_payload)
    assert res_create.status_code == 200
    assert res_create.json()["title"] == "Broken storm drain curb"


def test_feature_20_ai_voice_assistant(client):
    """Feature 20: AI Voice Assistant spoken query processing."""
    # Query: Where am I?
    r1 = client.post("/api/features/assistant/query", json={
        "device_id": "TEST_STICK", "query_text": "Where am I right now?"
    }).json()
    assert r1["topic"] == "location"
    assert "latitude" in r1["spoken_answer"].lower() or "coordinates" in r1["spoken_answer"].lower()

    # Query: Is there anything ahead?
    r2 = client.post("/api/features/assistant/query", json={
        "device_id": "TEST_STICK", "query_text": "Is there anything ahead?"
    }).json()
    assert r2["topic"] == "obstacle"
    assert "path" in r2["spoken_answer"].lower() or "ahead" in r2["spoken_answer"].lower()

    # Query: What is my battery level?
    r3 = client.post("/api/features/assistant/query", json={
        "device_id": "TEST_STICK", "query_text": "What is my battery level?"
    }).json()
    assert r3["topic"] == "battery"
    assert "%" in r3["spoken_answer"]


def test_feature_21_offline_safety_mode(client):
    """Feature 21: Offline Safety Mode guarantees local obstacle detection and local haptics."""
    # Microcontroller / local sensor evaluation endpoint functions with zero cloud dependency
    payload = {
        "device_id": "OFFLINE_STICK",
        "ultrasonic_cm": 38.0,
        "raw_telemetry": {"offline_mode": True}
    }
    res = client.post("/api/sensors/data", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["obstacle_detected"] is True
    assert data["vibration_feedback"] == "continuous"


def test_feature_22_battery_intelligence(client):
    """Feature 22: Battery Intelligence (normal, power-saving, critical modes)."""
    res = client.get("/api/features/battery/TEST_STICK")
    assert res.status_code == 200
    bat = res.json()
    assert bat["power_mode"] in ("normal", "power_saving", "critical")
    assert bat["estimated_hours_remaining"] > 0
    assert bat["voltage"] >= 3.0


def test_feature_23_self_diagnostic_system(client):
    """Feature 23: Self-Diagnostic System startup and sensor health report."""
    res = client.post("/api/features/diagnostics/run/TEST_STICK")
    assert res.status_code == 200
    diag = res.json()
    assert diag["overall_health"] in ("healthy", "warning", "critical_fault")
    assert len(diag["components"]) == 7
    # Verify all components checked: Ultrasonic, IR, GPS, Vibration, IMU, Battery, Connectivity
    comp_names = [c["component"] for c in diag["components"]]
    assert any("Ultrasonic" in n for n in comp_names)
    assert any("IR" in n for n in comp_names)
    assert any("GPS" in n for n in comp_names)
    assert any("Vibration" in n for n in comp_names)
    assert any("IMU" in n for n in comp_names)
    assert any("Battery" in n for n in comp_names)
    assert any("Connectivity" in n for n in comp_names)
    assert len(diag["startup_announcement"]) > 10
