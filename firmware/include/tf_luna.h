/**
 * @file tf_luna.h
 * @brief TF-Luna Time-of-Flight LiDAR Sensor Driver
 */

#ifndef TF_LUNA_H
#define TF_LUNA_H

#include <Arduino.h>
#include <HardwareSerial.h>
#include "pinout.h"
#include "config.h"

enum class ObstacleLevel {
    NONE = 0,
    NOTICE = 1,     // 120cm - 200cm
    WARNING = 2,    // 50cm - 120cm
    CRITICAL = 3    // < 50cm
};

struct TFLunaData {
    int16_t distance_cm;
    uint16_t signal_strength;
    float temperature_c;
    bool is_valid;
    bool is_sensor_healthy;
    ObstacleLevel alert_level;
    uint32_t last_update_ms;
};

class TFLunaSensor {
public:
    TFLunaSensor(HardwareSerial& serial_port = Serial2);
    
    bool begin();
    bool update();
    
    const TFLunaData& getData() const { return _data; }
    int16_t getDistanceCm() const { return _data.distance_cm; }
    bool isValid() const { return _data.is_valid; }
    bool isHealthy() const { return _data.is_sensor_healthy; }
    ObstacleLevel getAlertLevel() const { return _data.alert_level; }

private:
    HardwareSerial& _serial;
    TFLunaData _data;
    uint8_t _packet_buffer[9];
    uint8_t _buffer_index;
    uint32_t _last_successful_read_ms;
    ObstacleLevel _current_level;

    bool parsePacket(const uint8_t* buffer);
    void updateAlertLevel(int16_t distance);
};

#endif // TF_LUNA_H
