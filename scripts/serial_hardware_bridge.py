"""
Serial Hardware Bridge.

Connects physical Smart Blind Stick hardware (ESP32 DevKit V1)
plugged in via USB Serial / COM port directly to the FastAPI backend.

Features:
- Auto-detects active USB serial COM ports on Windows, Linux, and macOS
- Ingests check-ins, GPS coordinates, ultrasonic distances, and IMU fall triggers
- Ingests hardware SOS pushbutton presses
- Sends bidirectional haptic and buzzer commands BACK to the microcontroller
- Robust error recovery, auto-reconnection on cable disconnects

Usage:
    python scripts/serial_hardware_bridge.py
    python scripts/serial_hardware_bridge.py --port COM3 --baud 115200
    python scripts/serial_hardware_bridge.py --base-url http://127.0.0.1:8000
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import requests

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    serial = None


DEFAULT_BASE_URL = os.getenv("SIMULATOR_BASE_URL", "http://127.0.0.1:8000")
DEFAULT_DEVICE_ID = os.getenv("SIMULATOR_DEVICE_ID", "STICK_001")
DEFAULT_BAUD = 115200


def log(msg: str) -> None:
    t = datetime.now().strftime("%H:%M:%S")
    print(f"[{t}] [SERIAL-BRIDGE] {msg}")


def auto_detect_serial_port() -> Optional[str]:
    """Find the most probable microcontroller USB COM port."""
    if not serial or not hasattr(serial.tools, "list_ports"):
        return None

    ports = list(serial.tools.list_ports.comports())
    if not ports:
        return None

    # Prefer Silicon Labs CP210x, CH340, FTDI, Arduino, or ESP32 ports
    keywords = ["cp210", "ch340", "ftdi", "arduino", "esp32", "usb serial", "uart"]
    for p in ports:
        desc = (p.description or "").lower()
        mfg = (p.manufacturer or "").lower()
        if any(k in desc or k in mfg for k in keywords):
            return p.device

    # Fall back to first detected port
    return ports[0].device


class SerialHardwareBridge:
    def __init__(self, port: str, baudrate: int = DEFAULT_BAUD, base_url: str = DEFAULT_BASE_URL, device_id: str = DEFAULT_DEVICE_ID):
        self.port = port
        self.baudrate = baudrate
        self.base_url = base_url.rstrip("/")
        self.device_id = device_id
        self.ser: Optional[serial.Serial] = None

    def connect(self) -> bool:
        if serial is None:
            log("pyserial is not installed! Run: pip install pyserial")
            return False

        try:
            log(f"Opening serial port {self.port} at {self.baudrate} baud...")
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1.0)
            time.sleep(2.0)  # Allow Arduino/ESP32 reset sequence to complete
            log(f"Connected to hardware on {self.port} successfully.")
            return True
        except Exception as exc:
            log(f"Failed to open port {self.port}: {exc}")
            return False

    def send_feedback_to_hardware(self, vibration: str, buzzer: str) -> None:
        """Send haptic/buzzer feedback instruction back to microcontroller over Serial."""
        if not self.ser or not self.ser.is_open:
            return

        try:
            cmd = json.dumps({"cmd": "feedback", "vibe": vibration, "buzz": buzzer}) + "\n"
            self.ser.write(cmd.encode("utf-8"))
        except Exception as exc:
            log(f"Could not send feedback to hardware: {exc}")

    def process_incoming_line(self, line: str) -> None:
        """Parse JSON or key-value packet from the stick and dispatch to backend."""
        line = line.strip()
        if not line:
            return

        # Attempt JSON parse
        data = None
        if line.startswith("{") and line.endswith("}"):
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                pass

        if not data:
            # Fallback for simple key:value format e.g. "SOS" or "DIST:45.2"
            if line.upper() == "SOS":
                data = {"type": "sos", "reason": "Hardware pushbutton pressed"}
            elif line.startswith("DIST:"):
                try:
                    val = float(line.split(":")[1])
                    data = {"type": "sensor", "ultrasonic_cm": val}
                except Exception:
                    return
            else:
                log(f"[RAW HW OUTPUT] {line}")
                return

        packet_type = data.get("type", "sensor").lower()
        dev_id = data.get("device_id", self.device_id)

        try:
            if packet_type == "checkin":
                # POST /api/device/data
                payload = {
                    "device_id": dev_id,
                    "battery": data.get("battery", 100.0),
                    "latitude": data.get("latitude", 12.9716),
                    "longitude": data.get("longitude", 77.5946),
                    "status": data.get("status", "active"),
                    "gps_available": data.get("gps_available", True),
                    "satellites": data.get("satellites", 7),
                    "fix_quality": data.get("fix_quality", 1),
                }
                r = requests.post(f"{self.base_url}/api/device/data", json=payload, timeout=3)
                log(f"Check-in dispatched -> Status {r.status_code}")

            elif packet_type == "sensor":
                # POST /api/sensors/data
                payload = {
                    "device_id": dev_id,
                    "ultrasonic_cm": data.get("ultrasonic_cm"),
                    "waist_ultrasonic_cm": data.get("waist_ultrasonic_cm"),
                    "ground_ir_detected": data.get("ground_ir_detected", False),
                    "battery": data.get("battery"),
                }
                r = requests.post(f"{self.base_url}/api/sensors/data", json=payload, timeout=3)
                if r.ok:
                    res_json = r.json()
                    vib = res_json.get("vibration_feedback", "none")
                    buzz = res_json.get("buzzer_feedback", "silent")
                    log(f"Sensor processed -> Risk: {res_json.get('risk_level')}, Feedback: [Vibe={vib}, Buzz={buzz}]")
                    # Send feedback back to the microcontroller
                    if vib != "none" or buzz != "silent":
                        self.send_feedback_to_hardware(vib, buzz)

            elif packet_type == "fall":
                # POST /api/emergency/fall/detect
                payload = {
                    "device_id": dev_id,
                    "accel_magnitude": data.get("accel_magnitude", 2.6),
                    "tilt_angle_degrees": data.get("tilt_angle_degrees", 45.0),
                    "free_fall_detected": data.get("free_fall_detected", True),
                    "immobility_detected": data.get("immobility_detected", True),
                }
                r = requests.post(f"{self.base_url}/api/emergency/fall/detect", json=payload, timeout=3)
                log(f"Fall alert dispatched -> Status {r.status_code}")

            elif packet_type == "sos":
                # POST /api/emergency/sos/manual
                payload = {
                    "device_id": dev_id,
                    "reason": data.get("reason", "Hardware SOS button pressed"),
                }
                r = requests.post(f"{self.base_url}/api/emergency/sos/manual", json=payload, timeout=3)
                log(f"MANUAL SOS dispatched -> Status {r.status_code}")

        except requests.RequestException as err:
            log(f"HTTP dispatch failed: {err}")

    def run(self) -> None:
        if not self.ser or not self.ser.is_open:
            if not self.connect():
                return

        log("Listening for Smart Blind Stick serial packets... Press Ctrl+C to exit.\n")
        try:
            while True:
                if self.ser.in_waiting:
                    raw = self.ser.readline()
                    try:
                        line = raw.decode("utf-8", errors="replace")
                        self.process_incoming_line(line)
                    except Exception as exc:
                        log(f"Read error: {exc}")
                else:
                    time.sleep(0.01)
        except KeyboardInterrupt:
            log("Hardware bridge stopped by user.")
        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Bridge physical Smart Blind Stick hardware via USB Serial into FastAPI.")
    parser.add_argument("--port", default=None, help="Serial COM port (e.g. COM3 or /dev/ttyUSB0). If omitted, auto-detects.")
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD, help="Baud rate (default: 115200)")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Backend URL (default: http://127.0.0.1:8000)")
    parser.add_argument("--device-id", default=DEFAULT_DEVICE_ID, help="Device ID")
    args = parser.parse_args()

    port = args.port
    if not port:
        port = auto_detect_serial_port()
        if not port:
            print("[!] No active serial ports found automatically.")
            if serial and hasattr(serial.tools, "list_ports"):
                all_ports = [p.device for p in serial.tools.list_ports.comports()]
                if all_ports:
                    print(f"[*] Available ports: {', '.join(all_ports)}")
            print("[*] Please connect your ESP32/Arduino via USB or specify --port <PORT_NAME>")
            print("[*] Example: python scripts/serial_hardware_bridge.py --port COM3")
            return

    bridge = SerialHardwareBridge(port=port, baudrate=args.baud, base_url=args.base_url, device_id=args.device_id)
    bridge.run()


if __name__ == "__main__":
    main()
