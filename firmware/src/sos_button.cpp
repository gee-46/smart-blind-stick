/**
 * @file sos_button.cpp
 * @brief Implementation of Hardware SOS Debounce and Long-Press Detection
 */

#include "sos_button.h"

SOSButtonHandler::SOSButtonHandler(uint8_t pin)
    : _pin(pin), _last_raw_state(HIGH), _stable_state(HIGH),
      _last_debounce_ms(0), _press_start_ms(0), _is_pressed(false),
      _long_press_fired(false), _emergency_active(false), _trigger_timestamp_ms(0) {}

void SOSButtonHandler::begin() {
    pinMode(_pin, INPUT_PULLUP);
    _last_raw_state = digitalRead(_pin);
    _stable_state = _last_raw_state;
}

bool SOSButtonHandler::update() {
    int raw_in = digitalRead(_pin);
    uint32_t now = millis();
    bool newly_triggered = false;

    // Check for raw state change
    if (raw_in != _last_raw_state) {
        _last_debounce_ms = now;
        _last_raw_state = raw_in;
    }

    // Debounce timer elapsed
    if (now - _last_debounce_ms > SOS_DEBOUNCE_MS) {
        if (raw_in != _stable_state) {
            _stable_state = raw_in;

            if (_stable_state == LOW) {
                // Button just pressed down
                _is_pressed = true;
                _press_start_ms = now;
                _long_press_fired = false;
            } else {
                // Button released
                _is_pressed = false;
            }
        }
    }

    // Check for sustained long press (1.2 seconds) to eliminate accidental clicks
    if (_is_pressed && !_long_press_fired) {
        if (now - _press_start_ms >= SOS_LONG_PRESS_MS) {
            _long_press_fired = true;
            _emergency_active = true;
            _trigger_timestamp_ms = now;
            newly_triggered = true;
        }
    }

    return newly_triggered;
}
