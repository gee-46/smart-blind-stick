/**
 * @file haptics.h
 * @brief Non-Blocking Local Haptic (Vibration) & Buzzer Alert Controller
 */

#ifndef HAPTICS_H
#define HAPTICS_H

#include <Arduino.h>
#include "pinout.h"
#include "config.h"

enum class AlertPattern {
    OFF = 0,
    SYSTEM_CHIRP = 1,
    OBSTACLE_NOTICE = 2,
    OBSTACLE_WARNING = 3,
    OBSTACLE_CRITICAL = 4,
    FALL_ALERT = 5,
    SOS_EMERGENCY = 6
};

class HapticController {
public:
    HapticController(uint8_t vibro_pin = PIN_VIBRATION_MOTOR, uint8_t buzzer_pin = PIN_ACTIVE_BUZZER);

    void begin();
    void update();

    void triggerPattern(AlertPattern pattern);
    void stop();

    AlertPattern getCurrentPattern() const { return _current_pattern; }

private:
    uint8_t _vibro_pin;
    uint8_t _buzzer_pin;
    AlertPattern _current_pattern;
    uint32_t _step_start_ms;
    uint8_t _step_index;
    bool _vibro_state;
    bool _buzzer_state;

    void setOutputs(bool vibro, bool buzzer);
};

#endif // HAPTICS_H
