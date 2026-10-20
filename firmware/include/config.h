/**
 * @file config.h
 * @brief System Configuration & Calibration Parameters for DrishtiGuard Smart Stick
 */

#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

// ==============================================================================
// FIRMWARE METADATA
// ==============================================================================
#define FIRMWARE_NAME       "DrishtiGuard-Stick"
#define FIRMWARE_VERSION    "1.0.0-hw"
#define HARDWARE_REVISION   "ESP32-DEVKIT-V1-REV1"

// ==============================================================================
// DEVICE IDENTITY & BACKEND ENDPOINTS
// ==============================================================================
#define DEFAULT_DEVICE_ID   "STICK_001"
#define DEFAULT_WIFI_SSID   "YOUR_WIFI_SSID"
#define DEFAULT_WIFI_PASS   "YOUR_WIFI_PASSWORD"

// Production / Local Backend Server Base URL (e.g., http://192.168.1.100:8000)
#define BACKEND_BASE_URL    "http://192.168.1.100:8000"
#define ENDPOINT_CHECKIN    "/api/device/data"
#define ENDPOINT_REGISTER   "/api/device/register"
#define ENDPOINT_EVENTS     "/api/events"
#define ENDPOINT_SOS        "/api/sos"
#define ENDPOINT_STATUS     "/api/device/status/"

// ==============================================================================
// TIMING INTERVALS (Milliseconds)
// ==============================================================================
#define INTERVAL_LIDAR_MS       50    // 20Hz LiDAR distance sampling
#define INTERVAL_IMU_MS         20    // 50Hz IMU sampling for fall detection
#define INTERVAL_TELEMETRY_MS   3000  // 3s regular periodic check-in
#define INTERVAL_HEARTBEAT_MS   10000 // 10s liveness heartbeat
#define INTERVAL_BATTERY_MS     15000 // 15s battery voltage sampling
#define SOS_DEBOUNCE_MS         50    // Pushbutton debounce duration
#define SOS_LONG_PRESS_MS       1200  // Emergency trigger confirmation hold time

// ==============================================================================
// TF-LUNA LIDAR DISTANCE THRESHOLDS (Centimeters)
// ==============================================================================
#define DISTANCE_CRITICAL_CM    50    // Imminent hazard (< 0.5m)
#define DISTANCE_WARNING_CM     120   // Medium proximity alert (< 1.2m)
#define DISTANCE_NOTICE_CM      200   // Far notice (< 2.0m)
#define DISTANCE_HYSTERESIS_CM  10    // 10cm hysteresis band to prevent alert flapping
#define DISTANCE_MIN_VALID_CM   20    // Below 20cm is blind zone for TF-Luna
#define DISTANCE_MAX_VALID_CM   800   // 8 meters maximum rated range

// ==============================================================================
// MPU6050 MOTION & FALL DETECTION TUNING
// ==============================================================================
#define FALL_FREEFALL_G         0.55f // Acceleration drop below this triggers freefall candidate
#define FALL_IMPACT_G           2.60f // Acceleration spike exceeding this flags potential impact
#define FALL_TILT_DEGREES       45.0f // Angular orientation shift post-impact
#define FALL_REST_VARIANCE_G    0.20f // Post-impact stillness indicator
#define FALL_CONFIRM_WINDOW_MS  2500  // Required quiet period following impact to confirm fall

// ==============================================================================
// BATTERY SENSING & VOLTAGE DIVIDER CALIBRATION
// ==============================================================================
// Divider circuit: Vbat -> [R1: 100k] -> ADC_PIN -> [R2: 100k] -> GND
// V_adc = Vbat * (R2 / (R1 + R2)) = Vbat * 0.5
// Vbat = V_adc * (R1 + R2) / R2 = V_adc * 2.0
#define BATTERY_DIVIDER_RATIO   2.00f
#define BATTERY_ADC_VREF        3.30f // ESP32 ADC reference voltage
#define BATTERY_ADC_RESOLUTION  4095.0f
#define BATTERY_MIN_VOLTAGE     3.20f // Li-ion cutoff voltage (0%)
#define BATTERY_MAX_VOLTAGE     4.20f // Li-ion full charge voltage (100%)

// ==============================================================================
// DFPLAYER TRACK ALLOCATION (MP3 Files on MicroSD)
// ==============================================================================
#define AUDIO_TRACK_OBSTACLE_CLOSE  1 // "Warning: Obstacle within half meter"
#define AUDIO_TRACK_OBSTACLE_AHEAD  2 // "Obstacle detected ahead"
#define AUDIO_TRACK_FALL_ALERT      3 // "Fall detected. Alerting guardians."
#define AUDIO_TRACK_SOS_TRIGGERED   4 // "Emergency SOS activated."
#define AUDIO_TRACK_GPS_FIX         5 // "GPS signal connected."
#define AUDIO_TRACK_BATTERY_LOW     6 // "Battery level low. Please recharge."
#define AUDIO_TRACK_SYSTEM_READY    7 // "DrishtiGuard online. Ready for navigation."

#endif // CONFIG_H
