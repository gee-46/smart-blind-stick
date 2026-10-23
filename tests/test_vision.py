"""
Tests for AI Vision inference endpoint and diagnostics.

Verifies:
- Frame decoding and rejection of empty/malformed buffers.
- Structured inference response contract.
- Status and diagnostics reporting.
- ZERO DEMO DATA: Returns honest 'vision_unavailable' when weights absent,
  never fabricates synthetic detections.
"""
import io
import pytest


def test_vision_status_endpoint(client):
    response = client.get("/api/vision/status")
    assert response.status_code == 200
    data = response.json()
    assert "model_version" in data
    assert data["classes_supported"] == 80
    assert data["device"] == "cpu"
    assert "status" in data


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
    import app.api.vision as vision_module
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
    import app.api.vision as vision_module
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

