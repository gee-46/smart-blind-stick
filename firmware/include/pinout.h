/**
 * @file pinout.h
 * @brief Verified Hardware Pin Mapping and Electrical Constraints for DrishtiGuard Smart Stick
 *
 * Microcontroller: ESP32 DevKit V1 (30-pin / 38-pin module)
 * Operating Voltage: 3.3V Logic.
 *
 * SAFETY WARNINGS:
 * 1. Do NOT power vibration motors or buzzers directly from ESP32 GPIOs.
 *    Use N-channel MOSFETs (e.g., AO3400, 2N7000) with flyback diodes.
 * 2. TF-Luna requires 5.0V regulated power (current up to ~100mA during pulses).
 *    Its UART TX/RX lines are 3.3V TTL compatible.
 * 3. NEO-6M GPS operates on 3.3V/5V VCC with 3.3V logic level.
 * 4. MPU6050 requires 3.3V logic on I2C (GPIO 21 SDA, GPIO 22 SCL) with 4.7k pullups.
 * 5. DFPlayer Mini TX/RX requires a 1k series resistor on ESP32 TX -> DFPlayer RX
 *    to suppress digital noise and level mismatch.
 * 6. Battery ADC (GPIO 34) is an INPUT-ONLY pin. Never connect raw Li-ion voltage
 *    (up to 4.2V / 8.4V) directly; always use a calibrated resistor divider.
 */

#ifndef PINOUT_H
#define PINOUT_H

#include <Arduino.h>

// ==============================================================================
// I2C BUS (MPU6050 Accelerometer/Gyroscope & Optional VL53L1X ToF)
// ==============================================================================
#define PIN_I2C_SDA         21  // ESP32 Hardware I2C SDA
#define PIN_I2C_SCL         22  // ESP32 Hardware I2C SCL
#define MPU6050_I2C_ADDR    0x68
#define VL53L1X_I2C_ADDR    0x29
#define PIN_VL53L1X_XSHUT   32  // Optional ToF Shutdown control pin

// ==============================================================================
// TF-LUNA LIDAR (Hardware Serial 2)
// ==============================================================================
#define PIN_TFLUNA_RX       16  // ESP32 RX2 <- TF-Luna TX (3.3V TTL)
#define PIN_TFLUNA_TX       17  // ESP32 TX2 -> TF-Luna RX (3.3V TTL)
#define TFLUNA_BAUDRATE     115200

// ==============================================================================
// NEO-6M GPS RECEIVER (Hardware Serial 1)
// ==============================================================================
#define PIN_GPS_RX          26  // ESP32 RX1 <- NEO-6M TX
#define PIN_GPS_TX          27  // ESP32 TX1 -> NEO-6M RX
#define GPS_BAUDRATE        9600

// ==============================================================================
// DFPLAYER MINI VOICE MODULE (SoftwareSerial or Hardware Serial)
// ==============================================================================
#define PIN_DFPLAYER_TX     25  // ESP32 TX -> 1k Resistor -> DFPlayer RX
#define PIN_DFPLAYER_RX     33  // ESP32 RX <- DFPlayer TX
#define PIN_DFPLAYER_BUSY   35  // Input only: DFPlayer BUSY line (LOW when playing)
#define DFPLAYER_BAUDRATE   9600

// ==============================================================================
// PHYSICAL INPUTS & SENSING
// ==============================================================================
#define PIN_SOS_BUTTON      4   // Active-LOW pushbutton with internal pullup
#define PIN_BATTERY_ADC     34  // ADC1_CH6: Input-only pin connected to voltage divider

// ==============================================================================
// LOCAL ACTUATORS (Haptics & Audio)
// ==============================================================================
#define PIN_VIBRATION_MOTOR 23  // PWM-capable GPIO driving N-channel MOSFET gate
#define PIN_ACTIVE_BUZZER   19  // GPIO driving Buzzer transistor/MOSFET
#define PIN_STATUS_LED      18  // Diagnostic status LED (Active HIGH)

#endif // PINOUT_H
