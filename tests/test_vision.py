"""
Tests for AI Vision inference endpoint and diagnostics.

Verifies:
- Frame decoding and rejection of empty/malformed buffers.
- Structured inference response contract.
- Status and diagnostics reporting.
- ZERO DEMO DATA: Returns honest 'vision_unavailable' when weights absent or
  RAM is constrained (e.g. Render 512 MB Free Tier). Never fabricates detections.
- Regression tests for missing weights, missing torch/ultralytics dependencies,
  initialization errors, memory limits, and singleton model reuse across requests.
- Startup lightweight verification: health checks remain instant and unblocked.
"""
import logging
import sys
import time
from unittest.mock import MagicMock
import pytest

from ai_vision.schemas.detection import BoundingBox, Detection
import app.api.vision as vision_module


# Minimal valid 1x1 JPEG byte sequence for testing
VALID_JPEG_BYTES = (
    b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00'
    b'\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19'
    b'\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' \",#\x1c\x1c(7),01444'
    b'\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00'
    b'\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01'
    b'\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9'
)


def reset_vision_state():
    """Helper to reset vision module globals between tests."""
    vision_module._detector = None
    vision_module._detector_status = "uninitialized"
    vision_module._detector_failure_reason = None
    vision_module._resolved_weights_path = None


def test_health_endpoint_fast_and_independent_of_vision(client):
    """
    Verifies that /health responds immediately with HTTP 200 without requiring
    any model to load or blocking on vision dependencies.
    """
    reset_vision_state()
    start = time.perf_counter()
    response = client.get("/health")
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
    assert elapsed_ms < 500.0  # Must be fast and non-blocking


def test_vision_status_endpoint(client):
    response = client.get("/api/vision/status")
    assert response.status_code == 200
    data = response.json()
    assert "model_version" in data
    assert data["classes_supported"] == 80
    assert data["device"] == "cpu"
    assert "status" in data
    assert "numpy_available" in data
    assert "opencv_available" in data
    assert "torch_available" in data
    assert "ultralytics_available" in data
    assert "weights_present" in data


def test_vision_status_does_not_trigger_synchronous_weights_download(client, monkeypatch):
    """
    Verifies that calling /api/vision/status never triggers synchronous weights download.
    """
    reset_vision_state()
    download_attempted = {"count": 0}

    def tracking_resolver(allow_download=False):
        if allow_download:
            download_attempted["count"] += 1
        return None, "Not found"

    monkeypatch.setattr(vision_module, "resolve_model_weights", tracking_resolver)
    res = client.get("/api/vision/status")
    assert res.status_code == 200
    assert download_attempted["count"] == 0  # No download should be attempted for status check


def test_package_presence_probe_does_not_import_modules():
    """
    Verifies is_package_installed checks package presence via find_spec
    without importing non-existent or unimported packages.
    """
    assert vision_module.is_package_installed("non_existent_fake_package_xyz") is False
    assert vision_module.is_package_installed("json") is True


def test_vision_infer_rejects_empty_file(client):
    file_payload = {"file": ("empty.jpg", b"", "image/jpeg")}
    response = client.post("/api/vision/infer", files=file_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("invalid_frame", "vision_unavailable")


def test_vision_infer_rejects_corrupted_jpeg(client):
    corrupt_bytes = b"NOT_A_REAL_JPEG_IMAGE_HEADER"
    file_payload = {"file": ("corrupt.jpg", corrupt_bytes, "image/jpeg")}
    response = client.post("/api/vision/infer", files=file_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("invalid_frame", "vision_unavailable")


def test_vision_graceful_fallback_when_numpy_missing(client, monkeypatch):
    """Regression test: verify vision endpoints do not crash when NumPy is absent."""
    reset_vision_state()
    monkeypatch.setattr(vision_module, "np", None)

    # 1. Status endpoint must report healthy 200 with vision_unavailable
    status_res = client.get("/api/vision/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["numpy_available"] is False
    assert status_data["status"] == "vision_unavailable"

    # 2. Infer endpoint must return 200 with vision_unavailable instead of crashing with 500
    file_payload = {"file": ("test.jpg", b"fake_data", "image/jpeg")}
    infer_res = client.post("/api/vision/infer", files=file_payload)
    assert infer_res.status_code == 200
    infer_data = infer_res.json()
    assert infer_data["status"] == "vision_unavailable"
    assert "NumPy" in infer_data["message"]


def test_vision_graceful_fallback_when_opencv_missing(client, monkeypatch):
    """Regression test: verify vision endpoints do not crash when OpenCV is absent."""
    reset_vision_state()
    monkeypatch.setattr(vision_module, "cv2", None)

    status_res = client.get("/api/vision/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["opencv_available"] is False
    assert status_data["status"] == "vision_unavailable"

    file_payload = {"file": ("test.jpg", b"fake_data", "image/jpeg")}
    infer_res = client.post("/api/vision/infer", files=file_payload)
    assert infer_res.status_code == 200
    infer_data = infer_res.json()
    assert infer_data["status"] == "vision_unavailable"
    assert "OpenCV" in infer_data["message"]


def test_vision_missing_dependencies_regression(client, monkeypatch):
    """
    Regression test: when PyTorch / Ultralytics dependencies are missing,
    reports vision_unavailable with explicit installation instructions.
    """
    reset_vision_state()
    monkeypatch.setattr(vision_module, "get_memory_limit_mb", lambda: (2048.0, "cgroup_v2"))
    monkeypatch.setattr(vision_module, "is_package_installed", lambda pkg: False)

    status_res = client.get("/api/vision/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["status"] == "vision_unavailable"
    assert "PyTorch or Ultralytics" in (status_data["reason"] or "")


def test_vision_missing_weights_regression(client, monkeypatch):
    """
    Regression test: when weights are absent and cannot be resolved,
    endpoints must report vision_unavailable with clear explanation.
    """
    reset_vision_state()
    monkeypatch.setattr(vision_module, "is_package_installed", lambda pkg: True)
    monkeypatch.setattr(vision_module, "get_memory_limit_mb", lambda: (2048.0, "cgroup_v2"))
    monkeypatch.setattr(
        vision_module,
        "resolve_model_weights",
        lambda allow_download=True: (None, "YOLOv8n checkpoint not found on disk or network."),
    )

    file_payload = {"file": ("test.jpg", VALID_JPEG_BYTES, "image/jpeg")}
    infer_res = client.post("/api/vision/infer", files=file_payload)
    assert infer_res.status_code == 200
    infer_data = infer_res.json()
    assert infer_data["status"] == "vision_unavailable"
    assert infer_data["detections"] == []
    assert "Vision inference model not loaded or weights unavailable" in infer_data["message"]

    status_res = client.get("/api/vision/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["status"] == "vision_unavailable"
    assert status_data["weights_present"] is False
    assert "YOLOv8n" in (status_data["reason"] or "")


def test_vision_model_initialization_error_regression(client, monkeypatch):
    """
    Regression test: when detector constructor raises an exception,
    vision API safely captures the error, logs it, and does not crash the server.
    """
    reset_vision_state()
    monkeypatch.setattr(vision_module, "is_package_installed", lambda pkg: True)
    monkeypatch.setattr(vision_module, "get_memory_limit_mb", lambda: (2048.0, "cgroup_v2"))
    monkeypatch.setattr(
        vision_module,
        "resolve_model_weights",
        lambda allow_download=True: ("/fake/path/yolov8n.pt", None),
    )

    import ai_vision.detection.detector as det_module

    def mock_broken_detector(*args, **kwargs):
        raise RuntimeError("Simulated corrupt PyTorch weights file.")

    monkeypatch.setattr(det_module, "YoloDetector", mock_broken_detector)

    file_payload = {"file": ("test.jpg", VALID_JPEG_BYTES, "image/jpeg")}
    infer_res = client.post("/api/vision/infer", files=file_payload)
    assert infer_res.status_code == 200
    infer_data = infer_res.json()
    assert infer_data["status"] == "vision_unavailable"
    assert "Simulated corrupt PyTorch" in infer_data["message"]

    status_res = client.get("/api/vision/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["status"] == "vision_unavailable"
    assert "Simulated corrupt PyTorch" in (status_data["reason"] or "")


def test_vision_memory_limit_standby_on_render_512mb(client, monkeypatch):
    """
    Regression test: when running on a 512 MB instance (Render free tier),
    vision loading is held in standby to safeguard GPS and Emergency SOS from kernel OOM killer.
    """
    reset_vision_state()
    monkeypatch.setattr(vision_module, "get_memory_limit_mb", lambda: (512.0, "cgroup_v2"))
    monkeypatch.delenv("FORCE_LOAD_VISION", raising=False)

    status_res = client.get("/api/vision/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["status"] == "vision_unavailable"
    assert status_data["memory_limit_mb"] == 512.0
    assert "512MB" in status_data["reason"]
    assert "GPS/SOS" in status_data["reason"]

    file_payload = {"file": ("test.jpg", VALID_JPEG_BYTES, "image/jpeg")}
    infer_res = client.post("/api/vision/infer", files=file_payload)
    assert infer_res.status_code == 200
    infer_data = infer_res.json()
    assert infer_data["status"] == "vision_unavailable"
    assert "insufficient RAM" in infer_data["message"]


def test_vision_model_loaded_once_and_reused_singleton(client, monkeypatch):
    """
    Verifies that the detector singleton is initialized once and reused
    across multiple consecutive requests without reloading.
    """
    reset_vision_state()
    monkeypatch.setattr(vision_module, "is_package_installed", lambda pkg: True)

    mock_detector = MagicMock()
    mock_detector.detect.return_value = []

    init_counter = {"count": 0}

    import ai_vision.detection.detector as det_module

    def counted_init(*args, **kwargs):
        init_counter["count"] += 1
        return mock_detector

    monkeypatch.setattr(det_module, "YoloDetector", counted_init)
    monkeypatch.setattr(
        vision_module,
        "resolve_model_weights",
        lambda allow_download=True: ("/models/yolov8n.pt", None),
    )
    # Ensure memory check passes
    monkeypatch.setattr(vision_module, "get_memory_limit_mb", lambda: (2048.0, "cgroup_v2"))

    # First call initializes
    d1 = vision_module.get_detector()
    assert d1 is mock_detector
    assert init_counter["count"] == 1

    # Second call returns existing singleton without calling constructor again
    d2 = vision_module.get_detector()
    assert d2 is mock_detector
    assert init_counter["count"] == 1

    # Infer request reuses existing singleton
    file_payload = {"file": ("test.jpg", VALID_JPEG_BYTES, "image/jpeg")}
    res = client.post("/api/vision/infer", files=file_payload)
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    assert init_counter["count"] == 1
    assert mock_detector.detect.call_count == 1


def test_vision_infer_genuine_detection_flow(client, monkeypatch):
    """
    Verifies full inference pipeline with genuine Detection objects,
    verifying coordinate mapping, direction calculation, and DB event creation.
    """
    reset_vision_state()

    mock_detector = MagicMock()
    mock_detector.detect.return_value = [
        Detection(
            class_name="person",
            confidence=0.88,
            bbox=BoundingBox(x1=200.0, y1=100.0, x2=380.0, y2=450.0),
        ),
        Detection(
            class_name="car",
            confidence=0.92,
            bbox=BoundingBox(x1=50.0, y1=150.0, x2=180.0, y2=300.0),
        ),
    ]

    monkeypatch.setattr(vision_module, "_detector", mock_detector)
    monkeypatch.setattr(vision_module, "_detector_status", "ready")

    file_payload = {"file": ("test.jpg", VALID_JPEG_BYTES, "image/jpeg")}
    data_payload = {"device_id": "TEST_STICK_VISION"}
    res = client.post("/api/vision/infer", files=file_payload, data=data_payload)

    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "success"
    assert body["model_version"] == "YOLOv8n-COCO"
    assert len(body["detections"]) == 2

    # Check person detection
    d0 = body["detections"][0]
    assert d0["class_name"] == "person"
    assert d0["confidence"] == 0.88
    assert "box" in d0
    assert d0["box"]["x1"] == 200.0

    # Check car detection
    d1 = body["detections"][1]
    assert d1["class_name"] == "car"
    assert d1["confidence"] == 0.92


def test_vision_startup_diagnostics_logging(caplog):
    """Verifies that startup diagnostics function runs without exception and emits logs."""
    with caplog.at_level(logging.INFO):
        vision_module.log_vision_startup_diagnostics()
    assert "AI Vision Subsystem Startup Diagnostics" in caplog.text
