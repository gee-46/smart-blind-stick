/**
 * @file dfplayer_audio.cpp
 * @brief Implementation of Non-Blocking DFPlayer Mini Audio Manager
 */

#include "dfplayer_audio.h"

// Standard DFPlayer Mini UART Protocol
// Start Byte: 0x7E, Version: 0xFF, Length: 0x06, Command, Feedback, Param_H, Param_L, Checksum_H, Checksum_L, End Byte: 0xEF
#define DFPLAYER_START_BYTE 0x7E
#define DFPLAYER_END_BYTE   0xEF
#define CMD_PLAY_TRACK      0x03
#define CMD_SET_VOLUME      0x06
#define CMD_STOP            0x16

DFPlayerController::DFPlayerController(HardwareSerial& serial_port)
    : _serial(serial_port), _is_healthy(false), _track_start_ms(0),
      _estimated_duration_ms(0), _current_priority(AudioPriority::LOW), _is_busy(false) {}

bool DFPlayerController::begin() {
    pinMode(PIN_DFPLAYER_BUSY, INPUT);
    _serial.begin(DFPLAYER_BAUDRATE, SERIAL_8N1, PIN_DFPLAYER_RX, PIN_DFPLAYER_TX);
    delay(100);

    // Set default comfortable volume (0-30): set to 24
    sendCommand(CMD_SET_VOLUME, 24);
    delay(50);

    _is_healthy = true;
    return true;
}

void DFPlayerController::sendCommand(uint8_t cmd, uint16_t param) {
    uint8_t packet[10];
    packet[0] = DFPLAYER_START_BYTE;
    packet[1] = 0xFF; // Version
    packet[2] = 0x06; // Length
    packet[3] = cmd;
    packet[4] = 0x00; // No ACK requested
    packet[5] = (uint8_t)(param >> 8);
    packet[6] = (uint8_t)(param & 0xFF);

    // 16-bit Checksum = 0 - (sum of bytes 1 to 6)
    uint16_t checksum = 0 - (packet[1] + packet[2] + packet[3] + packet[4] + packet[5] + packet[6]);
    packet[7] = (uint8_t)(checksum >> 8);
    packet[8] = (uint8_t)(checksum & 0xFF);
    packet[9] = DFPLAYER_END_BYTE;

    _serial.write(packet, 10);
}

void DFPlayerController::playTrack(uint16_t track, AudioPriority priority) {
    // If currently playing something of higher priority, do not interrupt
    if (isPlaying() && priority < _current_priority) {
        return;
    }

    sendCommand(CMD_PLAY_TRACK, track);
    _track_start_ms = millis();
    _current_priority = priority;
    _estimated_duration_ms = 2500; // Default 2.5s safe window per voice prompt
    _is_busy = true;
}

void DFPlayerController::stop() {
    sendCommand(CMD_STOP, 0);
    _is_busy = false;
}

bool DFPlayerController::isPlaying() const {
    if (!_is_busy) return false;

    // Check BUSY pin (DFPlayer drives it LOW while audio is playing)
    if (digitalRead(PIN_DFPLAYER_BUSY) == LOW) {
        return true;
    }

    // Fallback: check software elapsed timer
    if (millis() - _track_start_ms < _estimated_duration_ms) {
        return true;
    }

    return false;
}

void DFPlayerController::update() {
    if (_is_busy) {
        if (!isPlaying()) {
            _is_busy = false;
            _current_priority = AudioPriority::LOW;
        }
    }
}
