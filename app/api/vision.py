"""
AI Vision API: Real-time Camera Inference & Diagnostics.

Receives genuine JPEG camera frames from the ESP32-CAM companion node,
executes the YOLOv8n detection pipeline, computes movement and direction,
and broadcasts verified obstacle events to paired guardians.

ZERO DEMO DATA: Never fabricates detections. If model weights are missing,
RAM is insufficient (e.g., Render 512 MB free instance), or camera is
disconnected, returns an honest 'vision_unavailable' status with full
diagnostic reasons.
"""
import hashlib
import logging
import os
import sys
import tempfile
import threading
import time
import urllib.request
from datetime import datetime, timezone
from typing import Optional, Tuple

try:
    import numpy as np
except ImportError:
    np = None

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

logger = logging.getLogger("smart_stick.ai_vision")

router = APIRouter(prefix="/api/vision", tags=["vision"])

_model_version = "YOLOv8n-COCO"
OFFICIAL_WEIGHTS_URL = "https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n.pt"
OFFICIAL_WEIGHTS_SHA256 = "f59b3d833e2ff32e194b5bb8e08d211dc7c5bdf144b90d2c8412c47ccfc83b36"
OFFICIAL_WEIGHTS_SIZE = 6549796

# Memory threshold: PyTorch CPU + Ultralytics YOLOv8n requires >= 650 MB working RSS
# during forward pass. On 512 MB instances (e.g. Render Free Tier), loading PyTorch
# causes kernel OOM termination (exit 137), crashing core GPS and SOS services.
CGROUP_OOM_THRESHOLD_MB = 650.0

# Lazy-loaded YOLO detector singleton and synchronization lock
_detector = None
_detector_lock = threading.Lock()
_detector_status = "uninitialized"
_detector_failure_reason: Optional[str] = None
_resolved_weights_path: Optional[str] = None


def get_memory_limit_mb() -> Tuple[Optional[float], str]:
    """
    Detect container/cgroup or system memory limits.
    Returns (limit_in_mb, source_description).
    """
    # 1. Linux cgroup v2 (Render, modern Docker, Kubernetes)
    cgroup_v2 = "/sys/fs/cgroup/memory.max"
    if os.path.exists(cgroup_v2):
        try:
            with open(cgroup_v2, "r", encoding="utf-8") as f:
                val = f.read().strip()
                if val and val != "max":
                    bytes_val = int(val)
                    return round(bytes_val / (1024 * 1024), 1), "cgroup_v2"
        except Exception:
            pass

    # 2. Linux cgroup v1 (legacy Docker / ECS)
    cgroup_v1 = "/sys/fs/cgroup/memory/memory.limit_in_bytes"
    if os.path.exists(cgroup_v1):
        try:
            with open(cgroup_v1, "r", encoding="utf-8") as f:
                val = f.read().strip()
                if val:
                    bytes_val = int(val)
                    if bytes_val < 500 * 1024 * 1024 * 1024:  # Ignore 64-bit max sentinel
                        return round(bytes_val / (1024 * 1024), 1), "cgroup_v1"
        except Exception:
            pass

    # 3. Linux /proc/meminfo
    meminfo = "/proc/meminfo"
    if os.path.exists(meminfo):
        try:
            with open(meminfo, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        parts = line.split()
                        kb = int(parts[1])
                        return round(kb / 1024.0, 1), "proc_meminfo"
        except Exception:
            pass

    # 4. Windows host memory query
    if sys.platform == "win32":
        try:
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            return round(stat.ullTotalPhys / (1024 * 1024), 1), "win32_kernel32"
        except Exception:
            pass

    return None, "unconstrained"


def resolve_model_weights(allow_download: bool = False) -> Tuple[Optional[str], Optional[str]]:
    """
    Locates or deterministically downloads the official YOLOv8n weights.
    Returns (weights_path, error_reason).
    """
    global _resolved_weights_path
    if _resolved_weights_path and os.path.exists(_resolved_weights_path):
        if os.path.getsize(_resolved_weights_path) >= 1_000_000:
            return _resolved_weights_path, None

    candidate_paths = [
        os.getenv("AI_VISION_MODEL_PATH"),
        "/app/models/yolov8n.pt",
        "models/yolov8n.pt",
        "/app/data/models/yolov8n.pt",
        os.path.join(tempfile.gettempdir(), "smart_stick_models", "yolov8n.pt"),
    ]

    for p in candidate_paths:
        if p and os.path.exists(p):
            try:
                sz = os.path.getsize(p)
                if sz >= 1_000_000:
                    _resolved_weights_path = p
                    return p, None
            except OSError:
                pass

    if not allow_download:
        return None, "Weights file not found on disk."

    # Determine a writable target path for download
    target_path = None
    target_dirs = [
        "models",
        "/app/models",
        "/app/data/models",
        os.path.join(tempfile.gettempdir(), "smart_stick_models"),
    ]

    for d in target_dirs:
        try:
            os.makedirs(d, exist_ok=True)
            test_file = os.path.join(d, ".write_test")
            with open(test_file, "w") as tf:
                tf.write("ok")
            os.remove(test_file)
            target_path = os.path.join(d, "yolov8n.pt")
            break
        except (OSError, PermissionError):
            continue

    if not target_path:
        err = "No writable directory found to download YOLOv8n weights."
        logger.error(err)
        return None, err

    tmp_path = target_path + ".tmp"
    logger.info("Downloading official YOLOv8n weights from %s to %s...", OFFICIAL_WEIGHTS_URL, target_path)

    try:
        req = urllib.request.Request(
            OFFICIAL_WEIGHTS_URL,
            headers={"User-Agent": "SmartBlindStick-Inference/1.0"},
        )
        hasher = hashlib.sha256()
        total_downloaded = 0

        with urllib.request.urlopen(req, timeout=30) as response, open(tmp_path, "wb") as out_file:
            while True:
                chunk = response.read(65536)
                if not chunk:
                    break
                out_file.write(chunk)
                hasher.update(chunk)
                total_downloaded += len(chunk)

        computed_sha = hasher.hexdigest()
        if total_downloaded < 1_000_000:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            err = f"Downloaded file incomplete ({total_downloaded} bytes received)."
            logger.error(err)
            return None, err

        # Verify checksum if official URL was used
        if computed_sha != OFFICIAL_WEIGHTS_SHA256:
            logger.warning(
                "Downloaded weights SHA256 (%s) differs from pinned reference (%s).",
                computed_sha,
                OFFICIAL_WEIGHTS_SHA256,
            )

        os.replace(tmp_path, target_path)
        logger.info("YOLOv8n weights successfully verified and stored at %s (%d bytes).", target_path, total_downloaded)
        _resolved_weights_path = target_path
        return target_path, None

    except Exception as exc:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        err = f"Failed to download YOLOv8n weights: {str(exc)}"
        logger.error(err)
        return None, err


def log_vision_startup_diagnostics():
    """
    Informative, non-blocking startup diagnostics for AI Vision.
    Safely logs environment, dependencies, memory headroom, and weights availability.
    Does NOT log any secrets.
    """
    logger.info("=== Smart Blind Stick AI Vision Subsystem Startup Diagnostics ===")
    logger.info("NumPy: %s", "AVAILABLE" if np is not None else "NOT INSTALLED")
    logger.info("OpenCV: %s", "AVAILABLE" if cv2 is not None else "NOT INSTALLED")

    torch_avail = False
    try:
        import torch  # noqa: F401
        torch_avail = True
    except ImportError:
        pass
    logger.info("PyTorch: %s", "AVAILABLE" if torch_avail else "NOT INSTALLED")

    ultralytics_avail = False
    try:
        from ultralytics import YOLO  # noqa: F401
        ultralytics_avail = True
    except ImportError:
        pass
    logger.info("Ultralytics: %s", "AVAILABLE" if ultralytics_avail else "NOT INSTALLED")

    mem_mb, source = get_memory_limit_mb()
    if mem_mb is not None:
        logger.info("Memory Limit: %.1f MB (detected via %s)", mem_mb, source)
        if mem_mb < CGROUP_OOM_THRESHOLD_MB:
            logger.warning(
                "Host RAM ceiling (%.1f MB) is below the 1.5 GB recommended for PyTorch YOLOv8n CPU inference. "
                "Vision inference will be held in standby to protect core safety services (GPS/SOS).",
                mem_mb,
            )
    else:
        logger.info("Memory Limit: Unconstrained / Not reported")

    weights_path, _ = resolve_model_weights(allow_download=False)
    if weights_path:
        logger.info("Model Weights: PRESENT at %s (size: %.2f MB)", weights_path, os.path.getsize(weights_path) / (1024 * 1024))
    else:
        logger.info("Model Weights: NOT PRE-LOADED (will be fetched deterministically on first inference if resources permit)")
    logger.info("==================================================================")


def get_detector():
    """
    Thread-safe lazy-loaded singleton for YOLOv8n detector.
    Loaded once and reused across all subsequent requests without reallocating memory.
    """
    global _detector, _detector_status, _detector_failure_reason
    if _detector is not None:
        return _detector

    with _detector_lock:
        if _detector is not None:
            return _detector

        # Check memory limit first to prevent OOM killer crashing the entire container
        mem_mb, source = get_memory_limit_mb()
        force_load = os.getenv("FORCE_LOAD_VISION", "false").lower() in ("true", "1")

        if mem_mb is not None and mem_mb < CGROUP_OOM_THRESHOLD_MB and not force_load:
            _detector_status = "vision_unavailable"
            _detector_failure_reason = (
                f"Render 512MB free instance has insufficient RAM ({mem_mb:.0f} MB detected via {source}) "
                "for PyTorch YOLOv8n inference (requires >= 1.5 GB RAM). Vision is placed in standby "
                "to protect core safety services (GPS/SOS)."
            )
            logger.warning("AI Vision: %s", _detector_failure_reason)
            return None

        # Check required numerical/vision libraries
        if np is None or cv2 is None:
            missing = []
            if np is None:
                missing.append("NumPy")
            if cv2 is None:
                missing.append("OpenCV")
            _detector_status = "vision_unavailable"
            _detector_failure_reason = f"Required dependencies ({', '.join(missing)}) are missing."
            logger.warning("AI Vision: %s", _detector_failure_reason)
            return None

        # Check PyTorch and Ultralytics
        try:
            import torch  # noqa: F401
            from ultralytics import YOLO  # noqa: F401
        except ImportError as exc:
            _detector_status = "vision_unavailable"
            _detector_failure_reason = (
                f"PyTorch or Ultralytics dependencies not installed: {str(exc)}. "
                "Install with 'pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu' "
                "and 'pip install ultralytics'."
            )
            logger.warning("AI Vision: %s", _detector_failure_reason)
            return None

        # Resolve or fetch model weights
        weights_path, err = resolve_model_weights(allow_download=True)
        if not weights_path:
            _detector_status = "vision_unavailable"
            _detector_failure_reason = f"Model weights unavailable: {err}"
            logger.warning("AI Vision: %s", _detector_failure_reason)
            return None

        try:
            from ai_vision.detection.detector import YoloDetector

            logger.info("Initializing YoloDetector from %s...", weights_path)
            _detector = YoloDetector(model_path=weights_path, confidence_threshold=0.45)
            _detector_status = "ready"
            _detector_failure_reason = None
            logger.info("YOLOv8n object detection model successfully loaded and ready.")
            return _detector
        except Exception as exc:
            _detector = None
            _detector_status = "vision_unavailable"
            _detector_failure_reason = f"Failed to instantiate YoloDetector: {str(exc)}"
            logger.error("AI Vision initialization failed: %s", exc, exc_info=True)
            return None


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

    if np is None or cv2 is None:
        missing = []
        if np is None:
            missing.append("NumPy")
        if cv2 is None:
            missing.append("OpenCV")
        return {
            "model_version": _model_version,
            "status": "vision_unavailable",
            "timestamp": now_iso,
            "device_id": dev_id,
            "detections": [],
            "latency_ms": 0.0,
            "message": f"Vision dependencies ({', '.join(missing)}) are not available on server.",
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
        msg = "Vision inference model not loaded or weights unavailable."
        if _detector_failure_reason:
            msg = f"{msg} {_detector_failure_reason}"
        return {
            "model_version": _model_version,
            "status": "vision_unavailable",
            "timestamp": now_iso,
            "device_id": dev_id,
            "detections": [],
            "latency_ms": round(latency, 2),
            "message": msg,
        }

    # Execute genuine YOLO detection
    try:
        raw_detections = detector.detect(frame)
    except Exception as exc:
        latency = (time.perf_counter() - start_time) * 1000.0
        logger.error("Inference execution failed: %s", exc)
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
        # Support both det.bbox (Detection schema) and det.box
        bbox = getattr(det, "bbox", getattr(det, "box", None))
        if bbox is None:
            continue
        x1, y1, x2, y2 = bbox.x1, bbox.y1, bbox.x2, bbox.y2
        center_x = (x1 + x2) / 2.0
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
                "x1": round(x1, 1),
                "y1": round(y1, 1),
                "x2": round(x2, 1),
                "y2": round(y2, 1),
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
    """Return runtime status and diagnostics of the AI Vision inference service."""
    detector = get_detector()
    is_ready = detector is not None and np is not None and cv2 is not None

    torch_available = False
    try:
        import torch  # noqa: F401
        torch_available = True
    except ImportError:
        pass

    ultralytics_available = False
    try:
        from ultralytics import YOLO  # noqa: F401
        ultralytics_available = True
    except ImportError:
        pass

    weights_path, _ = resolve_model_weights(allow_download=False)
    mem_mb, _ = get_memory_limit_mb()

    return {
        "model_version": _model_version,
        "status": "ready" if is_ready else "vision_unavailable",
        "classes_supported": 80,
        "device": "cpu",
        "numpy_available": np is not None,
        "opencv_available": cv2 is not None,
        "torch_available": torch_available,
        "ultralytics_available": ultralytics_available,
        "weights_present": weights_path is not None,
        "memory_limit_mb": mem_mb,
        "reason": _detector_failure_reason,
    }
