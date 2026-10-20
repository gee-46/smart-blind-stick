# DrishtiGuard Firmware Setup & Flashing Guide

> **STATUS:** Firmware architecture complete and ready for compilation. Physical hardware flashing marked as **Awaiting Physical Assembly Verification**.

---

## 1. Prerequisites & Toolchain Installation

The DrishtiGuard firmware is organized as a standard [PlatformIO](https://platformio.org/) project with the Arduino framework.

### Option A: PlatformIO CLI (Recommended for automated builds)
Install PlatformIO via Python pip:
```bash
python -m pip install -U platformio
pio --version
```

### Option B: VS Code / Cursor IDE Extension
1. Open VS Code or Cursor.
2. Install the **PlatformIO IDE** extension.
3. Open the repository root; PlatformIO will automatically recognize `firmware/platformio.ini`.

---

## 2. Firmware Directory Organization

```text
firmware/
├── platformio.ini              # Multi-target build configuration (ESP32 Stick + ESP32-CAM)
├── include/
│   ├── config.h                # Device ID, Wi-Fi credentials, thresholds, calibration
│   ├── pinout.h                # Verified GPIO pin assignments and electrical constants
│   ├── tf_luna.h               # TF-Luna LiDAR driver interface
│   ├── gps_reader.h            # NEO-6M GPS NMEA sentence parser
│   ├── mpu6050_fall.h          # 6-axis motion sensing & multi-stage fall pipeline
│   ├── dfplayer_audio.h        # DFPlayer Mini voice prompt controller
│   ├── haptics.h               # Non-blocking vibration & buzzer alert patterns
│   ├── sos_button.h            # Debounced physical emergency button
│   ├── battery.h               # Voltage divider ADC reader and calibration
│   ├── wifi_manager.h          # Station mode Wi-Fi manager with exponential backoff
│   └── backend_client.h        # Authenticated REST/WebSocket client & offline event queue
├── src/
│   ├── main.cpp                # Application loop, subsystem init, autonomous local safety
│   ├── tf_luna.cpp             # 9-byte packet parser, checksum validation, hysteresis
│   ├── gps_reader.cpp          # TinyGPSPlus integration, fix quality, zero-coord rejection
│   ├── mpu6050_fall.cpp        # Free-fall -> Impact spike -> Tilt angle -> Inactivity window
│   ├── dfplayer_audio.cpp      # Non-blocking audio commands, priority preemption
│   ├── haptics.cpp             # Non-blocking PWM vibration and buzzer pulse patterns
│   ├── sos_button.cpp          # Debouncing state machine, long-press latch
│   ├── battery.cpp             # ADC multi-sample, calibration curve, percentage conversion
│   ├── wifi_manager.cpp        # Resilient Wi-Fi station connectivity
│   └── backend_client.cpp      # HTTP telemetry dispatch and offline event queue flush
└── esp32_cam/                  # Dedicated ESP32-CAM Vision Companion Node
    ├── platformio.ini          # PlatformIO config for AI-Thinker board
    ├── include/
    │   ├── cam_pinout.h        # OV2640 camera pin definitions
    │   └── cam_config.h        # Wi-Fi & backend inference endpoint URL
    └── src/
        └── main.cpp            # OV2640 frame capture & HTTP POST snapshot client
```

---

## 3. Configuration & Provisioning

Before flashing, edit `firmware/include/config.h`:

```c
// 1. Set your network credentials
#define DEFAULT_WIFI_SSID   "MyHomeWiFi"
#define DEFAULT_WIFI_PASS   "MySecurePassword"

// 2. Set your FastAPI backend server URL (must be reachable from the stick's LAN)
#define BACKEND_BASE_URL    "http://192.168.1.100:8000"

// 3. Set the unique device ID for this stick
#define DEFAULT_DEVICE_ID   "STICK_001"
```

For the ESP32-CAM companion node, edit `firmware/esp32_cam/include/cam_config.h`:
```c
#define CAM_WIFI_SSID       "MyHomeWiFi"
#define CAM_WIFI_PASS       "MySecurePassword"
#define INFERENCE_BASE_URL  "http://192.168.1.100:8000"
#define ASSOCIATED_DEVICE_ID "STICK_001"
```

---

## 4. DFPlayer Mini MicroSD Card Setup

Prepare a clean FAT16 or FAT32 formatted MicroSD card (32GB or smaller).
Create a folder named `mp3` in the root of the SD card:

```text
SD_CARD/
└── mp3/
    ├── 0001.mp3    # "Warning: Obstacle within half meter"
    ├── 0002.mp3    # "Obstacle detected ahead"
    ├── 0003.mp3    # "Fall detected. Alerting guardians."
    ├── 0004.mp3    # "Emergency SOS activated."
    ├── 0005.mp3    # "GPS signal connected."
    ├── 0006.mp3    # "Battery level low. Please recharge."
    └── 0007.mp3    # "DrishtiGuard online. Ready for navigation."
```

---

## 5. Compilation & Flashing Instructions

### 5.1 Flashing the Main ESP32 Controller
1. Connect the ESP32 DevKit V1 board to your computer via micro-USB.
2. Verify COM port in Device Manager (e.g., `COM3` on Windows).
3. From the `firmware/` directory, compile the code:
   ```bash
   cd firmware
   pio run -e esp32_stick
   ```
4. Flash the compiled firmware:
   ```bash
   pio run -e esp32_stick -t upload
   ```
5. Open the Serial Monitor to observe boot diagnostics:
   ```bash
   pio device monitor -b 115200
   ```

### 5.2 Flashing the AI-Thinker ESP32-CAM
1. Connect the ESP32-CAM to a USB-to-UART FTDI adapter:
   - FTDI `VCC (5V)` -> ESP32-CAM `5V` (Do **not** power from 3.3V)
   - FTDI `GND` -> ESP32-CAM `GND`
   - FTDI `TX` -> ESP32-CAM `U0RXD` (GPIO 3)
   - FTDI `RX` -> ESP32-CAM `U0TXD` (GPIO 1)
   - **Crucial**: Connect ESP32-CAM `GPIO 0` to `GND` (enables flashing mode).
2. Press the `RST` button on the bottom of the ESP32-CAM board.
3. Flash the firmware:
   ```bash
   cd firmware
   pio run -e esp32_cam -t upload
   ```
4. Disconnect `GPIO 0` from `GND`, and press `RST` to boot into normal camera execution.
5. Monitor logs:
   ```bash
   pio device monitor -e esp32_cam -b 115200
   ```

---

## 6. Expected Serial Boot Output

When powered on, the ESP32 Serial Monitor (115200 baud) will display:

```text
========================================================
  DRISHTIGUARD SMART BLIND STICK — ESP32 FIRMWARE v1.0 
========================================================
[INIT] Initializing TF-Luna LiDAR... OK
[INIT] Initializing NEO-6M GPS... OK
[INIT] Initializing MPU6050 IMU... OK
[INIT] Initializing DFPlayer Mini... OK
[WIFI] Connecting to SSID: MyHomeWiFi ...
[WIFI] Connected successfully! IP: 192.168.1.145, RSSI: -54 dBm
[INIT] All subsystems initialized. Starting main loop.
```
