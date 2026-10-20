/**
 * @file cam_config.h
 * @brief Configuration for ESP32-CAM AI Vision Node
 */

#ifndef CAM_CONFIG_H
#define CAM_CONFIG_H

#define CAM_WIFI_SSID       "YOUR_WIFI_SSID"
#define CAM_WIFI_PASS       "YOUR_WIFI_PASSWORD"

// Base URL of FastAPI Backend running YOLOv8n inference
#define INFERENCE_BASE_URL  "http://192.168.1.100:8000"
#define INFERENCE_ENDPOINT  "/api/vision/infer"
#define ASSOCIATED_DEVICE_ID "STICK_001"

// Frame capture interval in milliseconds (e.g. 500ms = 2 FPS; 1000ms = 1 FPS)
#define FRAME_INTERVAL_MS   1000

// Frame resolution: FRAMESIZE_QVGA (320x240) or FRAMESIZE_VGA (640x480)
#define CAMERA_FRAME_SIZE   FRAMESIZE_QVGA
#define CAMERA_JPEG_QUALITY 12 // 10-63, lower means higher quality

#endif // CAM_CONFIG_H
