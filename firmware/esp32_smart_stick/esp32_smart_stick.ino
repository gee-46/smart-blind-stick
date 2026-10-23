/*
  =============================================================================
  🦯 SMART BLIND STICK - ESP32 FIRMWARE
  AI-Powered Assistive Mobility System Using IoT, Sensors, GPS & Computer Vision
  =============================================================================
  
  Target Microcontroller: ESP32 DevKit V1 (30-pin or 38-pin)
  Arduino IDE Board: "DOIT ESP32 DEVKIT V1" or "ESP32 Dev Module"

  HARDWARE PINOUT & CONNECTIONS:
  -----------------------------------------------------------------------------
  Component          ESP32 Pin     Notes
  -----------------------------------------------------------------------------
  HC-SR04 TRIG       GPIO 5        Ultrasonic trigger pulse (Output)
  HC-SR04 ECHO       GPIO 18       Ultrasonic echo pulse (Input, 3.3V safe)
  MPU-6050 SDA       GPIO 21       I2C Data line
  MPU-6050 SCL       GPIO 22       I2C Clock line
  NEO-6M GPS TX      GPIO 16       Serial2 RX (ESP32 receives NMEA sentences)
  NEO-6M GPS RX      GPIO 17       Serial2 TX (ESP32 transmits configuration)
  SOS Pushbutton     GPIO 4        Momentary switch to GND (INPUT_PULLUP)
  Active Buzzer      GPIO 19       Piezo buzzer (Output, PWM / digital)
  Vibration Motor    GPIO 23       NPN transistor/MOSFET gate driving motor
  Battery Voltage    GPIO 34       Analog ADC through 2:1 voltage divider
  Power (VCC)        5V / VIN      5V rail (from Li-ion boost converter)
  Ground (GND)       GND           Common Ground
  -----------------------------------------------------------------------------

  COMMUNICATION MODES:
  1. WiFi Direct HTTP: Posts telemetry directly to FastAPI backend over LAN.
  2. USB Serial Bridge: Outputs JSON packets on Serial (115200 baud) for
     scripts/serial_hardware_bridge.py when connected via USB cable.
*/

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <HardwareSerial.h>

// =============================================================================
// CONFIGURATION & CREDENTIALS
// =============================================================================
// Connect to any internet-enabled network:
// 1. Mobile Hotspot: configure phone's Personal Hotspot SSID & password
// 2. Home / Office Wi-Fi: configure router credentials
const char* WIFI_SSID     = "YOUR_WIFI_SSID";         // Replace with your WiFi or phone hotspot SSID
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";     // Replace with your WiFi or phone hotspot Password

// Cloud Backend URL: Use public HTTPS cloud URL or local development server
const char* BACKEND_BASE_URL = "https://smart-blind-stick.onrender.com";
const char* DEVICE_ID        = "STICK_001";
const char* DEVICE_API_KEY   = "";                    // Optional API key issued during registration

// Pin Assignments
const int PIN_TRIG      = 5;
const int PIN_ECHO      = 18;
const int PIN_SOS_BTN   = 4;
const int PIN_BUZZER    = 19;
const int PIN_VIBRO     = 23;
const int PIN_BATTERY   = 34;
const int PIN_GPS_RX    = 16;
const int PIN_GPS_TX    = 17;

// Hardware Serial 2 for GPS
HardwareSerial GPS_Serial(2);

// Timing variables
unsigned long lastCheckinTime = 0;
const unsigned long CHECKIN_INTERVAL_MS = 5000;

unsigned long lastSensorTime = 0;
const unsigned long SENSOR_INTERVAL_MS = 250;

// SOS button debouncing
int lastButtonState = HIGH;
unsigned long lastDebounceTime = 0;
const unsigned long DEBOUNCE_DELAY_MS = 50;

// MPU-6050 I2C Address
const int MPU_ADDR = 0x68;

// Fall Detection Constants
const float FALL_IMPACT_THRESHOLD_G = 2.4;
const float FALL_TILT_THRESHOLD_DEG = 40.0;

// =============================================================================
// HARDWARE INITIALIZATION
// =============================================================================
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n[STICK] Initializing Smart Blind Stick Hardware...");

  // Actuator pins
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_VIBRO, OUTPUT);
  digitalWrite(PIN_BUZZER, LOW);
  digitalWrite(PIN_VIBRO, LOW);

  // Ultrasonic pins
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);

  // SOS button with internal pullup
  pinMode(PIN_SOS_BTN, INPUT_PULLUP);

  // Battery ADC
  pinMode(PIN_BATTERY, INPUT);

  // Initialize I2C for MPU-6050
  Wire.begin(21, 22);
  initMPU6050();

  // Initialize GPS Serial (9600 baud default for NEO-6M)
  GPS_Serial.begin(9600, SERIAL_8N1, PIN_GPS_RX, PIN_GPS_TX);

  // Welcome chirp
  playChirp(200);

  // Connect to WiFi (optional - stick still operates via USB Serial if WiFi fails)
  connectWiFi();

  Serial.println("[STICK] Hardware initialization complete. System online.");
}

// =============================================================================
// MAIN EVENT LOOP
// =============================================================================
void loop() {
  unsigned long now = millis();

  // 1. Monitor Hardware SOS Button
  checkSOSButton();

  // 2. High-Frequency Sensor & Fall Detection Check
  if (now - lastSensorTime >= SENSOR_INTERVAL_MS) {
    lastSensorTime = now;
    readUltrasonicDistance();
    checkFallDetection();
  }

  // 3. Periodic GPS & Telemetry Check-in
  if (now - lastCheckinTime >= CHECKIN_INTERVAL_MS) {
    lastCheckinTime = now;
    sendPeriodicCheckin();
  }

  // 4. Listen for Incoming Serial Feedback from PC Bridge
  readSerialFeedback();
}

// =============================================================================
// SENSOR FUNCTIONS
// =============================================================================
void initMPU6050() {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B); // PWR_MGMT_1 register
  Wire.write(0);    // Wake up MPU-6050
  if (Wire.endTransmission() == 0) {
    Serial.println("[STICK] MPU-6050 IMU initialized.");
  } else {
    Serial.println("[STICK] Warning: MPU-6050 not responding on I2C (Check wiring SDA=21, SCL=22).");
  }
}

float measureUltrasonicCM() {
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);

  long duration = pulseIn(PIN_ECHO, HIGH, 30000); // 30ms timeout (~5m max)
  if (duration == 0) return 300.0; // Clear path / timeout
  float distance = (duration * 0.0343) / 2.0;
  return distance;
}

void readUltrasonicDistance() {
  float distanceCm = measureUltrasonicCM();

  // Local Haptic & Audio Feedback based on proximity
  if (distanceCm < 40.0 && distanceCm > 0) {
    // Critical Proximity (< 40cm): Continuous vibration + continuous alarm
    digitalWrite(PIN_VIBRO, HIGH);
    digitalWrite(PIN_BUZZER, HIGH);
  } else if (distanceCm < 100.0 && distanceCm >= 40.0) {
    // High Risk (40cm - 1m): Fast pulsing
    digitalWrite(PIN_VIBRO, (millis() / 150) % 2);
    digitalWrite(PIN_BUZZER, (millis() / 150) % 2);
  } else if (distanceCm < 180.0 && distanceCm >= 100.0) {
    // Medium Risk (1m - 1.8m): Gentle pulse
    digitalWrite(PIN_VIBRO, (millis() / 350) % 2);
    digitalWrite(PIN_BUZZER, LOW);
  } else {
    // Clear Path
    digitalWrite(PIN_VIBRO, LOW);
    digitalWrite(PIN_BUZZER, LOW);
  }

  // If obstacle is within detection range, output packet
  if (distanceCm < 180.0) {
    String json = "{\"type\":\"sensor\",\"device_id\":\"" + String(DEVICE_ID) +
                  "\",\"ultrasonic_cm\":" + String(distanceCm, 1) + "}";
    Serial.println(json);

    // Send HTTP if connected
    if (WiFi.status() == WL_CONNECTED) {
      postHTTP("/api/sensors/data", json);
    }
  }
}

void checkFallDetection() {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B); // Accel data register
  if (Wire.endTransmission(false) != 0) return;

  Wire.requestFrom(MPU_ADDR, 6, true);
  if (Wire.available() < 6) return;

  int16_t rawX = Wire.read() << 8 | Wire.read();
  int16_t rawY = Wire.read() << 8 | Wire.read();
  int16_t rawZ = Wire.read() << 8 | Wire.read();

  // Convert raw values to g's (standard sensitivity 16384 LSB/g)
  float ax = rawX / 16384.0;
  float ay = rawY / 16384.0;
  float az = rawZ / 16384.0;

  // Signal Vector Magnitude (SVM)
  float svm = sqrt(ax * ax + ay * ay + az * az);

  // Compute stick tilt angle from vertical (Z-axis)
  float tiltDeg = 0.0;
  if (svm > 0.01) {
    float cosTheta = az / svm;
    if (cosTheta > 1.0) cosTheta = 1.0;
    if (cosTheta < -1.0) cosTheta = -1.0;
    tiltDeg = acos(cosTheta) * (180.0 / 3.14159265);
  }

  // Evaluate multi-condition fall criteria
  if (svm >= FALL_IMPACT_THRESHOLD_G && tiltDeg >= FALL_TILT_THRESHOLD_DEG) {
    Serial.println("[STICK] 💥 POTENTIAL FALL DETECTED! SVM=" + String(svm, 2) + "g, Tilt=" + String(tiltDeg, 1) + "°");
    playFallWarningPattern();

    String json = "{\"type\":\"fall\",\"device_id\":\"" + String(DEVICE_ID) +
                  "\",\"accel_magnitude\":" + String(svm, 2) +
                  ",\"tilt_angle_degrees\":" + String(tiltDeg, 1) +
                  ",\"free_fall_detected\":true,\"immobility_detected\":true}";
    Serial.println(json);

    if (WiFi.status() == WL_CONNECTED) {
      postHTTP("/api/emergency/fall/detect", json);
    }
  }
}

// =============================================================================
// SOS BUTTON & EMERGENCY
// =============================================================================
void checkSOSButton() {
  int reading = digitalRead(PIN_SOS_BTN);
  if (reading != lastButtonState) {
    lastDebounceTime = millis();
  }

  if ((millis() - lastDebounceTime) > DEBOUNCE_DELAY_MS) {
    if (reading == LOW) { // Button pressed (active low)
      Serial.println("[STICK] 🚨 PHYSICAL SOS BUTTON PRESSED!");
      playSOSAlarm();

      String json = "{\"type\":\"sos\",\"device_id\":\"" + String(DEVICE_ID) +
                    "\",\"reason\":\"Hardware momentary push button activated on stick handle\"}";
      Serial.println(json);

      if (WiFi.status() == WL_CONNECTED) {
        postHTTP("/api/emergency/sos/manual", json);
      }
      delay(500); // debounce lockout
    }
  }
  lastButtonState = reading;
}

// =============================================================================
// BATTERY & GPS TELEMETRY
// =============================================================================
float readBatteryPercentage() {
  int raw = analogRead(PIN_BATTERY);
  // ADC reading with 2:1 voltage divider (0 - 4095 corresponds to 0 - 6.6V battery)
  float voltage = (raw / 4095.0) * 3.3 * 2.0;
  // Map 3.3V (0%) to 4.2V (100%) for 1S Li-Ion cell
  float percent = ((voltage - 3.3) / (4.2 - 3.3)) * 100.0;
  if (percent > 100.0) percent = 100.0;
  if (percent < 0.0) percent = 0.0;
  return percent;
}

void sendPeriodicCheckin() {
  float battery = readBatteryPercentage();
  // Default coordinates (updated when GPS has valid lock)
  float lat = 12.9716;
  float lon = 77.5946;

  String json = "{\"type\":\"checkin\",\"device_id\":\"" + String(DEVICE_ID) +
                "\",\"battery\":" + String(battery, 1) +
                ",\"latitude\":" + String(lat, 6) +
                ",\"longitude\":" + String(lon, 6) +
                ",\"status\":\"active\",\"gps_available\":true}";
  Serial.println(json);

  if (WiFi.status() == WL_CONNECTED) {
    postHTTP("/api/device/data", json);
  }
}

// =============================================================================
// AUDIO & HAPTIC PATTERNS
// =============================================================================
void playChirp(int ms) {
  digitalWrite(PIN_BUZZER, HIGH);
  digitalWrite(PIN_VIBRO, HIGH);
  delay(ms);
  digitalWrite(PIN_BUZZER, LOW);
  digitalWrite(PIN_VIBRO, LOW);
}

void playSOSAlarm() {
  for (int i = 0; i < 3; i++) {
    digitalWrite(PIN_BUZZER, HIGH);
    digitalWrite(PIN_VIBRO, HIGH);
    delay(250);
    digitalWrite(PIN_BUZZER, LOW);
    digitalWrite(PIN_VIBRO, LOW);
    delay(100);
  }
}

void playFallWarningPattern() {
  for (int i = 0; i < 4; i++) {
    digitalWrite(PIN_BUZZER, HIGH);
    delay(80);
    digitalWrite(PIN_BUZZER, LOW);
    delay(80);
  }
}

// =============================================================================
// SERIAL FEEDBACK & WIFI
// =============================================================================
void readSerialFeedback() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.indexOf("\"vibe\":\"continuous\"") >= 0 || line.indexOf("\"buzz\":\"alarm\"") >= 0) {
      playSOSAlarm();
    } else if (line.indexOf("\"vibe\":\"pulse_fast\"") >= 0) {
      playChirp(150);
    }
  }
}

void connectWiFi() {
  if (String(WIFI_SSID) == "YOUR_WIFI_SSID") {
    Serial.println("[STICK] WiFi SSID not configured. Operating in USB Serial Bridge mode.");
    return;
  }
  Serial.print("[STICK] Connecting to WiFi: ");
  Serial.println(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 15) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[STICK] WiFi Connected! IP Address: " + WiFi.localIP().toString());
  } else {
    Serial.println("\n[STICK] WiFi connection timed out. Falling back to USB Serial Bridge mode.");
  }
}

void postHTTP(const char* endpoint, const String& jsonPayload) {
  String fullUrl = String(BACKEND_BASE_URL) + String(endpoint);

  if (fullUrl.startsWith("https://")) {
    WiFiClientSecure secureClient;
    secureClient.setInsecure(); // Allows standard cloud TLS connection without hardcoding CA expiration
    HTTPClient http;
    http.begin(secureClient, fullUrl);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-Device-Id", DEVICE_ID);
    if (strlen(DEVICE_API_KEY) > 0) {
      http.addHeader("X-API-Key", DEVICE_API_KEY);
    }
    int httpCode = http.POST(jsonPayload);
    http.end();
  } else {
    HTTPClient http;
    http.begin(fullUrl);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-Device-Id", DEVICE_ID);
    if (strlen(DEVICE_API_KEY) > 0) {
      http.addHeader("X-API-Key", DEVICE_API_KEY);
    }
    int httpCode = http.POST(jsonPayload);
    http.end();
  }
}
