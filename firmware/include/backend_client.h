/**
 * @file backend_client.h
 * @brief Authenticated FastAPI Backend Client & Telemetry Serializer
 */

#ifndef BACKEND_CLIENT_H
#define BACKEND_CLIENT_H

#include <Arduino.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "config.h"
#include "gps_reader.h"
#include "tf_luna.h"
#include "mpu6050_fall.h"
#include "battery.h"

struct QueuedEvent {
    char event_type[32];
    char source[32];
    char risk_level[16];
    char message[128];
    double latitude;
    double longitude;
    uint32_t timestamp_ms;
    bool is_sos;
};

class BackendClient {
public:
    BackendClient(const char* base_url = BACKEND_BASE_URL, const char* device_id = DEFAULT_DEVICE_ID);

    void begin();
    
    // Core telemetry
    bool sendTelemetry(const GPSData& gps, const TFLunaData& lidar, const MotionData& motion, const BatteryStatus& battery);
    bool sendSOS(double latitude, double longitude, const char* reason = "manual_sos");
    bool sendEvent(const char* source, const char* event_type, const char* risk_level, const char* message, const JsonDocument* extra = nullptr);
    
    // Offline queue handling
    void queueEvent(const char* source, const char* event_type, const char* risk_level, const char* message, double lat, double lng, bool is_sos = false);
    void flushQueuedEvents();

    bool isRegistered() const { return _is_registered; }
    const String& getApiKey() const { return _api_key; }
    void setApiKey(const String& key) { _api_key = key; _is_registered = true; }

private:
    String _base_url;
    String _device_id;
    String _api_key;
    bool _is_registered;
    uint32_t _sequence_number;

    // Bounded queue for offline buffering (max 10 incidents)
    static const uint8_t QUEUE_CAPACITY = 10;
    QueuedEvent _event_queue[QUEUE_CAPACITY];
    uint8_t _queue_count;
    uint8_t _queue_head;

    bool postJson(const String& endpoint, const JsonDocument& doc, String* response_out = nullptr);
};

#endif // BACKEND_CLIENT_H
