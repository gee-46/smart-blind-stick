"""
AI Vision API: Real-time Camera Inference & Diagnostics.

Receives genuine JPEG camera frames from the ESP32-CAM companion node,
executes the YOLOv8n detection pipeline, computes movement and direction,
and broadcasts verified obstacle events to paired guardians.

ZERO DEMO DATA: Never fabricates detections. If model weights are missing
or camera is disconnected, returns 'vision_unavailable'.
"""
import time
from datetime import datetime, timezone
from typing import Optional

import numpy as np
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.event import EventIn
from app.services import event_service
from app.websocket_manager import manager as ws_manager

try:
    import cv2
except ImportError:
    cv2 = None

router = APIRouter(prefix="/api/vision", tags=["vision"])

# Lazy-loaded YOLO detector singleton
_detector = None
_detector_init_attempted = False
_model_version = "YOLOv8n-COCO"


def get_detector():
    global _detector, _detector_init_attempted
    if _detector is None and not _detector_init_attempted:
        _detector_init_attempted = True
        try:
            from ai_vision.detection.detector import YoloDetector
            _detector = YoloDetector(model_path="models/yolov8n.pt", confidence_threshold=0.45)
        except Exception:
            try:
                # Try root yolov8n.pt
                from ai_vision.detection.detector import YoloDetector
                _detector = YoloDetector(model_path="yolov8n.pt", confidence_threshold=0.45)
            except Exception:
                _detector = None
    return _detector


@router.post("/infer")
async def infer_frame(
    file: UploadFile = File(...),
    device_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Ingest a real JPEG frame from the ESP32-CAM, run genuine YOLOv8n
    inference, and return honest detections or 'vision_unavailable'.
    """
    start_time = time.perf_counter()
    now_iso = datetime.now(timezone.utc).isoformat()
    dev_id = device_id or "STICK_001"

    if cv2 is None:
        return {
            "model_version": _model_version,
            "status": "vision_unavailable",
            "timestamp": now_iso,
            "device_id": dev_id,
            "detections": [],
            "latency_ms": 0.0,
            "message": "OpenCV is not available on server.",
        }

    contents = await file.read()
    if not contents:
        return {
            "model_version": _model_version,
            "status": "invalid_frame",
            "timestamp": now_iso,
            "device_id": dev_id,
            "detections": [],
            "latency_ms": 0.0,
            "message": "Empty frame buffer received.",
        }

    # Decode JPEG to BGR numpy array
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is None:
        return {
            "model_version": _model_version,
            "status": "invalid_frame",
            "timestamp": now_iso,
            "device_id": dev_id,
            "detections": [],
            "latency_ms": 0.0,
            "message": "Failed to decode JPEG frame.",
        }

    detector = get_detector()
    if detector is None:
        latency = (time.perf_counter() - start_time) * 1000.0
        return {
            "model_version": _model_version,
            "status": "vision_unavailable",
            "timestamp": now_iso,
            "device_id": dev_id,
            "detections": [],
            "latency_ms": round(latency, 2),
            "message": "Vision inference model not loaded or weights unavailable.",
        }

    # Execute genuine YOLO detection
    try:
        raw_detections = detector.detect(frame)
    except Exception as exc:
        latency = (time.perf_counter() - start_time) * 1000.0
        return {
            "model_version": _model_version,
            "status": "inference_error",
            "timestamp": now_iso,
            "device_id": dev_id,
            "detections": [],
            "latency_ms": round(latency, 2),
            "message": f"Inference execution failed: {str(exc)}",
        }

    formatted_detections = []
    frame_width = frame.shape[1]

    for det in raw_detections:
        # Determine direction based on box center X relative to frame width
        center_x = (det.box.x1 + det.box.x2) / 2.0
        norm_x = center_x / max(frame_width, 1)

        if norm_x < 0.33:
            direction = "left"
        elif norm_x > 0.66:
            direction = "right"
        else:
            direction = "center"

        formatted_detections.append({
            "class_name": det.class_name,
            "confidence": round(det.confidence, 3),
            "direction": direction,
            "box": {
                "x1": round(det.box.x1, 1),
                "y1": round(det.box.y1, 1),
                "x2": round(det.box.x2, 1),
                "y2": round(det.box.y2, 1),
            },
        })

        # If a critical object is detected (e.g. vehicle, truck, bus), relay genuine event
        if det.class_name in ("car", "bus", "truck", "motorcycle", "person") and det.confidence >= 0.70:
            try:
                event_in = EventIn(
                    device_id=dev_id,
                    source="ai_vision",
                    event_type="object_detected",
                    risk_level="high" if det.class_name in ("car", "bus", "truck") else "medium",
                    message=f"{det.class_name.capitalize()} detected {direction}",
                    extra={
                        "object": det.class_name,
                        "confidence": det.confidence,
                        "direction": direction,
                    },
                )
                event_service.create_event(db, event_in)
            except Exception:
                pass

    latency = (time.perf_counter() - start_time) * 1000.0

    return {
        "model_version": _model_version,
        "status": "success",
        "timestamp": now_iso,
        "device_id": dev_id,
        "detections": formatted_detections,
        "latency_ms": round(latency, 2),
    }


@router.get("/status")
def get_vision_status():
    """Return runtime status of the AI Vision inference service."""
    detector = get_detector()
    is_ready = detector is not None
    return {
        "model_version": _model_version,
        "status": "ready" if is_ready else "vision_unavailable",
        "classes_supported": 80,
        "device": "cpu",
        "opencv_available": cv2 is not None,
    }
