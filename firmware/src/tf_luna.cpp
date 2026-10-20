/**
 * @file tf_luna.cpp
 * @brief Implementation of TF-Luna LiDAR Distance Reader
 */

#include "tf_luna.h"

TFLunaSensor::TFLunaSensor(HardwareSerial& serial_port)
    : _serial(serial_port), _buffer_index(0), _last_successful_read_ms(0), _current_level(ObstacleLevel::NONE) {
    _data.distance_cm = -1;
    _data.signal_strength = 0;
    _data.temperature_c = 0.0f;
    _data.is_valid = false;
    _data.is_sensor_healthy = false;
    _data.alert_level = ObstacleLevel::NONE;
    _data.last_update_ms = 0;
}

bool TFLunaSensor::begin() {
    _serial.begin(TFLUNA_BAUDRATE, SERIAL_8N1, PIN_TFLUNA_RX, PIN_TFLUNA_TX);
    delay(50);
    
    // Empty RX buffer
    while (_serial.available()) {
        _serial.read();
    }
    
    _data.is_sensor_healthy = true;
    _last_successful_read_ms = millis();
    return true;
}

bool TFLunaSensor::update() {
    bool new_reading_obtained = false;

    while (_serial.available() > 0) {
        uint8_t byte_in = _serial.read();

        // Looking for sync headers 0x59 0x59
        if (_buffer_index == 0) {
            if (byte_in == 0x59) {
                _packet_buffer[0] = byte_in;
                _buffer_index = 1;
            }
        } else if (_buffer_index == 1) {
            if (byte_in == 0x59) {
                _packet_buffer[1] = byte_in;
                _buffer_index = 2;
            } else {
                _buffer_index = 0; // Sync lost
            }
        } else {
            _packet_buffer[_buffer_index++] = byte_in;

            // Full 9-byte packet received
            if (_buffer_index == 9) {
                if (parsePacket(_packet_buffer)) {
                    new_reading_obtained = true;
                }
                _buffer_index = 0;
            }
        }
    }

    // Health check: sensor considered unhealthy if no valid packet received for 1000ms
    if (millis() - _last_successful_read_ms > 1000) {
        _data.is_sensor_healthy = false;
        _data.is_valid = false;
        _data.alert_level = ObstacleLevel::NONE;
    }

    return new_reading_obtained;
}

bool TFLunaSensor::parsePacket(const uint8_t* buffer) {
    // Checksum verification: low 8 bits of sum of bytes 0..7
    uint8_t checksum = 0;
    for (int i = 0; i < 8; i++) {
        checksum += buffer[i];
    }

    if (checksum != buffer[8]) {
        // Corrupted packet
        return false;
    }

    uint16_t raw_dist = (buffer[3] << 8) | buffer[2];
    uint16_t raw_flux = (buffer[5] << 8) | buffer[4];
    int16_t raw_temp = (buffer[7] << 8) | buffer[6];

    _data.signal_strength = raw_flux;
    _data.temperature_c = (float)raw_temp / 8.0f - 256.0f;
    _data.last_update_ms = millis();

    // Validity conditions:
    // 1. Signal strength (flux) >= 100 (below 100 reading is noisy or diffused)
    // 2. Distance in operational range (20 cm to 800 cm)
    if (raw_flux >= 100 && raw_dist >= DISTANCE_MIN_VALID_CM && raw_dist <= DISTANCE_MAX_VALID_CM) {
        _data.distance_cm = (int16_t)raw_dist;
        _data.is_valid = true;
        _data.is_sensor_healthy = true;
        _last_successful_read_ms = millis();
        updateAlertLevel(_data.distance_cm);
        return true;
    } else {
        // Measurement out of range or signal absorbed
        _data.is_valid = false;
        _data.distance_cm = -1;
        _data.alert_level = ObstacleLevel::NONE;
        return false;
    }
}

void TFLunaSensor::updateAlertLevel(int16_t dist) {
    if (!_data.is_valid || dist <= 0) {
        _current_level = ObstacleLevel::NONE;
        _data.alert_level = _current_level;
        return;
    }

    // Apply hysteresis band around thresholds
    switch (_current_level) {
        case ObstacleLevel::CRITICAL:
            if (dist > (DISTANCE_CRITICAL_CM + DISTANCE_HYSTERESIS_CM)) {
                _current_level = ObstacleLevel::WARNING;
            }
            break;
            
        case ObstacleLevel::WARNING:
            if (dist <= DISTANCE_CRITICAL_CM) {
                _current_level = ObstacleLevel::CRITICAL;
            } else if (dist > (DISTANCE_WARNING_CM + DISTANCE_HYSTERESIS_CM)) {
                _current_level = ObstacleLevel::NOTICE;
            }
            break;
            
        case ObstacleLevel::NOTICE:
            if (dist <= DISTANCE_WARNING_CM) {
                _current_level = ObstacleLevel::WARNING;
            } else if (dist > (DISTANCE_NOTICE_CM + DISTANCE_HYSTERESIS_CM)) {
                _current_level = ObstacleLevel::NONE;
            }
            break;
            
        case ObstacleLevel::NONE:
        default:
            if (dist <= DISTANCE_CRITICAL_CM) {
                _current_level = ObstacleLevel::CRITICAL;
            } else if (dist <= DISTANCE_WARNING_CM) {
                _current_level = ObstacleLevel::WARNING;
            } else if (dist <= DISTANCE_NOTICE_CM) {
                _current_level = ObstacleLevel::NOTICE;
            }
            break;
    }

    _data.alert_level = _current_level;
}
