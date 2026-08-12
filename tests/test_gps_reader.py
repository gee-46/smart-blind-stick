"""
Tests for the real-GPS NMEA parsing logic (scripts/gps_reader.py).

No physical GPS hardware or serial port is required: `FakeSerial` stands
in for a `serial.Serial` connection and feeds pre-recorded NMEA sentences
line-by-line, exactly as the real module would.
"""
import pytest

from scripts.gps_reader import NEO6MGPSReader, fix_quality_label


def _nmea_checksum(body: str) -> str:
    cs = 0
    for c in body:
        cs ^= ord(c)
    return f"{cs:02X}"


def _sentence(body: str) -> str:
    """Builds a correctly-checksummed NMEA sentence from a body string
    (without the leading '$' or trailing '*CS')."""
    return f"${body}*{_nmea_checksum(body)}"


# A real fix: 48.1173 N, 11.516666 E, altitude 545.4m, 8 satellites, quality 1
GGA_FIX = _sentence("GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,")

# No fix yet (quality 0, 0 satellites) -- typical right after cold power-on
GGA_NO_FIX = _sentence("GPGGA,123519,4807.038,N,01131.000,E,0,00,,,,,,,")

# Matching RMC sentence with ground speed of 22.4 knots
RMC_WITH_SPEED = _sentence("GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W")

GARBAGE_LINE = "not an nmea sentence at all"

CORRUPTED_CHECKSUM = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*00"


class FakeSerial:
    """Minimal stand-in for serial.Serial -- yields pre-set lines, then empty bytes."""

    def __init__(self, lines: list[str]):
        self._lines = list(lines)
        self.closed = False

    def readline(self) -> bytes:
        if self._lines:
            return (self._lines.pop(0) + "\r\n").encode("ascii")
        return b""  # simulates a read timeout with no data

    def close(self) -> None:
        self.closed = True


def make_reader(lines: list[str]) -> NEO6MGPSReader:
    return NEO6MGPSReader(serial_conn=FakeSerial(lines))


def test_read_fix_parses_valid_gga():
    reader = make_reader([GGA_FIX])
    fix = reader.read_fix(max_lines=5)

    assert fix is not None
    assert fix.fix_quality == 1
    assert fix.has_fix is True
    assert fix.satellites == 8
    assert fix.altitude == pytest.approx(545.4)
    assert fix.latitude == pytest.approx(48.1173, abs=1e-3)
    assert fix.longitude == pytest.approx(11.5167, abs=1e-3)


def test_read_fix_returns_none_when_no_fix_yet():
    reader = make_reader([GGA_NO_FIX])
    fix = reader.read_fix(max_lines=5)
    assert fix is None


def test_read_fix_attaches_speed_from_preceding_rmc():
    reader = make_reader([RMC_WITH_SPEED, GGA_FIX])
    fix = reader.read_fix(max_lines=5)

    assert fix is not None
    # 22.4 knots -> km/h
    assert fix.speed_kmh == pytest.approx(22.4 * 1.852, abs=0.01)


def test_read_fix_skips_garbage_and_corrupted_lines():
    reader = make_reader([GARBAGE_LINE, CORRUPTED_CHECKSUM, GGA_FIX])
    fix = reader.read_fix(max_lines=10)

    assert fix is not None
    assert fix.fix_quality == 1


def test_read_fix_returns_none_when_stream_exhausted_without_fix():
    reader = make_reader([GGA_NO_FIX, GARBAGE_LINE])
    fix = reader.read_fix(max_lines=10)
    assert fix is None


def test_read_fix_respects_max_lines():
    # Fix is present but beyond the max_lines window -- should not be found.
    reader = make_reader([GARBAGE_LINE, GARBAGE_LINE, GARBAGE_LINE, GGA_FIX])
    fix = reader.read_fix(max_lines=2)
    assert fix is None


def test_close_closes_underlying_connection():
    fake = FakeSerial([GGA_FIX])
    reader = NEO6MGPSReader(serial_conn=fake)
    reader.close()
    assert fake.closed is True


def test_context_manager_closes_connection():
    fake = FakeSerial([GGA_FIX])
    with NEO6MGPSReader(serial_conn=fake) as reader:
        fix = reader.read_fix(max_lines=5)
        assert fix is not None
    assert fake.closed is True


def test_fix_quality_label_known_values():
    assert fix_quality_label(0) == "no fix"
    assert fix_quality_label(1) == "GPS fix"
    assert fix_quality_label(2) == "DGPS fix"


def test_fix_quality_label_unknown_value():
    assert "unknown" in fix_quality_label(99)


def test_fix_quality_label_none():
    assert fix_quality_label(None) == "unknown"
