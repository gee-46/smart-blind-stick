/**
 * @file battery.cpp
 * @brief Implementation of Battery ADC Calibration & Percentage Estimation
 */

#include "battery.h"

BatteryMonitor::BatteryMonitor(uint8_t adc_pin)
    : _adc_pin(adc_pin) {
    _status.voltage = 0.0f;
    _status.percentage = -1.0f;
    _status.is_available = false;
    _status.is_low = false;
}

void BatteryMonitor::begin() {
    pinMode(_adc_pin, INPUT);
    analogReadResolution(12); // 12-bit ADC (0 - 4095)
    analogSetAttenuation(ADC_11db); // Full-scale voltage approx 2.6V - 3.1V
    update();
}

float BatteryMonitor::readFilteredVoltage() {
    uint32_t adc_accum = 0;
    const uint8_t SAMPLES = 16;

    for (uint8_t i = 0; i < SAMPLES; i++) {
        adc_accum += analogRead(_adc_pin);
        delayMicroseconds(50);
    }

    float raw_avg = (float)adc_accum / (float)SAMPLES;

    // Convert raw ADC to pin voltage:
    // With 11dB attenuation, max voltage is ~3.14V
    float pin_voltage = (raw_avg / BATTERY_ADC_RESOLUTION) * BATTERY_ADC_VREF;

    // Multiply by voltage divider ratio (R1 + R2) / R2
    float battery_voltage = pin_voltage * BATTERY_DIVIDER_RATIO;
    return battery_voltage;
}

float BatteryMonitor::calculatePercentage(float v) {
    // Standard Li-ion 1S discharge curve approximation
    if (v >= BATTERY_MAX_VOLTAGE) return 100.0f;
    if (v <= BATTERY_MIN_VOLTAGE) return 0.0f;

    // Linear piecewise interpolation
    // 4.2V -> 100%
    // 3.8V -> 55%
    // 3.6V -> 20%
    // 3.2V -> 0%
    if (v >= 3.8f) {
        return 55.0f + (v - 3.8f) * (45.0f / (4.2f - 3.8f));
    } else if (v >= 3.6f) {
        return 20.0f + (v - 3.6f) * (35.0f / (3.8f - 3.6f));
    } else {
        return (v - 3.2f) * (20.0f / (3.6f - 3.2f));
    }
}

void BatteryMonitor::update() {
    float v = readFilteredVoltage();

    // Plausibility check:
    // If voltage is less than 1.5V, the sensing circuit is disconnected/unpopulated.
    // In that case, we mark battery sensing as UNAVAILABLE rather than faking 0% or 100%.
    if (v < 1.5f || v > 5.0f) {
        _status.voltage = 0.0f;
        _status.percentage = -1.0f;
        _status.is_available = false;
        _status.is_low = false;
        return;
    }

    _status.voltage = v;
    _status.percentage = calculatePercentage(v);
    _status.is_available = true;
    _status.is_low = (_status.percentage <= 15.0f);
}
