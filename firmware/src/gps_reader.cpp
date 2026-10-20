/**
 * @file gps_reader.cpp
 * @brief Implementation of NEO-6M GPS Reader
 */

#include "gps_reader.h"

GPSReader::GPSReader(HardwareSerial& serial_port)
    : _serial(serial_port), _last_char_received_ms(0) {
    _data.latitude = 0.0;
    _data.longitude = 0.0;
    _data.altitude_m = 0.0f;
    _data.speed_kmh = 0.0f;
    _data.satellites = 0;
    _data.hdop = 99.99f;
    _data.fix_quality = 0;
    _data.has_valid_fix = false;
    _data.is_module_alive = false;
    _data.last_fix_timestamp_ms = 0;
    _data.seconds_since_last_fix = 999999;
}

bool GPSReader::begin() {
    _serial.begin(GPS_BAUDRATE, SERIAL_8N1, PIN_GPS_RX, PIN_GPS_TX);
    delay(50);
    return true;
}

bool GPSReader::update() {
    bool new_fix_encoded = false;

    while (_serial.available() > 0) {
        char c = _serial.read();
        _last_char_received_ms = millis();
        _data.is_module_alive = true;

        if (_gps.encode(c)) {
            new_fix_encoded = true;
        }
    }

    // Module vitality check (if no characters received for 3 seconds)
    if (millis() - _last_char_received_ms > 3000) {
        _data.is_module_alive = false;
        _data.has_valid_fix = false;
    }

    if (new_fix_encoded || _data.is_module_alive) {
        // Satellites tracking
        if (_gps.satellites.isValid()) {
            _data.satellites = _gps.satellites.value();
        } else {
            _data.satellites = 0;
        }

        // HDOP tracking
        if (_gps.hdop.isValid()) {
            _data.hdop = _gps.hdop.hdop();
        }

        // Altitude & Speed
        if (_gps.altitude.isValid()) {
            _data.altitude_m = _gps.altitude.meters();
        }
        if (_gps.speed.isValid()) {
            _data.speed_kmh = _gps.speed.kmph();
        }

        // Strict fix validity rules:
        // 1. Location must be reported valid by TinyGPS
        // 2. Latitude and Longitude must not be exactly 0.0
        // 3. Location age must be recent (< 3000ms)
        // 4. Must see at least 3 satellites
        if (_gps.location.isValid() &&
            _gps.location.age() < 3000 &&
            _data.satellites >= 3 &&
            (fabs(_gps.location.lat()) > 0.0001 || fabs(_gps.location.lng()) > 0.0001)) {

            _data.latitude = _gps.location.lat();
            _data.longitude = _gps.location.lng();
            _data.has_valid_fix = true;
            _data.fix_quality = 1; // Standard GPS fix
            _data.last_fix_timestamp_ms = millis();
            _data.seconds_since_last_fix = 0;
        } else {
            _data.has_valid_fix = false;
            _data.fix_quality = 0;
            if (_data.last_fix_timestamp_ms > 0) {
                _data.seconds_since_last_fix = (millis() - _data.last_fix_timestamp_ms) / 1000;
            } else {
                _data.seconds_since_last_fix = 999999;
            }
        }
    }

    return _data.has_valid_fix;
}
