/**
 * @file wifi_manager.h
 * @brief Resilient Non-Blocking Wi-Fi Manager for DrishtiGuard Stick
 */

#ifndef WIFI_MANAGER_H
#define WIFI_MANAGER_H

#include <Arduino.h>
#include <WiFi.h>
#include "config.h"

class StickWiFiManager {
public:
    StickWiFiManager(const char* ssid = DEFAULT_WIFI_SSID, const char* password = DEFAULT_WIFI_PASS);

    void begin();
    void update();

    bool isConnected() const;
    int32_t getRSSI() const;
    String getIPAddress() const;

private:
    const char* _ssid;
    const char* _password;
    uint32_t _last_attempt_ms;
    uint32_t _reconnect_interval_ms;
    bool _was_connected;

    void attemptConnect();
};

#endif // WIFI_MANAGER_H
