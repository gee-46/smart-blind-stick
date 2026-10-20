/**
 * @file battery.h
 * @brief Battery Voltage Sensing & Calibration Interface
 */

#ifndef BATTERY_H
#define BATTERY_H

#include <Arduino.h>
#include "pinout.h"
#include "config.h"

struct BatteryStatus {
    float voltage;
    float percentage;
    bool is_available;
    bool is_low;
};

class BatteryMonitor {
public:
    BatteryMonitor(uint8_t adc_pin = PIN_BATTERY_ADC);

    void begin();
    void update();

    const BatteryStatus& getStatus() const { return _status; }
    float getVoltage() const { return _status.voltage; }
    float getPercentage() const { return _status.percentage; }
    bool isAvailable() const { return _status.is_available; }
    bool isLow() const { return _status.is_low; }

private:
    uint8_t _adc_pin;
    BatteryStatus _status;

    float readFilteredVoltage();
    float calculatePercentage(float voltage);
};

#endif // BATTERY_H
