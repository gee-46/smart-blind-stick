/**
 * @file wifi_manager.cpp
 * @brief Implementation of Resilient Wi-Fi Connection Manager
 */

#include "wifi_manager.h"

StickWiFiManager::StickWiFiManager(const char* ssid, const char* password)
    : _ssid(ssid), _password(password), _last_attempt_ms(0),
      _reconnect_interval_ms(5000), _was_connected(false) {}

void StickWiFiManager::begin() {
    WiFi.mode(WIFI_STA);
    WiFi.setAutoReconnect(false); // We control reconnection with exponential backoff
    attemptConnect();
}

void StickWiFiManager::attemptConnect() {
    Serial.printf("[WIFI] Connecting to SSID: %s ...\n", _ssid);
    WiFi.begin(_ssid, _password);
    _last_attempt_ms = millis();
}

bool StickWiFiManager::isConnected() const {
    return WiFi.status() == WL_CONNECTED;
}

int32_t StickWiFiManager::getRSSI() const {
    return isConnected() ? WiFi.RSSI() : -100;
}

String StickWiFiManager::getIPAddress() const {
    return isConnected() ? WiFi.localIP().toString() : "0.0.0.0";
}

void StickWiFiManager::update() {
    bool current_connected = isConnected();

    if (current_connected) {
        if (!_was_connected) {
            Serial.printf("[WIFI] Connected successfully! IP: %s, RSSI: %d dBm\n",
                          getIPAddress().c_str(), getRSSI());
            _was_connected = true;
            _reconnect_interval_ms = 5000; // Reset backoff
        }
    } else {
        if (_was_connected) {
            Serial.println("[WIFI] Connection lost. Entering reconnection loop...");
            _was_connected = false;
        }

        uint32_t now = millis();
        if (now - _last_attempt_ms >= _reconnect_interval_ms) {
            attemptConnect();

            // Exponential backoff up to 60 seconds
            _reconnect_interval_ms = min((uint32_t)60000, _reconnect_interval_ms * 2);
        }
    }
}
