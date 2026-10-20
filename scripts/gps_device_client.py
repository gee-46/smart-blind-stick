"""
Real GPS device client.

Reads real position fixes via scripts/gps_reader.py from an attached
NEO-6M GPS receiver or USB-UART bridge and posts them to the backend's
existing /api/device/data endpoint.
"""
import argparse
import os
import time
from datetime import datetime

import requests

try:
    from scripts.gps_reader import NEO6MGPSReader, fix_quality_label
except ImportError:
    from gps_reader import NEO6MGPSReader, fix_quality_label

try:
    import serial.tools.list_ports
except ImportError:
    serial = None

DEFAULT_BASE_URL = os.getenv("SIMULATOR_BASE_URL", "http://127.0.0.1:8000")
DEFAULT_DEVICE_ID = os.getenv("SIMULATOR_DEVICE_ID", "STICK_001")
DEFAULT_PORT = os.getenv("GPS_SERIAL_PORT", "/dev/serial0")
DEFAULT_BAUDRATE = int(os.getenv("GPS_BAUDRATE", "9600"))
DEFAULT_INTERVAL = float(os.getenv("SIMULATOR_INTERVAL_SECONDS", "5"))


def read_battery_percent() -> int:
    """
    Placeholder battery reader.

    TODO(feature/safety-emergency or hardware owner): replace this with a
    real fuel-gauge / ADC read once the battery monitoring circuit is
    wired (e.g. an INA219 current sensor or a MAX17048 fuel gauge over
    I2C). Until then this returns a fixed value so real GPS tracking can
    be tested end-to-end without battery hardware blocking it.
    """
    return 100


def send_checkin(base_url: str, device_id: str, fix, status: str = "safe") -> requests.Response:
    payload = {
        "device_id": device_id,
        "battery": read_battery_percent(),
        "latitude": fix.latitude,
        "longitude": fix.longitude,
        "status": status,
        "altitude": fix.altitude,
        "speed_kmh": fix.speed_kmh,
        "satellites": fix.satellites,
        "fix_quality": fix.fix_quality,
    }
    return requests.post(f"{base_url}/api/device/data", json=payload, timeout=5)


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read real GPS fixes from a serial GPS module and send them to the backend."
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Backend base URL")
    parser.add_argument("--device-id", default=DEFAULT_DEVICE_ID, help="This stick's device ID")
    parser.add_argument("--port", default=DEFAULT_PORT, help="Serial port the GPS module is on")
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUDRATE, help="Serial baud rate")
    parser.add_argument(
        "--interval", type=float, default=DEFAULT_INTERVAL, help="Seconds between check-ins"
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=100,
        help="Max NMEA lines to read per attempt before giving up on a fix",
    )
    parser.add_argument("--once", action="store_true", help="Send a single check-in and exit")
    args = parser.parse_args()

    log(f"Opening GPS module on {args.port} @ {args.baud} baud ...")
    try:
        reader = NEO6MGPSReader(port=args.port, baudrate=args.baud, timeout=1.0)
    except Exception as exc:
        log(f"Could not open serial port '{args.port}': {exc}")
        if serial and hasattr(serial, "tools") and hasattr(serial.tools, "list_ports"):
            ports = [p.device for p in serial.tools.list_ports.comports()]
            if ports:
                log(f"Detected available serial ports on this machine: {', '.join(ports)}")
                log(f"Try running with: --port {ports[0]}")
            else:
                log("No active serial ports detected. Check USB/UART physical connections.")
        log("Check wiring, port name, and that the UART is enabled (see gps_reader.py docstring).")
        return

    log(f"Reading real GPS and sending check-ins to {args.base_url} for device '{args.device_id}'")
    log("Press Ctrl+C to stop.\n")

    try:
        while True:
            fix = reader.read_fix(max_lines=args.max_lines)

            if fix is None:
                log("No GPS fix yet (acquiring satellites / no sky view) -- skipping check-in.")
            else:
                try:
                    response = send_checkin(args.base_url, args.device_id, fix)
                    status = "OK" if response.ok else f"FAILED ({response.status_code})"
                    log(
                        f"check-in -> {status} | "
                        f"lat={fix.latitude:.6f} lon={fix.longitude:.6f} "
                        f"alt={fix.altitude} sats={fix.satellites} "
                        f"fix={fix_quality_label(fix.fix_quality)}"
                    )
                except requests.RequestException as exc:
                    log(f"check-in -> FAILED to reach backend: {exc}")

            if args.once:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        log("Stopped.")
    finally:
        reader.close()


if __name__ == "__main__":
    main()
