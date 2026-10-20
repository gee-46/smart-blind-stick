/**
 * @file haptics.cpp
 * @brief Implementation of Non-Blocking Alert Patterns
 */

#include "haptics.h"

HapticController::HapticController(uint8_t vibro_pin, uint8_t buzzer_pin)
    : _vibro_pin(vibro_pin), _buzzer_pin(buzzer_pin),
      _current_pattern(AlertPattern::OFF), _step_start_ms(0),
      _step_index(0), _vibro_state(false), _buzzer_state(false) {}

void HapticController::begin() {
    pinMode(_vibro_pin, OUTPUT);
    pinMode(_buzzer_pin, OUTPUT);
    setOutputs(false, false);
}

void HapticController::setOutputs(bool vibro, bool buzzer) {
    _vibro_state = vibro;
    _buzzer_state = buzzer;
    digitalWrite(_vibro_pin, vibro ? HIGH : LOW);
    digitalWrite(_buzzer_pin, buzzer ? HIGH : LOW);
}

void HapticController::triggerPattern(AlertPattern pattern) {
    // Priority preemption: SOS and FALL override ordinary obstacle notices
    if (_current_pattern == AlertPattern::SOS_EMERGENCY && pattern != AlertPattern::SOS_EMERGENCY && pattern != AlertPattern::OFF) {
        return; // Don't interrupt SOS
    }
    if (_current_pattern == AlertPattern::FALL_ALERT && (pattern == AlertPattern::OBSTACLE_NOTICE || pattern == AlertPattern::OBSTACLE_WARNING)) {
        return; // Don't interrupt Fall alert
    }

    _current_pattern = pattern;
    _step_start_ms = millis();
    _step_index = 0;
}

void HapticController::stop() {
    _current_pattern = AlertPattern::OFF;
    setOutputs(false, false);
}

void HapticController::update() {
    if (_current_pattern == AlertPattern::OFF) {
        setOutputs(false, false);
        return;
    }

    uint32_t elapsed = millis() - _step_start_ms;

    switch (_current_pattern) {
        case AlertPattern::SYSTEM_CHIRP:
            // Single short beep (150ms)
            if (elapsed < 150) {
                setOutputs(false, true);
            } else {
                stop();
            }
            break;

        case AlertPattern::OBSTACLE_NOTICE:
            // Single subtle buzz (100ms)
            if (elapsed < 100) {
                setOutputs(true, false);
            } else {
                stop();
            }
            break;

        case AlertPattern::OBSTACLE_WARNING:
            // Pulse: 150ms ON, 150ms OFF, repeating
            if ((elapsed % 300) < 150) {
                setOutputs(true, false);
            } else {
                setOutputs(false, false);
            }
            break;

        case AlertPattern::OBSTACLE_CRITICAL:
            // Rapid urgent pulse: 80ms ON, 60ms OFF (both vibro + buzzer)
            if ((elapsed % 140) < 80) {
                setOutputs(true, true);
            } else {
                setOutputs(false, false);
            }
            break;

        case AlertPattern::FALL_ALERT:
            // Alternating 250ms ON, 250ms OFF
            if ((elapsed % 500) < 250) {
                setOutputs(true, true);
            } else {
                setOutputs(false, false);
            }
            break;

        case AlertPattern::SOS_EMERGENCY:
            // Continuous SOS Morse code pattern:
            // 3 dots (100ms on, 100ms off) -> 3 dashes (300ms on, 100ms off) -> 3 dots -> 600ms gap
            {
                uint32_t cycle = elapsed % 3000;
                bool active = false;
                if (cycle < 600) {
                    // S: 3 short pulses
                    active = ((cycle % 200) < 100);
                } else if (cycle >= 700 && cycle < 1900) {
                    // O: 3 long pulses (300ms on, 100ms off)
                    uint32_t sub = cycle - 700;
                    active = ((sub % 400) < 300);
                } else if (cycle >= 2000 && cycle < 2600) {
                    // S: 3 short pulses
                    uint32_t sub = cycle - 2000;
                    active = ((sub % 200) < 100);
                }
                setOutputs(active, active);
            }
            break;

        default:
            stop();
            break;
    }
}
