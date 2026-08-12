"""
Real GPS reader for a serial/UART-connected module (NEO-6M, NEO-7M,
NEO-M8N, or any GPS chip that outputs standard NMEA-0183 sentences).

This replaces the mock GPS generator (app/services/location_service.py::
generate_mock_gps_point) with an actual hardware read. It has no
dependency on FastAPI or the rest of the backend -- it is a small,
standalone, testable unit: read raw NMEA sentences off a serial port and
turn them into a `GPSFix`.

--------------------------------------------------------------------------
Wiring (Raspberry Pi example, NEO-6M module)
--------------------------------------------------------------------------
    GPS module      Raspberry Pi
    -----------      ------------
    VCC        ->    5V (or 3.3V, check your module's datasheet)
    GND        ->    GND
    TX         ->    GPIO15 / RXD (pin 10)
    RX         ->    GPIO14 / TXD (pin 8)

Before this will work on a Pi you must free up the hardware UART:
    sudo raspi-config
      -> Interface Options -> Serial Port
         "Login shell over serial?"      -> No
         "Enable serial port hardware?"  -> Yes
    sudo reboot

The module will then be available at /dev/serial0 (the default `port`
below). On other boards/USB GPS dongles it's typically /dev/ttyUSB0 or
/dev/ttyACM0 (Linux/Pi) or COM3 etc. (Windows) -- pass `--port` to
scripts/gps_device_client.py accordingly.

--------------------------------------------------------------------------
NMEA fix quality (from the GGA sentence)
--------------------------------------------------------------------------
    0 = no fix        3 = PPS fix        6 = estimated (dead reckoning)
    1 = GPS fix        4 = RTK fixed        7 = manual input
    2 = DGPS fix        5 = RTK float        8 = simulation

A fix_quality of 0 means "no satellites locked yet" -- this is normal for
the first 30-60 seconds after cold power-on, especially indoors. This
reader will not return a `GPSFix` until quality > 0.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

import pynmea2

logger = logging.getLogger("gps_reader")


class SerialLike(Protocol):
    """Minimal interface this module needs from a serial connection.

    Satisfied by `serial.Serial` (pyserial) and, in tests, by a fake
    in-memory stream -- so GPS parsing logic can be unit tested without
    any physical hardware attached.
    """

    def readline(self) -> bytes: ...
    def close(self) -> None: ...


FIX_QUALITY_LABELS = {
    0: "no fix",
    1: "GPS fix",
    2: "DGPS fix",
    3: "PPS fix",
    4: "RTK fixed",
    5: "RTK float",
    6: "estimated",
    7: "manual",
    8: "simulation",
}


def fix_quality_label(fix_quality: int | None) -> str:
    if fix_quality is None:
        return "unknown"
    return FIX_QUALITY_LABELS.get(fix_quality, f"unknown ({fix_quality})")


@dataclass
class GPSFix:
    latitude: float
    longitude: float
    altitude: float | None
    speed_kmh: float | None
    satellites: int | None
    fix_quality: int
    timestamp: datetime

    @property
    def has_fix(self) -> bool:
        return self.fix_quality > 0


class NEO6MGPSReader:
    """
    Reads NMEA sentences from a serial GPS module and returns parsed
    position fixes.

    Works with any NMEA-0183 GPS module (NEO-6M and compatible chips are
    the common/cheap choice for hobby GPS projects), not just the exact
    NEO-6M part.
    """

    def __init__(
        self,
        port: str = "/dev/serial0",
        baudrate: int = 9600,
        timeout: float = 1.0,
        serial_conn: SerialLike | None = None,
    ):
        """
        `serial_conn` can be injected directly (e.g. in tests, or if the
        caller already opened the port). If omitted, this opens a real
        `serial.Serial` connection -- pyserial is only imported here so
        the rest of this module stays importable/testable without it
        installed in restricted environments.
        """
        if serial_conn is not None:
            self.serial_conn: SerialLike = serial_conn
        else:
            import serial  # local import: only required for real hardware use

            self.serial_conn = serial.Serial(port, baudrate, timeout=timeout)

        self._last_gga = None
        self._last_rmc_speed_kmh: float | None = None

    def _read_line(self) -> str | None:
        try:
            raw = self.serial_conn.readline()
        except Exception as exc:  # serial disconnects, permission errors, etc.
            logger.warning("Serial read failed: %s", exc)
            return None

        if not raw:
            return None  # timeout with no data

        try:
            return raw.decode("ascii", errors="replace").strip()
        except Exception:
            return None

    def _handle_sentence(self, line: str) -> GPSFix | None:
        if not line.startswith("$"):
            return None

        try:
            # check=False: tolerate the occasional corrupted checksum on
            # noisy UART links rather than dropping an otherwise-usable fix.
            msg = pynmea2.parse(line, check=False)
        except pynmea2.ParseError:
            return None

        sentence_type = getattr(msg, "sentence_type", "")

        if sentence_type in ("RMC",):
            speed_knots = getattr(msg, "spd_over_grnd", None)
            if speed_knots not in (None, ""):
                try:
                    self._last_rmc_speed_kmh = round(float(speed_knots) * 1.852, 2)
                except (TypeError, ValueError):
                    pass
            return None

        if sentence_type not in ("GGA",):
            return None

        # GGA carries position, altitude, fix quality, and satellite count.
        try:
            fix_quality = int(msg.gps_qual) if msg.gps_qual is not None else 0
        except (TypeError, ValueError):
            fix_quality = 0

        if fix_quality == 0:
            logger.debug("GGA sentence received but no fix yet (quality=0)")
            return None

        if msg.latitude in (None, 0) and msg.longitude in (None, 0):
            return None

        satellites = None
        if msg.num_sats not in (None, ""):
            try:
                satellites = int(msg.num_sats)
            except ValueError:
                satellites = None

        altitude = None
        if msg.altitude not in (None, ""):
            try:
                altitude = float(msg.altitude)
            except (TypeError, ValueError):
                altitude = None

        return GPSFix(
            latitude=float(msg.latitude),
            longitude=float(msg.longitude),
            altitude=altitude,
            speed_kmh=self._last_rmc_speed_kmh,
            satellites=satellites,
            fix_quality=fix_quality,
            timestamp=datetime.now(timezone.utc),
        )

    def read_fix(self, max_lines: int = 100) -> GPSFix | None:
        """
        Reads up to `max_lines` NMEA sentences looking for a valid
        position fix (from a GGA sentence). Returns None if no valid fix
        was found in that window (e.g. module still acquiring satellites,
        or indoors with no sky view).

        Ground speed (from RMC) is attached if a recent RMC sentence
        provided one; otherwise `speed_kmh` is None.
        """
        for _ in range(max_lines):
            line = self._read_line()
            if line is None:
                continue

            fix = self._handle_sentence(line)
            if fix is not None:
                return fix

        return None

    def close(self) -> None:
        self.serial_conn.close()

    def __enter__(self) -> "NEO6MGPSReader":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
