/**
 * @file main.cpp
 * @brief DrishtiGuard Smart Blind Stick — Main Firmware Application
 *
 * Microcontroller: ESP32 DevKit V1
 * Framework: Arduino / PlatformIO
 */

#include <Arduino.h>
#include <esp_task_wdt.h>

#include "pinout.h"
#include "config.h"
#include "tf_luna.h"
#include "gps_reader.h"
#include "mpu6050_fall.h"
#include "haptics.h"
#include "dfplayer_audio.h"
#include "sos_button.h"
#include "battery.h"
#include "wifi_manager.h"
#include "backend_client.h"

// Hardware instances
TFLunaSensor lidar(Serial2);
GPSReader gps(Serial1);
MPU6050FallDetector imu(MPU6050_I2C_ADDR);
HapticController haptics(PIN_VIBRATION_MOTOR, PIN_ACTIVE_BUZZER);
DFPlayerController audio(Serial);
SOSButtonHandler sosBtn(PIN_SOS_BUTTON);
BatteryMonitor battery(PIN_BATTERY_ADC);
StickWiFiManager wifi(DEFAULT_WIFI_SSID, DEFAULT_WIFI_PASS);
BackendClient backend(BACKEND_BASE_URL, DEFAULT_DEVICE_ID);

// Loop timing trackers
uint32_t lastLidarTime = 0;
uint32_t lastImuTime = 0;
uint32_t lastTelemetryTime = 0;
uint32_t lastBatteryTime = 0;
ObstacleLevel lastObstacleAlert = ObstacleLevel::NONE;

void setup() {
    Serial.begin(115200);
    delay(500);

    Serial.println("\n========================================================");
    Serial.println("  DRISHTIGUARD SMART BLIND STICK — ESP32 FIRMWARE v1.0 ");
    Serial.println("========================================================");

    // 1. Initialize diagnostic Status LED
    pinMode(PIN_STATUS_LED, OUTPUT);
    digitalWrite(PIN_STATUS_LED, HIGH);

    // 2. Initialize Haptics and Actuators
    haptics.begin();
    haptics.triggerPattern(AlertPattern::SYSTEM_CHIRP);

    // 3. Initialize Physical SOS Button
    sosBtn.begin();

    // 4. Initialize Battery ADC
    battery.begin();

    // 5. Initialize TF-Luna LiDAR (UART2)
    Serial.print("[INIT] Initializing TF-Luna LiDAR... ");
    if (lidar.begin()) {
        Serial.println("OK");
    } else {
        Serial.println("FAILED");
    }

    // 6. Initialize NEO-6M GPS (UART1)
    Serial.print("[INIT] Initializing NEO-6M GPS... ");
    if (gps.begin()) {
        Serial.println("OK");
    } else {
        Serial.println("FAILED");
    }

    // 7. Initialize MPU6050 Motion Sensor (I2C)
    Serial.print("[INIT] Initializing MPU6050 IMU... ");
    if (imu.begin()) {
        Serial.println("OK");
    } else {
        Serial.println("FAILED (Check SDA/SCL pullup resistors)");
    }

    // 8. Initialize DFPlayer Mini Audio
    Serial.print("[INIT] Initializing DFPlayer Mini... ");
    if (audio.begin()) {
        Serial.println("OK");
        audio.playTrack(AUDIO_TRACK_SYSTEM_READY, AudioPriority::LOW);
    } else {
        Serial.println("FAILED");
    }

    // 9. Initialize Wi-Fi & Backend Client
    wifi.begin();
    backend.begin();

    digitalWrite(PIN_STATUS_LED, LOW);
    Serial.println("[INIT] All subsystems initialized. Starting main loop.\n");
}

void loop() {
    uint32_t now = millis();

    // -------------------------------------------------------------------------
    // 1. CRITICAL PRIORITY: Check Physical Hardware SOS Button
    // -------------------------------------------------------------------------
    if (sosBtn.update()) {
        Serial.println("\n[EMERGENCY] Physical SOS Button Activated by User!");

        // Immediate Local Safety Feedback
        haptics.triggerPattern(AlertPattern::SOS_EMERGENCY);
        audio.playTrack(AUDIO_TRACK_SOS_TRIGGERED, AudioPriority::EMERGENCY);

        // Immediate Remote Delivery
        double lat = gps.hasValidFix() ? gps.getLatitude() : 0.0;
        double lng = gps.hasValidFix() ? gps.getLongitude() : 0.0;
        backend.sendSOS(lat, lng, "physical_button_pressed");
    }

    // -------------------------------------------------------------------------
    // 2. HIGH FREQUENCY (50Hz): MPU6050 Motion & Fall Detection
    // -------------------------------------------------------------------------
    if (now - lastImuTime >= INTERVAL_IMU_MS) {
        lastImuTime = now;
        imu.update();

        if (imu.isFallConfirmed()) {
            Serial.println("\n[SAFETY] Validated Fall Detected by IMU Pipeline!");
            
            // Immediate Local Alert
            haptics.triggerPattern(AlertPattern::FALL_ALERT);
            audio.playTrack(AUDIO_TRACK_FALL_ALERT, AudioPriority::HIGH);

            // Transmit Fall Incident to Backend
            double lat = gps.hasValidFix() ? gps.getLatitude() : 0.0;
            double lng = gps.hasValidFix() ? gps.getLongitude() : 0.0;
            
            backend.sendSOS(lat, lng, "fall_detected_confirmed");
            imu.resetFallState();
        }
    }

    // -------------------------------------------------------------------------
    // 3. DISTANCE SENSING (20Hz): TF-Luna LiDAR Obstacle Warnings
    // -------------------------------------------------------------------------
    if (now - lastLidarTime >= INTERVAL_LIDAR_MS) {
        lastLidarTime = now;
        lidar.update();

        ObstacleLevel level = lidar.getAlertLevel();
        if (level != lastObstacleAlert) {
            lastObstacleAlert = level;

            if (level == ObstacleLevel::CRITICAL) {
                // < 50cm: Urgent vibration + buzzer
                haptics.triggerPattern(AlertPattern::OBSTACLE_CRITICAL);
                audio.playTrack(AUDIO_TRACK_OBSTACLE_CLOSE, AudioPriority::MEDIUM);
                Serial.printf("[LIDAR] Critical Obstacle at %d cm!\n", lidar.getDistanceCm());
            } else if (level == ObstacleLevel::WARNING) {
                // < 120cm: Pulsed vibration warning
                haptics.triggerPattern(AlertPattern::OBSTACLE_WARNING);
                audio.playTrack(AUDIO_TRACK_OBSTACLE_AHEAD, AudioPriority::MEDIUM);
                Serial.printf("[LIDAR] Warning: Obstacle at %d cm\n", lidar.getDistanceCm());
            } else if (level == ObstacleLevel::NOTICE) {
                // < 200cm: Gentle notice buzz
                haptics.triggerPattern(AlertPattern::OBSTACLE_NOTICE);
            } else {
                // Obstacle cleared
                if (haptics.getCurrentPattern() == AlertPattern::OBSTACLE_CRITICAL ||
                    haptics.getCurrentPattern() == AlertPattern::OBSTACLE_WARNING ||
                    haptics.getCurrentPattern() == AlertPattern::OBSTACLE_NOTICE) {
                    haptics.stop();
                }
            }
        }
    }

    // -------------------------------------------------------------------------
    // 4. GPS NMEA Stream Ingestion
    // -------------------------------------------------------------------------
    gps.update();

    // -------------------------------------------------------------------------
    // 5. Periodic Battery Measurement (Every 15s)
    // -------------------------------------------------------------------------
    if (now - lastBatteryTime >= INTERVAL_BATTERY_MS) {
        lastBatteryTime = now;
        battery.update();

        if (battery.isAvailable() && battery.isLow()) {
            Serial.printf("[BATTERY] Low Battery Warning: %.2fV (%.1f%%)\n",
                          battery.getVoltage(), battery.getPercentage());
            audio.playTrack(AUDIO_TRACK_BATTERY_LOW, AudioPriority::LOW);
        }
    }

    // -------------------------------------------------------------------------
    // 6. Network & Periodic Telemetry Check-in (Every 3s)
    // -------------------------------------------------------------------------
    wifi.update();

    if (now - lastTelemetryTime >= INTERVAL_TELEMETRY_MS) {
        lastTelemetryTime = now;

        if (wifi.isConnected()) {
            // Heartbeat blink on status LED
            digitalWrite(PIN_STATUS_LED, HIGH);

            // Flush offline queued alerts first
            backend.flushQueuedEvents();

            // Send full genuine telemetry packet
            backend.sendTelemetry(gps.getData(), lidar.getData(), imu.getData(), battery.getStatus());

            digitalWrite(PIN_STATUS_LED, LOW);
        }
    }

    // -------------------------------------------------------------------------
    // 7. Non-Blocking Subsystem Updates (Haptics timers, Audio states)
    // -------------------------------------------------------------------------
    haptics.update();
    audio.update();
}
