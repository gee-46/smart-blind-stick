/**
 * @file main.cpp
 * @brief ESP32-CAM AI Vision Node — Snapshot Capture and Inference Relay
 */

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <esp_camera.h>

#include "cam_pinout.h"
#include "cam_config.h"

uint32_t lastFrameTime = 0;
bool cameraInitialized = false;

bool initCamera() {
    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer   = LEDC_TIMER_0;
    config.pin_d0       = Y2_GPIO_NUM;
    config.pin_d1       = Y3_GPIO_NUM;
    config.pin_d2       = Y4_GPIO_NUM;
    config.pin_d3       = Y5_GPIO_NUM;
    config.pin_d4       = Y6_GPIO_NUM;
    config.pin_d5       = Y7_GPIO_NUM;
    config.pin_d6       = Y8_GPIO_NUM;
    config.pin_d7       = Y9_GPIO_NUM;
    config.pin_xclk     = XCLK_GPIO_NUM;
    config.pin_pclk     = PCLK_GPIO_NUM;
    config.pin_vsync    = VSYNC_GPIO_NUM;
    config.pin_href     = HREF_GPIO_NUM;
    config.pin_sccb_sda = SIOD_GPIO_NUM;
    config.pin_sccb_scl = SIOC_GPIO_NUM;
    config.pin_pwdn     = PWDN_GPIO_NUM;
    config.pin_reset    = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000;
    config.pixel_format = PIXFORMAT_JPEG;

    if (psramFound()) {
        config.frame_size   = CAMERA_FRAME_SIZE;
        config.jpeg_quality = CAMERA_JPEG_QUALITY;
        config.fb_count     = 2;
    } else {
        config.frame_size   = FRAMESIZE_QVGA;
        config.jpeg_quality = 15;
        config.fb_count     = 1;
    }

    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.printf("[CAM] Camera init failed with error 0x%x\n", err);
        return false;
    }

    // Optional sensor adjustments
    sensor_t* s = esp_camera_sensor_get();
    if (s != nullptr) {
        s->set_brightness(s, 1);
        s->set_contrast(s, 1);
    }

    return true;
}

void connectWiFi() {
    Serial.printf("[WIFI] Connecting to %s ...\n", CAM_WIFI_SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(CAM_WIFI_SSID, CAM_WIFI_PASS);

    uint8_t retries = 0;
    while (WiFi.status() != WL_CONNECTED && retries < 20) {
        delay(500);
        Serial.print(".");
        retries++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("\n[WIFI] Connected! IP: %s\n", WiFi.localIP().toString().c_str());
    } else {
        Serial.println("\n[WIFI] Initial connection timed out. Will retry in loop.");
    }
}

bool uploadFrame(camera_fb_t* fb) {
    if (WiFi.status() != WL_CONNECTED || fb == nullptr) {
        return false;
    }

    HTTPClient http;
    String full_url = String(INFERENCE_BASE_URL) + INFERENCE_ENDPOINT;
    http.begin(full_url);
    http.setTimeout(3000);

    // Prepare multipart form-data payload
    String boundary = "----ESP32CamBoundary7MA4YWxkTrZu0gW";
    http.addHeader("Content-Type", "multipart/form-data; boundary=" + boundary);
    http.addHeader("X-Device-ID", ASSOCIATED_DEVICE_ID);

    String bodyHeader = "--" + boundary + "\r\n" +
                        "Content-Disposition: form-data; name=\"file\"; filename=\"frame.jpg\"\r\n" +
                        "Content-Type: image/jpeg\r\n\r\n";
    String bodyFooter = "\r\n--" + boundary + "\r\n" +
                        "Content-Disposition: form-data; name=\"device_id\"\r\n\r\n" +
                        ASSOCIATED_DEVICE_ID + "\r\n--" + boundary + "--\r\n";

    size_t totalLen = bodyHeader.length() + fb->len + bodyFooter.length();

    uint8_t* payload = (uint8_t*)malloc(totalLen);
    if (!payload) {
        Serial.println("[HTTP] Malloc failed for frame upload payload");
        http.end();
        return false;
    }

    memcpy(payload, bodyHeader.c_str(), bodyHeader.length());
    memcpy(payload + bodyHeader.length(), fb->buf, fb->len);
    memcpy(payload + bodyHeader.length() + fb->len, bodyFooter.c_str(), bodyFooter.length());

    int httpResponseCode = http.POST(payload, totalLen);
    free(payload);

    bool success = false;
    if (httpResponseCode >= 200 && httpResponseCode < 300) {
        success = true;
        String response = http.getString();
        Serial.printf("[CAM] Inference Result: %s\n", response.c_str());
    } else {
        Serial.printf("[CAM] Frame POST failed, code: %d\n", httpResponseCode);
    }

    http.end();
    return success;
}

void setup() {
    Serial.begin(115200);
    delay(500);

    Serial.println("\n========================================================");
    Serial.println("  DRISHTIGUARD ESP32-CAM AI VISION COMPANION NODE       ");
    Serial.println("========================================================");

    cameraInitialized = initCamera();
    if (!cameraInitialized) {
        Serial.println("[CAM] ERROR: Camera hardware failed to start.");
    } else {
        Serial.println("[CAM] Camera initialized successfully.");
    }

    connectWiFi();
}

void loop() {
    uint32_t now = millis();

    if (now - lastFrameTime >= FRAME_INTERVAL_MS) {
        lastFrameTime = now;

        if (!cameraInitialized) {
            // Attempt to re-init
            cameraInitialized = initCamera();
            return;
        }

        if (WiFi.status() != WL_CONNECTED) {
            WiFi.reconnect();
            return;
        }

        // Capture frame from OV2640
        camera_fb_t* fb = esp_camera_fb_get();
        if (!fb) {
            Serial.println("[CAM] Frame buffer capture failed");
            return;
        }

        // Upload frame to FastAPI YOLOv8n inference pipeline
        uploadFrame(fb);

        // Return frame buffer to driver
        esp_camera_fb_return(fb);
    }
}
