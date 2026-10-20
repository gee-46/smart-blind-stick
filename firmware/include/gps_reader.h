/**
 * @file gps_reader.h
 * @brief NEO-6M GPS NMEA Sentence Parser & Fix Validator
 */

#ifndef GPS_READER_H
#define GPS_READER_H

#include <Arduino.h>
#include <HardwareSerial.h>
#include <TinyGPSPlus.h>
#include "pinout.h"
#include "config.h"

struct GPSData {
    double latitude;
    double longitude;
    float altitude_m;
    float speed_kmh;
    uint32_t satellites;
    float hdop;
    uint8_t fix_quality;
    bool has_valid_fix;
    bool is_module_alive;
    uint32_t last_fix_timestamp_ms;
    uint32_t seconds_since_last_fix;
};

class GPSReader {
public:
    GPSReader(HardwareSerial& serial_port = Serial1);

    bool begin();
    bool update();

    const GPSData& getData() const { return _data; }
    bool hasValidFix() const { return _data.has_valid_fix; }
    double getLatitude() const { return _data.latitude; }
    double getLongitude() const { return _data.longitude; }
    uint32_t getSatellites() const { return _data.satellites; }
    bool isModuleAlive() const { return _data.is_module_alive; }

private:
    HardwareSerial& _serial;
    TinyGPSPlus _gps;
    GPSData _data;
    uint32_t _last_char_received_ms;
};

#endif // GPS_READER_H
