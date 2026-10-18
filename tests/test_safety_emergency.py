"""Comprehensive Test Suite for Member 3's Safety & Emergency Subsystem."""
import time
from datetime import datetime, timezone, timedelta
from app.models.emergency import EmergencySession, EmergencyLog
from app.services.notification_service import MockNotificationService
from app.services.fall_detection_service import FallDetectionService
from app.schemas.emergency import FallTelemetry


class TestSafetyEmergencySubsystem:
    """Tests covering all 9 responsibilities of Safety & Emergency."""

    def test_manual_sos_activation(self, client):
        """Test immediate Manual SOS activation."""
        payload = {
            "device_id": "STICK_TEST_001",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "reason": "Emergency button pressed by user",
        }
        res = client.post("/api/emergency/sos/manual", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["device_id"] == "STICK_TEST_001"
        assert data["state"] == "ACTIVE_SOS"
        assert data["trigger_type"] == "MANUAL_SOS"
        assert data["latitude"] == 12.9716
        assert data["longitude"] == 77.5946
        assert "maps.google.com" in data["maps_url"]
        assert data["notification_status"] == "DISPATCHED"

        # Check guardian notification delivery
        history = MockNotificationService.get_history()
        assert len(history) >= 1
        assert history[-1].success is True
        assert history[-1].raw_payload["emergency_type"] == "MANUAL_SOS"
        assert "MANUAL" in history[-1].summary.upper() or "EMERGENCY" in history[-1].summary.upper()

    def test_duplicate_sos_prevention(self, client):
        """Test that triggering manual SOS twice updates active emergency rather than creating conflicting sessions."""
        payload1 = {
            "device_id": "STICK_DUP_001",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "reason": "First SOS press",
        }
        res1 = client.post("/api/emergency/sos/manual", json=payload1)
        assert res1.status_code == 201
        session_id_1 = res1.json()["session_id"]

        # Trigger second manual SOS for same device
        payload2 = {
            "device_id": "STICK_DUP_001",
            "latitude": 12.9720,
            "longitude": 77.5950,
            "reason": "Repeated SOS press",
        }
        res2 = client.post("/api/emergency/sos/manual", json=payload2)
        assert res2.status_code == 201
        session_id_2 = res2.json()["session_id"]

        # Session ID must remain the same (session updated)
        assert session_id_1 == session_id_2
        assert res2.json()["latitude"] == 12.9720

    def test_gps_attached_to_sos(self, client):
        """Verify GPS coordinates and valid Google Maps links are attached to emergency session."""
        payload = {
            "device_id": "STICK_GPS_001",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "reason": "SOS in New Delhi",
        }
        res = client.post("/api/emergency/sos/manual", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["latitude"] == 28.6139
        assert data["longitude"] == 77.2090
        assert data["maps_url"] == "https://maps.google.com/?q=28.613900,77.209000"

    def test_invalid_missing_gps_handling(self, client):
        """Verify system gracefully falls back to mock/cached location when coordinates are omitted."""
        payload = {
            "device_id": "STICK_NOGPS_001",
            "reason": "SOS with no hardware GPS",
        }
        res = client.post("/api/emergency/sos/manual", json=payload)
        assert res.status_code == 201
        data = res.json()
        # Mock GPS fallback provides valid coordinates
        assert data["latitude"] is not None
        assert data["longitude"] is not None
        assert data["maps_url"] is not None
        assert "maps.google.com" in data["maps_url"]

    def test_guardian_notification_generation(self, client):
        """Verify structured notification contents and delivery status."""
        MockNotificationService.clear_history()
        payload = {
            "device_id": "STICK_NOTIF_001",
            "latitude": 13.0827,
            "longitude": 80.2707,
            "reason": "Test notification dispatch",
        }
        res = client.post("/api/emergency/sos/manual", json=payload)
        assert res.status_code == 201

        history = MockNotificationService.get_history()
        assert len(history) == 1
        notif = history[0]
        assert notif.success is True
        assert notif.channel == "mock_console"
        assert notif.raw_payload["device_id"] == "STICK_NOTIF_001"
        assert notif.raw_payload["emergency_type"] == "MANUAL_SOS"
        assert "maps.google.com" in notif.raw_payload["maps_url"]

    def test_fall_detection_positive_case(self, client):
        """Test multi-condition fall detection algorithm with high-impact + tilt + immobility telemetry."""
        telemetry = {
            "accel_x": 0.40,
            "accel_y": 0.80,
            "accel_z": 2.90,
            "impact_magnitude_g": 3.03,
            "tilt_angle_deg": 70.0,
            "immobility_seconds": 4.0,
            "free_fall_detected": True,
        }
        payload = {
            "device_id": "STICK_FALL_001",
            "telemetry": telemetry,
            "latitude": 12.9716,
            "longitude": 77.5946,
            "reason": "High impact and tilt detected",
        }
        res = client.post("/api/emergency/fall/detect", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "fall_detected"
        assert data["assessment"]["detected"] is True
        assert data["assessment"]["confidence"] >= 0.70
        assert data["assessment"]["conditions_met"]["high_impact_spike"] is True
        assert data["assessment"]["conditions_met"]["post_impact_tilt"] is True

        # Session should enter PENDING_CONFIRMATION
        session = data["session"]
        assert session["state"] == "PENDING_CONFIRMATION"
        assert session["trigger_type"] == "AUTOMATIC_FALL"
        assert session["countdown_remaining_seconds"] == 20
        assert session["notification_status"] == "PENDING"

    def test_fall_detection_negative_false_alarm(self, client):
        """Test that regular walking motion is correctly classified as non-fall."""
        normal_telemetry = {
            "accel_x": 0.10,
            "accel_y": 0.12,
            "accel_z": 1.01,
            "impact_magnitude_g": 1.02,
            "tilt_angle_deg": 10.0,
            "immobility_seconds": 0.0,
            "free_fall_detected": False,
        }
        payload = {
            "device_id": "STICK_WALK_001",
            "telemetry": normal_telemetry,
        }
        res = client.post("/api/emergency/fall/detect", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "no_fall"
        assert data["assessment"]["detected"] is False
        assert data["session"] is None

        # Verify device status remains IDLE
        status_res = client.get("/api/emergency/status/STICK_WALK_001").json()
        assert status_res["state"] == "IDLE"
        assert status_res["has_active_emergency"] is False

    def test_fall_cancellation_within_window(self, client):
        """Test false alarm cancellation by user during confirmation countdown."""
        # 1. Trigger Fall
        fall_payload = {
            "device_id": "STICK_CANCEL_001",
            "telemetry": {
                "accel_x": 0.5,
                "accel_y": 0.8,
                "accel_z": 2.8,
                "impact_magnitude_g": 2.95,
                "tilt_angle_deg": 65.0,
                "immobility_seconds": 3.0,
            }
        }
        res_fall = client.post("/api/emergency/fall/detect", json=fall_payload)
        assert res_fall.status_code == 200
        assert res_fall.json()["session"]["state"] == "PENDING_CONFIRMATION"

        # 2. Cancel Emergency
        cancel_payload = {
            "device_id": "STICK_CANCEL_001",
            "reason": "Stick was dropped on sofa, user is completely fine",
        }
        res_cancel = client.post("/api/emergency/sos/cancel", json=cancel_payload)
        assert res_cancel.status_code == 200
        cancel_data = res_cancel.json()
        assert cancel_data["state"] == "CANCELLED"
        assert cancel_data["cancellation_reason"] == "Stick was dropped on sofa, user is completely fine"

        # 3. Verify device status is now IDLE (no active emergency)
        status_res = client.get("/api/emergency/status/STICK_CANCEL_001").json()
        assert status_res["has_active_emergency"] is False
        assert status_res["state"] == "IDLE"

    def test_automatic_sos_after_timeout(self, client, db_session):
        """Test that uncancelled fall automatically escalates to ACTIVE_SOS when countdown expires."""
        # 1. Trigger Fall
        fall_payload = {
            "device_id": "STICK_TIMEOUT_001",
            "telemetry": {
                "accel_x": 0.5,
                "accel_y": 0.8,
                "accel_z": 3.0,
                "impact_magnitude_g": 3.15,
                "tilt_angle_deg": 75.0,
                "immobility_seconds": 4.0,
            }
        }
        res_fall = client.post("/api/emergency/fall/detect", json=fall_payload)
        assert res_fall.status_code == 200

        # Fast-forward started_at timestamp in database to simulate timeout
        session = db_session.query(EmergencySession).filter(EmergencySession.device_id == "STICK_TIMEOUT_001").first()
        assert session is not None
        session.started_at = datetime.now(timezone.utc) - timedelta(seconds=25)
        db_session.commit()

        # 2. Check status -> triggers auto-escalation check
        status_res = client.get("/api/emergency/status/STICK_TIMEOUT_001").json()
        assert status_res["state"] == "ACTIVE_SOS"
        assert status_res["trigger_type"] == "AUTOMATIC_FALL"
        assert status_res["notification_status"] == "DISPATCHED"
        assert status_res["has_active_emergency"] is True

    def test_sos_resolution(self, client):
        """Test resolving an active SOS emergency."""
        # 1. Trigger SOS
        client.post("/api/emergency/sos/manual", json={"device_id": "STICK_RESOLVE_001"})

        # 2. Resolve
        resolve_payload = {
            "device_id": "STICK_RESOLVE_001",
            "resolution_notes": "Guardian and paramedic arrived, user in safe care",
        }
        res_resolve = client.post("/api/emergency/sos/resolve", json=resolve_payload)
        assert res_resolve.status_code == 200
        data = res_resolve.json()
        assert data["state"] == "RESOLVED"
        assert data["resolution_notes"] == "Guardian and paramedic arrived, user in safe care"

        # 3. Status should now be IDLE
        status_res = client.get("/api/emergency/status/STICK_RESOLVE_001").json()
        assert status_res["has_active_emergency"] is False
        assert status_res["state"] == "IDLE"

    def test_emergency_logs_retrieval(self, client):
        """Verify complete audit trail logging."""
        device_id = "STICK_LOGS_001"
        # Trigger manual SOS
        client.post("/api/emergency/sos/manual", json={"device_id": device_id, "reason": "Test audit log"})
        # Resolve SOS
        client.post("/api/emergency/sos/resolve", json={"device_id": device_id, "resolution_notes": "Resolved for test"})

        res_logs = client.get(f"/api/emergency/logs/{device_id}")
        assert res_logs.status_code == 200
        log_data = res_logs.json()
        assert log_data["count"] >= 2
        event_types = [l["event_type"] for l in log_data["logs"]]
        assert "MANUAL_SOS_TRIGGERED" in event_types
        assert "EMERGENCY_RESOLVED" in event_types

    def test_backward_compatible_sos_endpoint(self, client):
        """Verify legacy POST /api/sos works seamlessly with the Emergency State Manager."""
        legacy_payload = {
            "device_id": "STICK_LEGACY_001",
            "reason": "Legacy button press",
            "latitude": 13.0827,
            "longitude": 80.2707,
        }
        res = client.post("/api/sos", json=legacy_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["device_id"] == "STICK_LEGACY_001"
        assert data["notified"] is True
        assert "maps.google.com" in data["maps_url"]

        # Verify underlying Emergency State was created as ACTIVE_SOS
        status_res = client.get("/api/emergency/status/STICK_LEGACY_001").json()
        assert status_res["has_active_emergency"] is True
        assert status_res["state"] == "ACTIVE_SOS"
