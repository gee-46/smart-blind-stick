"""Mock Smart Stick Device Simulator.

Simulates periodic check-ins, battery decay, GPS movement, and occasional
sensor/AI/safety events for testing the backend without physical hardware.

Usage:
    python scripts/simulate_device.py
    python scripts/simulate_device.py --device-id STICK_002 --interval 3
    python scripts/simulate_device.py --once
"""
import argparse
import os
import random
import time
from datetime import datetime
from typing import Optional

import requests

try:
    from app.services.location_service import LocationService
except ImportError:
    LocationService = None  # type: ignore

DEFAULT_BASE_URL = os.getenv("SIMULATOR_BASE_URL", "http://127.0.0.1:8000")
DEFAULT_DEVICE_ID = os.getenv("SIMULATOR_DEVICE_ID", "STICK_001")
DEFAULT_INTERVAL = float(os.getenv("SIMULATOR_INTERVAL_SECONDS", "5"))

BASE_LAT = 12.9716
BASE_LNG = 77.5946

STATUSES = ["active", "safe", "moving", "idle"]

SAMPLE_EVENTS = [
    {
        "source": "sensor_fusion",
        "event_type": "obstacle",
        "risk_level": "medium",
        "message": "Obstacle detected on left",
        "extra": {"distance": 1.4, "direction": "left", "level": "head", "confidence": 0.91},
    },
    {
        "source": "ai_vision",
        "event_type": "object_detected",
        "risk_level": "high",
        "message": "Vehicle approaching from right",
        "extra": {
            "object": "vehicle",
            "distance": 2.1,
            "direction": "right",
            "movement": "approaching",
            "confidence": 0.94,
        },
    },
    {
        "source": "safety_engine",
        "event_type": "danger",
        "risk_level": "critical",
        "message": "Immediate danger",
    },
]


class DeviceSimulator:
    def __init__(self, base_url: str = DEFAULT_BASE_URL, device_id: str = DEFAULT_DEVICE_ID):
        self.base_url = base_url.rstrip("/")
        self.device_id = device_id
        self.battery = 98.0
        self.latitude = BASE_LAT
        self.longitude = BASE_LNG

    def _drift_battery(self) -> float:
        self.battery = max(0.0, round(self.battery - random.uniform(0.05, 0.2), 1))
        return self.battery

    def _drift_gps(self) -> tuple[float, float]:
        if LocationService and hasattr(LocationService, "generate_mock_gps_point"):
            self.latitude, self.longitude = LocationService.generate_mock_gps_point(
                base_lat=self.latitude, base_lon=self.longitude, drift_radius_meters=15.0
            )
        else:
            self.latitude = round(self.latitude + random.uniform(-0.0002, 0.0002), 6)
            self.longitude = round(self.longitude + random.uniform(-0.0002, 0.0002), 6)
        return self.latitude, self.longitude

    def send_checkin(self) -> None:
        lat, lng = self._drift_gps()
        payload = {
            "device_id": self.device_id,
            "battery": self._drift_battery(),
            "status": random.choice(STATUSES),
            "latitude": lat,
            "longitude": lng,
            "gps_available": True,
        }
        try:
            response = requests.post(f"{self.base_url}/api/device/data", json=payload, timeout=5)
            self._log("check-in", payload, response)
        except Exception as err:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] check-in  -> FAILED: {err}")

    def maybe_send_event(self, probability: float = 0.3) -> None:
        if random.random() > probability:
            return
        event = dict(random.choice(SAMPLE_EVENTS))
        event["device_id"] = self.device_id
        try:
            response = requests.post(f"{self.base_url}/api/events", json=event, timeout=5)
            self._log("event", event, response)
        except Exception as err:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] event     -> FAILED: {err}")

    @staticmethod
    def _log(kind: str, payload: dict, response: requests.Response) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        status = f"OK ({response.status_code})" if response.ok else f"FAILED ({response.status_code})"
        print(f"[{timestamp}] {kind:<9} -> {status} | {payload}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate Smart Blind Stick Hardware")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Backend base URL")
    parser.add_argument("--device-id", default=DEFAULT_DEVICE_ID, help="Simulated device ID")
    parser.add_argument(
        "--interval", type=float, default=DEFAULT_INTERVAL, help="Seconds between check-ins"
    )
    parser.add_argument("--events", action="store_true", default=True, help="Send random simulated events")
    parser.add_argument("--once", action="store_true", help="Send single check-in then exit")
    args = parser.parse_args()

    simulator = DeviceSimulator(base_url=args.base_url, device_id=args.device_id)

    print(f"[*] Simulating device '{args.device_id}' against {args.base_url}")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            simulator.send_checkin()
            if args.events:
                simulator.maybe_send_event()
            if args.once:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nSimulator stopped.")


if __name__ == "__main__":
    main()

