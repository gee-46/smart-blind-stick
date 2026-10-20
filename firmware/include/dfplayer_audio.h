/**
 * @file dfplayer_audio.h
 * @brief DFPlayer Mini Voice Prompt & Audio Feedback Controller
 */

#ifndef DFPLAYER_AUDIO_H
#define DFPLAYER_AUDIO_H

#include <Arduino.h>
#include <HardwareSerial.h>
#include "pinout.h"
#include "config.h"

enum class AudioPriority {
    LOW = 0,      // System ready, battery notices
    MEDIUM = 1,   // Obstacle warnings
    HIGH = 2,     // Fall candidate alerts
    EMERGENCY = 3 // Physical SOS
};

struct AudioRequest {
    uint16_t track_number;
    AudioPriority priority;
};

class DFPlayerController {
public:
    DFPlayerController(HardwareSerial& serial_port = Serial);

    bool begin();
    void update();

    void playTrack(uint16_t track, AudioPriority priority = AudioPriority::MEDIUM);
    void stop();
    bool isPlaying() const;
    bool isHealthy() const { return _is_healthy; }

private:
    HardwareSerial& _serial;
    bool _is_healthy;
    uint32_t _track_start_ms;
    uint32_t _estimated_duration_ms;
    AudioPriority _current_priority;
    bool _is_busy;

    void sendCommand(uint8_t cmd, uint16_t param);
};

#endif // DFPLAYER_AUDIO_H
