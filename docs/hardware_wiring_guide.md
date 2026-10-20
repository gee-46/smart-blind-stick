# 🦯 Smart Blind Stick - Hardware Wiring & Physical Integration Guide

This guide provides complete instructions for wiring all sensors, modules, and actuators to the **ESP32 microcontroller**, connecting the hardware to the FastAPI backend, and running the complete system.

---

## 📋 1. Bill of Materials (BOM)

| Component | Quantity | Purpose |
| :--- | :--- | :--- |
| **ESP32 DevKit V1** (30 or 38 pin) | 1 | Master IoT Controller (Wi-Fi, Bluetooth, Dual-Core) |
| **HC-SR04 Ultrasonic Sensor** | 1 (or 2) | Proximity & Obstacle Distance Detection (Head & Waist) |
| **MPU-6050 6-Axis IMU** | 1 | Accelerometer & Gyroscope for Automatic Fall Detection |
| **NEO-6M GPS Module** | 1 | Real-Time Geolocation & Satellite Tracking |
| **Momentary Pushbutton** | 1 | Emergency Manual SOS Trigger |
| **Active 5V Buzzer** | 1 | Acoustic Obstacle & Emergency Alerts |
| **Coin Vibration Motor** (3V - 5V) | 1 | Haptic Tactile Feedback on Cane Handle |
| **2N2222 NPN Transistor** (or MOSFET) | 1 | Switching driver for Vibration Motor |
| **Resistors** | 1kΩ, 2kΩ, 10kΩ | Logic level division & base current limiting |
| **18650 Li-Ion Cell + TP4056 Boost** | 1 | 3.7V - 5V Rechargeable Power Supply |
| **USB Webcam / CSI Camera** | 1 | Computer Vision Obstacle Classification & Tracking |

---

## 🔌 2. Complete Pin-to-Pin Connection Table

| Sensor / Module Pin | ESP32 GPIO Pin | Wire Color (Typical) | Electrical / Wiring Notes |
| :--- | :--- | :--- | :--- |
| **HC-SR04 VCC** | `5V / VIN` | Red | 5V Power supply |
| **HC-SR04 GND** | `GND` | Black | Common Ground |
| **HC-SR04 TRIG** | `GPIO 5` | Yellow | Output from ESP32 |
| **HC-SR04 ECHO** | `GPIO 18` | Green | Direct input or 1kΩ/2kΩ voltage divider (5V -> 3.3V safe) |
| **MPU-6050 VCC** | `3.3V` (or 5V) | Red | 3.3V Power |
| **MPU-6050 GND** | `GND` | Black | Common Ground |
| **MPU-6050 SDA** | `GPIO 21` | Blue | I2C Data (default hardware SDA) |
| **MPU-6050 SCL** | `GPIO 22` | Yellow | I2C Clock (default hardware SCL) |
| **NEO-6M VCC** | `3.3V / 5V` | Red | 3.3V or 5V Power |
| **NEO-6M GND** | `GND` | Black | Common Ground |
| **NEO-6M TX** | `GPIO 16` | Orange | Connects to ESP32 Hardware Serial2 RX |
| **NEO-6M RX** | `GPIO 17` | White | Connects to ESP32 Hardware Serial2 TX |
| **SOS Pushbutton Terminal 1**| `GPIO 4` | Purple | Active LOW, configured with internal `INPUT_PULLUP` |
| **SOS Pushbutton Terminal 2**| `GND` | Black | Connects to Ground on button press |
| **Active Buzzer (+)** | `GPIO 19` | Red | Positive lead (GPIO high triggers beep) |
| **Active Buzzer (-)** | `GND` | Black | Common Ground |
| **Vibration Motor (+)** | `5V / VIN` | Red | Positive motor terminal |
| **Vibration Motor (-)** | `Transistor Collector`| Black | Switched to GND via 2N2222 NPN |
| **2N2222 Base** | `GPIO 23` | White | Through a 1kΩ current-limiting resistor |
| **2N2222 Emitter** | `GND` | Black | Common Ground |
| **Battery Voltage Divider** | `GPIO 34` | Orange | Midpoint between two 10kΩ resistors from Battery (+) |

---

## 📐 3. System Architecture & Wiring Diagram

```text
                               +-----------------------------+
                               |     18650 Li-Ion Battery    |
                               |    (3.7V -> 5V Boost Reg)   |
                               +--------------+--------------+
                                              | 5V & GND
                                              v
                              +---------------+---------------+
                              |       ESP32 DevKit V1         |
                              +---------------+---------------+
                                 |   |   |   |   |   |   |
         +-----------------------+   |   |   |   |   |   +-----------------------+
         |                           |   |   |   |   |                           |
         v (GPIO 5, 18)              |   |   |   |   v (GPIO 4)                  v (GPIO 19, 23)
+------------------+                 |   |   |   | +------------------+  +--------------------+
| HC-SR04 Ultrasonic|                 |   |   |   | |  SOS Pushbutton  |  | Buzzer & Vibration |
| Obstacle Sensing |                 |   |   |   | | (Manual Distress)|  | (Haptic Feedback)  |
+------------------+                 |   |   |   | +------------------+  +--------------------+
                                     |   |   |   |
                +--------------------+   |   |   +--------------------+
                |                        |   |                        |
                v (I2C: GPIO 21, 22)     |   |                        v (ADC: GPIO 34)
      +-------------------+              |   |               +------------------+
      |  MPU-6050 6-DOF   |              |   |               | Battery Voltage  |
      |   Accelerometer   |              |   |               |   Divider (2:1)  |
      |  (Fall Detection) |              |   |               +------------------+
      +-------------------+              |   |
                                         v   v (UART2: GPIO 16, 17)
                                 +-------------------+
                                 |  NEO-6M GPS Chip  |
                                 | Satellite NMEA    |
                                 +-------------------+
```

---

## 🚀 4. How to Connect the Hardware & Run

You can connect and run the Smart Blind Stick in **two simple ways**:

### Method A: USB Cable Plugged into Computer (Simplest & Recommended for Testing)
1. Wire the components to the ESP32 as shown in the table above.
2. Open `firmware/esp32_smart_stick/esp32_smart_stick.ino` in Arduino IDE.
3. Select board: **DOIT ESP32 DEVKIT V1**, select your USB COM Port, and click **Upload**.
4. Leave the ESP32 connected via USB cable to your PC.
5. In your project terminal, start the backend server:
   ```bash
   python run.py
   ```
6. In a second terminal, start the **Serial Hardware Bridge**:
   ```bash
   python scripts/serial_hardware_bridge.py
   ```
   *The bridge will automatically detect your COM port (e.g. `COM3`), stream all telemetry into the app, and transmit buzzer/haptic commands back to the stick!*
7. Open the **Guardian Web Dashboard** in your browser:
   ```text
   http://127.0.0.1:8000/dashboard
   ```

---

### Method B: Standalone Wi-Fi Direct Mode (Wireless Cane)
1. Open `firmware/esp32_smart_stick/esp32_smart_stick.ino` in Arduino IDE.
2. Update your Wi-Fi credentials and PC local IP address:
   ```cpp
   const char* WIFI_SSID     = "MyHomeWiFi";
   const char* WIFI_PASSWORD = "MyPassword123";
   const char* BACKEND_BASE_URL = "http://192.168.1.50:8000"; // Your PC's IP
   ```
3. Flash the code to the ESP32.
4. Ensure your PC running `python run.py` is on the same Wi-Fi network.
5. Power the stick via power bank or battery — the stick will transmit check-ins, obstacle alerts, and SOS signals wirelessly directly to your backend!

---

### Method C: Adding AI Vision Camera
To connect your laptop webcam or USB cane camera:
```bash
python scripts/run_vision_hardware.py
```
This automatically runs real-time object detection and monocular distance estimation, annotates the video with direction/proximity HUD, and streams detected obstacles straight into the Guardian Dashboard!
