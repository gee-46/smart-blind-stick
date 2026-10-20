/**
 * @file mpu6050_fall.cpp
 * @brief Implementation of MPU6050 Motion and Multi-Stage Fall Pipeline
 */

#include "mpu6050_fall.h"
#include <math.h>

#define MPU6050_PWR_MGMT_1   0x6B
#define MPU6050_ACCEL_CONFIG 0x1C
#define MPU6050_GYRO_CONFIG  0x1B
#define MPU6050_ACCEL_XOUT_H 0x3B

MPU6050FallDetector::MPU6050FallDetector(uint8_t i2c_addr)
    : _address(i2c_addr), _freefall_timestamp_ms(0), _impact_timestamp_ms(0),
      _pre_impact_pitch(0), _pre_impact_roll(0), _smooth_accel_g(1.0f),
      _rest_variance_accumulator(0), _sample_count(0) {
    _data.accel_x_g = 0.0f;
    _data.accel_y_g = 0.0f;
    _data.accel_z_g = 1.0f;
    _data.total_accel_g = 1.0f;
    _data.gyro_x_dps = 0.0f;
    _data.gyro_y_dps = 0.0f;
    _data.gyro_z_dps = 0.0f;
    _data.total_gyro_dps = 0.0f;
    _data.pitch_deg = 0.0f;
    _data.roll_deg = 0.0f;
    _data.is_sensor_healthy = false;
    _data.fall_state = FallState::MONITORING;
    _data.fall_confidence = 0.0f;
    _data.fall_detected_flag = false;
}

bool MPU6050FallDetector::begin() {
    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL, 400000); // 400kHz fast I2C
    delay(50);

    // Wake up MPU-6050 (clear SLEEP bit in PWR_MGMT_1)
    Wire.beginTransmission(_address);
    Wire.write(MPU6050_PWR_MGMT_1);
    Wire.write(0x00);
    uint8_t err = Wire.endTransmission();

    if (err != 0) {
        _data.is_sensor_healthy = false;
        return false;
    }

    // Configure Accel to +/- 4g (AFS_SEL = 1 -> 8192 LSB/g)
    Wire.beginTransmission(_address);
    Wire.write(MPU6050_ACCEL_CONFIG);
    Wire.write(0x08);
    Wire.endTransmission();

    // Configure Gyro to +/- 500 deg/s (FS_SEL = 1 -> 65.5 LSB/(deg/s))
    Wire.beginTransmission(_address);
    Wire.write(MPU6050_GYRO_CONFIG);
    Wire.write(0x08);
    Wire.endTransmission();

    _data.is_sensor_healthy = true;
    return true;
}

bool MPU6050FallDetector::readRawSensors(int16_t& ax, int16_t& ay, int16_t& az, int16_t& gx, int16_t& gy, int16_t& gz) {
    Wire.beginTransmission(_address);
    Wire.write(MPU6050_ACCEL_XOUT_H);
    uint8_t err = Wire.endTransmission(false); // Restart
    if (err != 0) {
        _data.is_sensor_healthy = false;
        return false;
    }

    uint8_t count = Wire.requestFrom(_address, (uint8_t)14, (uint8_t)true);
    if (count < 14) {
        _data.is_sensor_healthy = false;
        return false;
    }

    ax = (Wire.read() << 8) | Wire.read();
    ay = (Wire.read() << 8) | Wire.read();
    az = (Wire.read() << 8) | Wire.read();
    Wire.read(); Wire.read(); // Skip temperature
    gx = (Wire.read() << 8) | Wire.read();
    gy = (Wire.read() << 8) | Wire.read();
    gz = (Wire.read() << 8) | Wire.read();

    _data.is_sensor_healthy = true;
    return true;
}

bool MPU6050FallDetector::update() {
    int16_t raw_ax, raw_ay, raw_az;
    int16_t raw_gx, raw_gy, raw_gz;

    if (!readRawSensors(raw_ax, raw_ay, raw_az, raw_gx, raw_gy, raw_gz)) {
        return false;
    }

    // Scale to engineering units (+/- 4g -> 8192 LSB/g; +/- 500 dps -> 65.5 LSB/dps)
    _data.accel_x_g = (float)raw_ax / 8192.0f;
    _data.accel_y_g = (float)raw_ay / 8192.0f;
    _data.accel_z_g = (float)raw_az / 8192.0f;

    _data.gyro_x_dps = (float)raw_gx / 65.5f;
    _data.gyro_y_dps = (float)raw_gy / 65.5f;
    _data.gyro_z_dps = (float)raw_gz / 65.5f;

    // Magnitudes
    float total_a = sqrtf(_data.accel_x_g * _data.accel_x_g +
                          _data.accel_y_g * _data.accel_y_g +
                          _data.accel_z_g * _data.accel_z_g);
    _data.total_accel_g = total_a;

    float total_g = sqrtf(_data.gyro_x_dps * _data.gyro_x_dps +
                          _data.gyro_y_dps * _data.gyro_y_dps +
                          _data.gyro_z_dps * _data.gyro_z_dps);
    _data.total_gyro_dps = total_g;

    // Pitch and roll angles from accelerometer
    _data.pitch_deg = atan2f(-_data.accel_x_g, sqrtf(_data.accel_y_g * _data.accel_y_g + _data.accel_z_g * _data.accel_z_g)) * 180.0f / M_PI;
    _data.roll_deg  = atan2f(_data.accel_y_g, _data.accel_z_g) * 180.0f / M_PI;

    evaluateFallPipeline(total_a, total_g, _data.pitch_deg, _data.roll_deg);
    return true;
}

void MPU6050FallDetector::evaluateFallPipeline(float total_a, float total_g, float pitch, float roll) {
    uint32_t now = millis();

    switch (_data.fall_state) {
        case FallState::MONITORING:
            // Stage 1: Candidate Free-fall condition (|a| < FALL_FREEFALL_G)
            if (total_a < FALL_FREEFALL_G) {
                _data.fall_state = FallState::FREEFALL_CANDIDATE;
                _freefall_timestamp_ms = now;
                _pre_impact_pitch = pitch;
                _pre_impact_roll = roll;
            }
            break;

        case FallState::FREEFALL_CANDIDATE:
            // Freefall must transition to impact within 800ms
            if (now - _freefall_timestamp_ms > 800) {
                // Freefall timeout without impact -> reset
                _data.fall_state = FallState::MONITORING;
            } else if (total_a > FALL_IMPACT_G) {
                // Stage 2: Impact spike detected
                _data.fall_state = FallState::IMPACT_DETECTED;
                _impact_timestamp_ms = now;
                _rest_variance_accumulator = 0.0f;
                _sample_count = 0;
            }
            break;

        case FallState::IMPACT_DETECTED:
            // Transition immediately into post-impact stillness confirmation
            _data.fall_state = FallState::WAITING_CONFIRMATION;
            _rest_variance_accumulator = 0.0f;
            _sample_count = 0;
            break;

        case FallState::WAITING_CONFIRMATION: {
            uint32_t elapsed = now - _impact_timestamp_ms;
            
            // Track post-impact motion variance
            float deviation = fabsf(total_a - 1.0f);
            _rest_variance_accumulator += deviation;
            _sample_count++;

            // If user immediately picks up stick and walks, deviation spikes -> False positive
            if (_sample_count > 20 && (_rest_variance_accumulator / _sample_count) > 0.8f) {
                _data.fall_state = FallState::FALSE_POSITIVE_RECOVERED;
                _data.fall_confidence = 0.1f;
                break;
            }

            // After confirmation window elapsed
            if (elapsed >= FALL_CONFIRM_WINDOW_MS) {
                float avg_variance = (_sample_count > 0) ? (_rest_variance_accumulator / _sample_count) : 1.0f;
                float delta_pitch = fabsf(pitch - _pre_impact_pitch);
                float delta_roll  = fabsf(roll - _pre_impact_roll);
                float total_tilt  = sqrtf(delta_pitch * delta_pitch + delta_roll * delta_roll);

                // Stage 3 & 4 Validation:
                // Must have tilted significantly AND stick must be resting/lying down
                if (total_tilt >= FALL_TILT_DEGREES && avg_variance <= FALL_REST_VARIANCE_G) {
                    _data.fall_state = FallState::FALL_CONFIRMED;
                    _data.fall_detected_flag = true;
                    _data.fall_confidence = 0.92f;
                } else if (total_tilt >= FALL_TILT_DEGREES) {
                    // Significant tilt but motion present -> Candidate event with moderate confidence
                    _data.fall_state = FallState::FALL_CONFIRMED;
                    _data.fall_detected_flag = true;
                    _data.fall_confidence = 0.65f;
                } else {
                    // Upright or minor bump -> False positive
                    _data.fall_state = FallState::FALSE_POSITIVE_RECOVERED;
                    _data.fall_confidence = 0.20f;
                }
            }
            break;
        }

        case FallState::FALL_CONFIRMED:
            // Latched until cleared by user or SOS handler
            break;

        case FallState::FALSE_POSITIVE_RECOVERED:
            // Auto reset after 1 second
            if (now - _impact_timestamp_ms > (FALL_CONFIRM_WINDOW_MS + 1000)) {
                _data.fall_state = FallState::MONITORING;
                _data.fall_detected_flag = false;
            }
            break;
    }
}

void MPU6050FallDetector::resetFallState() {
    _data.fall_state = FallState::MONITORING;
    _data.fall_detected_flag = false;
    _data.fall_confidence = 0.0f;
}
