/**
 * @file backend_client.cpp
 * @brief Implementation of FastAPI Client and Offline Queue Handling
 */

#include "backend_client.h"

BackendClient::BackendClient(const char* base_url, const char* device_id)
    : _base_url(base_url), _device_id(device_id), _api_key(""),
      _is_registered(false), _sequence_number(0), _queue_count(0), _queue_head(0) {}

void BackendClient::begin() {
    // Clean trailing slashes
    if (_base_url.endsWith("/")) {
        _base_url = _base_url.substring(0, _base_url.length() - 1);
    }
}

bool BackendClient::postJson(const String& endpoint, const JsonDocument& doc, String* response_out) {
    if (WiFi.status() != WL_CONNECTED) {
        return false;
    }

    HTTPClient http;
    String full_url = _base_url + endpoint;
    http.begin(full_url);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(4000); // 4-second network timeout

    if (_is_registered && _api_key.length() > 0) {
        http.addHeader("X-API-Key", _api_key);
    }

    String json_string;
    serializeJson(doc, json_string);

    int http_code = http.POST(json_string);
    bool success = false;

    if (http_code >= 200 && http_code < 300) {
        success = true;
        if (response_out != nullptr) {
            *response_out = http.getString();
        }
    } else {
        Serial.printf("[HTTP] POST %s failed. Code: %d\n", endpoint.c_str(), http_code);
    }

    http.end();
    return success;
}

bool BackendClient::sendTelemetry(const GPSData& gps, const TFLunaData& lidar, const MotionData& motion, const BatteryStatus& battery) {
    JsonDocument doc;

    doc["device_id"] = _device_id;
    doc["sequence"] = ++_sequence_number;
    doc["firmware_version"] = FIRMWARE_VERSION;

    // Battery (only populated if sensing is genuinely available)
    if (battery.is_available) {
        doc["battery"] = round(battery.percentage * 10.0f) / 10.0f;
    } else {
        doc["battery"] = nullptr;
    }

    // GPS Telemetry (strict validity check)
    if (gps.has_valid_fix) {
        doc["latitude"] = gps.latitude;
        doc["longitude"] = gps.longitude;
        doc["altitude"] = gps.altitude_m;
        doc["speed_kmh"] = gps.speed_kmh;
        doc["satellites"] = gps.satellites;
        doc["fix_quality"] = gps.fix_quality;
        doc["gps_available"] = true;
    } else {
        doc["gps_available"] = false;
        doc["satellites"] = gps.satellites;
    }

    // Overall Status
    if (motion.fall_state == FallState::FALL_CONFIRMED) {
        doc["status"] = "fall_detected";
    } else if (lidar.alert_level == ObstacleLevel::CRITICAL) {
        doc["status"] = "obstacle_critical";
    } else if (lidar.alert_level == ObstacleLevel::WARNING) {
        doc["status"] = "obstacle_warning";
    } else {
        doc["status"] = "safe";
    }

    // Diagnostics & Sensor Health
    JsonObject health = doc["sensor_health"].to<JsonObject>();
    health["lidar"] = lidar.is_sensor_healthy;
    health["gps"] = gps.is_module_alive;
    health["imu"] = motion.is_sensor_healthy;
    health["battery"] = battery.is_available;

    if (lidar.is_valid) {
        doc["lidar_distance_cm"] = lidar.distance_cm;
    }

    return postJson(ENDPOINT_CHECKIN, doc);
}

bool BackendClient::sendSOS(double latitude, double longitude, const char* reason) {
    JsonDocument doc;
    doc["device_id"] = _device_id;
    doc["reason"] = reason;

    if (fabs(latitude) > 0.0001 && fabs(longitude) > 0.0001) {
        doc["latitude"] = latitude;
        doc["longitude"] = longitude;
    }

    bool delivered = postJson(ENDPOINT_SOS, doc);
    if (!delivered) {
        // Queue for immediate retry as soon as connectivity restores
        queueEvent("manual", "sos", "critical", reason, latitude, longitude, true);
    }
    return delivered;
}

bool BackendClient::sendEvent(const char* source, const char* event_type, const char* risk_level, const char* message, const JsonDocument* extra) {
    JsonDocument doc;
    doc["device_id"] = _device_id;
    doc["source"] = source;
    doc["event_type"] = event_type;
    doc["risk_level"] = risk_level;
    doc["message"] = message;

    if (extra != nullptr) {
        doc["extra"] = *extra;
    }

    return postJson(ENDPOINT_EVENTS, doc);
}

void BackendClient::queueEvent(const char* source, const char* event_type, const char* risk_level, const char* message, double lat, double lng, bool is_sos) {
    if (_queue_count >= QUEUE_CAPACITY) {
        // Drop oldest non-SOS event or shift head
        _queue_head = (_queue_head + 1) % QUEUE_CAPACITY;
        _queue_count--;
    }

    uint8_t insert_idx = (_queue_head + _queue_count) % QUEUE_CAPACITY;
    QueuedEvent& ev = _event_queue[insert_idx];

    strncpy(ev.source, source, sizeof(ev.source) - 1);
    strncpy(ev.event_type, event_type, sizeof(ev.event_type) - 1);
    strncpy(ev.risk_level, risk_level, sizeof(ev.risk_level) - 1);
    strncpy(ev.message, message, sizeof(ev.message) - 1);
    ev.latitude = lat;
    ev.longitude = lng;
    ev.timestamp_ms = millis();
    ev.is_sos = is_sos;

    _queue_count++;
    Serial.printf("[QUEUE] Stored offline event: %s. Queue size: %d\n", event_type, _queue_count);
}

void BackendClient::flushQueuedEvents() {
    if (WiFi.status() != WL_CONNECTED || _queue_count == 0) {
        return;
    }

    Serial.printf("[QUEUE] Flushing %d queued events to backend...\n", _queue_count);

    while (_queue_count > 0) {
        QueuedEvent& ev = _event_queue[_queue_head];
        bool sent = false;

        if (ev.is_sos) {
            sent = sendSOS(ev.latitude, ev.longitude, ev.message);
        } else {
            sent = sendEvent(ev.source, ev.event_type, ev.risk_level, ev.message, nullptr);
        }

        if (sent) {
            _queue_head = (_queue_head + 1) % QUEUE_CAPACITY;
            _queue_count--;
        } else {
            // Stop flushing if network fails again
            break;
        }
    }
}
