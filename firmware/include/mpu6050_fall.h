/**
 * @file mpu6050_fall.h
 * @brief MPU6050 6-Axis Motion Sensing & Fall Detection Pipeline
 */

#ifndef MPU6050_FALL_H
#define MPU6050_FALL_H

#include <Arduino.h>
#include <Wire.h>
#include "pinout.h"
#include "config.h"

enum class FallState {
    MONITORING = 0,
    FREEFALL_CANDIDATE = 1,
    IMPACT_DETECTED = 2,
    WAITING_CONFIRMATION = 3,
    FALL_CONFIRMED = 4,
    FALSE_POSITIVE_RECOVERED = 5
};

struct MotionData {
    float accel_x_g;
    float accel_y_g;
    float accel_z_g;
    float total_accel_g;
    float gyro_x_dps;
    float gyro_y_dps;
    float gyro_z_dps;
    float total_gyro_dps;
    float pitch_deg;
    float roll_deg;
    bool is_sensor_healthy;
    FallState fall_state;
    float fall_confidence;
    bool fall_detected_flag;
};

class MPU6050FallDetector {
public:
    MPU6050FallDetector(uint8_t i2c_addr = MPU6050_I2C_ADDR);

    bool begin();
    bool update();
    void resetFallState();

    const MotionData& getData() const { return _data; }
    bool isFallConfirmed() const { return _data.fall_state == FallState::FALL_CONFIRMED; }
    bool isHealthy() const { return _data.is_sensor_healthy; }
    float getAccelMagnitude() const { return _data.total_accel_g; }

private:
    uint8_t _address;
    MotionData _data;
    uint32_t _freefall_timestamp_ms;
    uint32_t _impact_timestamp_ms;
    float _pre_impact_pitch;
    float _pre_impact_roll;
    
    // Low-pass filter smoothing
    float _smooth_accel_g;
    float _rest_variance_accumulator;
    uint16_t _sample_count;

    bool readRawSensors(int16_t& ax, int16_t& ay, int16_t& az, int16_t& gx, int16_t& gy, int16_t& gz);
    void evaluateFallPipeline(float total_a, float total_g, float pitch, float roll);
};

#endif // MPU6050_FALL_H
