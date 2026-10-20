/**
 * @file sos_button.h
 * @brief Debounced Hardware Pushbutton & SOS Event Trigger
 */

#ifndef SOS_BUTTON_H
#define SOS_BUTTON_H

#include <Arduino.h>
#include "pinout.h"
#include "config.h"

class SOSButtonHandler {
public:
    SOSButtonHandler(uint8_t pin = PIN_SOS_BUTTON);

    void begin();
    bool update();

    bool isEmergencyActive() const { return _emergency_active; }
    void clearEmergency() { _emergency_active = false; }
    uint32_t getEmergencyTimestamp() const { return _trigger_timestamp_ms; }

private:
    uint8_t _pin;
    int _last_raw_state;
    int _stable_state;
    uint32_t _last_debounce_ms;
    uint32_t _press_start_ms;
    bool _is_pressed;
    bool _long_press_fired;
    bool _emergency_active;
    uint32_t _trigger_timestamp_ms;
};

#endif // SOS_BUTTON_H
