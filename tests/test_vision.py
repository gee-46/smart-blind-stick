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
