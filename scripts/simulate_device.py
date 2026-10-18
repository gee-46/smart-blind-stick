<<<<<<< HEAD
"""
Mock device simulator.

Simulates a smart stick sending periodic check-ins (battery + GPS +
status) to the backend, plus occasional sensor/AI/safety-style events.
This lets the whole backend be exercised end-to-end before any physical
hardware exists.

Usage:
    python scripts/simulate_device.py
    python scripts/simulate_device.py --device-id STICK_002 --interval 3
    python scripts/simulate_device.py --once

Configuration can also come from environment variables (see .env.example):
    SIMULATOR_BASE_URL, SIMULATOR_DEVICE_ID, SIMULATOR_INTERVAL_SECONDS
"""
import argparse
import os
import random
import time
from datetime import datetime

import requests

DEFAULT_BASE_URL = os.getenv("SIMULATOR_BASE_URL", "http://127.0.0.1:8000")
DEFAULT_DEVICE_ID = os.getenv("SIMULATOR_DEVICE_ID", "STICK_001")
DEFAULT_INTERVAL = int(os.getenv("SIMULATOR_INTERVAL_SECONDS", "5"))

BASE_LAT = 15.8497
BASE_LNG = 74.4977

STATUSES = ["safe", "moving", "idle"]

# Mimics events that would eventually come from the other three modules.
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
    def __init__(self, base_url: str, device_id: str):
        self.base_url = base_url.rstrip("/")
        self.device_id = device_id
        self.battery = 100
        self.latitude = BASE_LAT
        self.longitude = BASE_LNG

    def _drift_battery(self) -> int:
        self.battery = max(0, self.battery - random.randint(0, 1))
        return self.battery

    def _drift_gps(self) -> tuple[float, float]:
        self.latitude = round(self.latitude + random.uniform(-0.0008, 0.0008), 6)
        self.longitude = round(self.longitude + random.uniform(-0.0008, 0.0008), 6)
        return self.latitude, self.longitude

    def send_checkin(self) -> None:
        lat, lng = self._drift_gps()
        payload = {
            "device_id": self.device_id,
            "battery": self._drift_battery(),
            "latitude": lat,
            "longitude": lng,
            "status": random.choice(STATUSES),
        }
        response = requests.post(f"{self.base_url}/api/device/data", json=payload, timeout=5)
        self._log("check-in", payload, response)

    def maybe_send_event(self, probability: float = 0.3) -> None:
        if random.random() > probability:
            return
        event = dict(random.choice(SAMPLE_EVENTS))
        event["device_id"] = self.device_id
        response = requests.post(f"{self.base_url}/api/events", json=event, timeout=5)
        self._log("event", event, response)

    @staticmethod
    def _log(kind: str, payload: dict, response: requests.Response) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        status = "OK" if response.ok else f"FAILED ({response.status_code})"
        print(f"[{timestamp}] {kind:<9} -> {status} | {payload}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate a smart blind stick device.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Backend base URL")
    parser.add_argument("--device-id", default=DEFAULT_DEVICE_ID, help="Simulated device ID")
    parser.add_argument(
        "--interval", type=float, default=DEFAULT_INTERVAL, help="Seconds between check-ins"
    )
    parser.add_argument("--once", action="store_true", help="Send a single check-in and exit")
    args = parser.parse_args()

    simulator = DeviceSimulator(base_url=args.base_url, device_id=args.device_id)

    print(f"Simulating device '{args.device_id}' against {args.base_url}")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            simulator.send_checkin()
            simulator.maybe_send_event()
            if args.once:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nSimulator stopped.")
=======
"""Mock Smart Stick Device Simulator.

Simulates periodic check-ins, battery decay, and GPS movement for testing the backend
without physical ESP32 hardware.
"""
import argparse
import random
import time
import requests

from app.services.location_service import LocationService


def simulate_stick(
    base_url: str = "http://127.0.0.1:8000",
    device_id: str = "STICK_001",
    interval: int = 5,
    once: bool = False,
):
    print(f"🦯 Starting device simulation for '{device_id}' -> {base_url}")
    battery = 98.0
    lat, lon = 12.9716, 77.5946

    while True:
        # Simulate slight GPS walking movement
        lat, lon = LocationService.generate_mock_gps_point(base_lat=lat, base_lon=lon, drift_radius_meters=15.0)
        battery = max(0.0, round(battery - random.uniform(0.05, 0.2), 1))

        payload = {
            "device_id": device_id,
            "battery": battery,
            "status": "active",
            "latitude": lat,
            "longitude": lon,
            "gps_available": True,
        }

        try:
            res = requests.post(f"{base_url}/api/device/data", json=payload, timeout=5)
            print(f"[{time.strftime('%X')}] Check-in: Status={res.status_code}, Battery={battery}%, GPS=({lat}, {lon})")
        except Exception as err:
            print(f"[{time.strftime('%X')}] ❌ Check-in failed: {err}")

        if once:
            break
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="Simulate Smart Blind Stick Hardware")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="API base URL")
    parser.add_argument("--device-id", default="STICK_001", help="Device ID")
    parser.add_argument("--interval", type=int, default=5, help="Seconds between check-ins")
    parser.add_argument("--once", action="store_true", help="Send single check-in then exit")
    args = parser.parse_args()

    simulate_stick(
        base_url=args.base_url,
        device_id=args.device_id,
        interval=args.interval,
        once=args.once,
    )
>>>>>>> origin/feature/safety-emergency


if __name__ == "__main__":
    main()
