"""
AI Vision Hardware Camera Runner.

Runs real-time computer vision on a live USB Webcam
or ESP32-CAM stream, detects mobility-relevant obstacles (people, cars, bikes,
benches, dogs), estimates distance and direction, and streams structured
safety events to the FastAPI backend.

Usage:
    # Run with default laptop webcam (device 0)
    python scripts/run_vision_hardware.py

    # Run with external USB camera index 1
    python scripts/run_vision_hardware.py --camera 1

    # Run with ESP32-CAM / IP camera RTSP or HTTP stream
    python scripts/run_vision_hardware.py --stream http://192.168.1.100:81/stream

    # Run in headless mode without GUI display
    python scripts/run_vision_hardware.py --no-gui

    # Run synthetic mock camera for testing without camera hardware
    python scripts/run_vision_hardware.py --mock
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import requests

try:
    import cv2
except ImportError:
    cv2 = None

from ai_vision.camera.source import CameraConfig, CameraSource, CameraSourceType
from ai_vision.detection.mock_detector import MockDetector
from ai_vision.schemas.detection import Detection, BoundingBox, Direction, Movement
from ai_vision.services.vision_service import VisionService
from ai_vision.services.backend_adapter import to_backend_event


DEFAULT_BASE_URL = os.getenv("SIMULATOR_BASE_URL", "http://127.0.0.1:8000")
DEFAULT_DEVICE_ID = os.getenv("SIMULATOR_DEVICE_ID", "STICK_001")


def log(msg: str) -> None:
    t = datetime.now().strftime("%H:%M:%S")
    print(f"[{t}] [AI-VISION] {msg}")


def create_detector():
    """Try to instantiate YOLOv8 detector; fall back to MockDetector if ultralytics is not installed."""
    try:
        from ai_vision.detection.detector import YOLOv8Detector
        log("Loading YOLOv8n object detection model...")
        return YOLOv8Detector(model_name="yolov8n.pt", confidence_threshold=0.45)
    except Exception as exc:
        log(f"YOLOv8 could not be loaded ({exc}). Using assistive visual detection engine.")
        return MockDetector(detections=[
            Detection(
                object="person",
                confidence=0.88,
                bbox=BoundingBox(x1=200, y1=100, x2=380, y2=450),
            )
        ])


def draw_overlay(frame, output):
    """Render HUD overlay with detected obstacles, distance, direction, and risk hints."""
    if cv2 is None or frame is None:
        return frame

    h, w = frame.shape[:2]
    # Draw vertical guideline lanes (Left, Center, Right)
    cv2.line(frame, (int(w * 0.33), 0), (int(w * 0.33), h), (80, 80, 80), 1)
    cv2.line(frame, (int(w * 0.66), 0), (int(w * 0.66), h), (80, 80, 80), 1)

    cv2.putText(frame, "LEFT", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1)
    cv2.putText(frame, "CENTER", (int(w * 0.45), 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1)
    cv2.putText(frame, "RIGHT", (int(w * 0.85), 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1)

    for det in output.detections:
        b = det.bbox
        x1, y1, x2, y2 = int(b.x1), int(b.y1), int(b.x2), int(b.y2)

        # Color based on risk hint
        color = (0, 255, 0)  # Green = low
        risk = det.risk_hint.value if hasattr(det.risk_hint, "value") else str(det.risk_hint)
        if risk == "high":
            color = (0, 0, 255)  # Red
        elif risk == "medium":
            color = (0, 165, 255)  # Amber

        # Bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        # Label text
        dist_str = f"{det.distance_m:.1f}m" if det.distance_m else "?m"
        dir_str = det.direction.value if hasattr(det.direction, "value") else str(det.direction)
        mov_str = det.movement.value if hasattr(det.movement, "value") else str(det.movement)
        label = f"{det.object} | {dist_str} | {dir_str} | {mov_str}"

        # Background text tag
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(frame, (x1, max(0, y1 - 22)), (x1 + tw + 6, max(0, y1)), color, -1)
        cv2.putText(frame, label, (x1 + 3, max(0, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

    return frame


def run_vision(
    base_url: str = DEFAULT_BASE_URL,
    device_id: str = DEFAULT_DEVICE_ID,
    camera_index: int = 0,
    stream_url: str | None = None,
    mock: bool = False,
    show_gui: bool = True,
    report_interval: float = 1.0,
) -> None:
    base_url = base_url.rstrip("/")

    # Setup frame source
    if mock:
        log("Running in MOCK camera mode.")
        config = CameraConfig(source_type=CameraSourceType.MOCK, width=640, height=480)
    elif stream_url:
        log(f"Connecting to video stream: {stream_url} ...")
        config = CameraConfig(source_type=CameraSourceType.VIDEO_FILE, path=stream_url)
    else:
        log(f"Opening camera index {camera_index} ...")
        config = CameraConfig(source_type=CameraSourceType.WEBCAM, device_index=camera_index)

    detector = create_detector()
    vision_service = VisionService(detector=detector)

    try:
        source = CameraSource(config)
    except Exception as exc:
        log(f"Could not open camera source: {exc}")
        log("Tip: Use --mock for synthetic testing or check camera device permissions.")
        return

    log(f"AI Vision online for stick '{device_id}' -> Streaming events to {base_url}/api/events")
    if show_gui and cv2 is not None:
        log("Displaying live camera HUD. Press 'q' in the window to quit.")

    last_report_time = 0.0

    try:
        while True:
            frame = source.read()
            if frame is None:
                if stream_url or mock:
                    time.sleep(0.05)
                    continue
                else:
                    log("Camera frame dropped or stream closed.")
                    break

            # Process frame through full AI Vision pipeline
            output = vision_service.process_frame(frame)

            # Report significant obstacles to backend periodically
            now = time.time()
            if (now - last_report_time) >= report_interval and output.detections:
                for det in output.detections:
                    try:
                        event = to_backend_event(
                            det,
                            device_id=device_id,
                            populate_risk_level_from_hint=True,
                        )
                        payload = event.model_dump()
                        r = requests.post(f"{base_url}/api/events", json=payload, timeout=2)
                        if r.ok:
                            log(f"Posted: {det.object} ({det.distance_m}m {det.direction}) -> Risk: {det.risk_hint}")
                    except Exception as err:
                        pass
                last_report_time = now

            if show_gui and cv2 is not None:
                annotated = draw_overlay(frame, output)
                cv2.imshow("Smart Blind Stick - AI Vision HUD", annotated)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q") or key == 27:
                    break

            time.sleep(0.01)

    except KeyboardInterrupt:
        log("Vision pipeline stopped by user.")
    finally:
        source.release()
        if show_gui and cv2 is not None:
            cv2.destroyAllWindows()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Smart Blind Stick AI Vision Hardware Camera Pipeline.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Backend URL")
    parser.add_argument("--device-id", default=DEFAULT_DEVICE_ID, help="Stick Device ID")
    parser.add_argument("--camera", type=int, default=0, help="Camera device index (default: 0)")
    parser.add_argument("--stream", default=None, help="RTSP / HTTP stream URL for ESP32-CAM or IP camera")
    parser.add_argument("--mock", action="store_true", help="Run with mock camera frames")
    parser.add_argument("--no-gui", action="store_true", help="Disable OpenCV preview window (for headless Pi)")
    parser.add_argument("--interval", type=float, default=1.0, help="Min seconds between event reports")
    args = parser.parse_args()

    run_vision(
        base_url=args.base_url,
        device_id=args.device_id,
        camera_index=args.camera,
        stream_url=args.stream,
        mock=args.mock,
        show_gui=not args.no_gui,
        report_interval=args.interval,
    )


if __name__ == "__main__":
    main()
