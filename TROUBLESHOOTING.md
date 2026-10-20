# DrishtiGuard Hardware & Network Troubleshooting Guide

---

## 1. GPS Issues: No Fix or Missing Data

### Symptom: `gps_available: false` or Satellites = 0
- **Cause 1: Indoor Testing**: GPS signals (1575.42 MHz) cannot penetrate concrete ceilings.
  - **Resolution**: Move near an open window or outdoors with an unobstructed view of the sky.
- **Cause 2: Cold Start Delay**: The NEO-6M module requires 45 seconds to 3 minutes on cold start to download the GPS ephemeris.
  - **Resolution**: Wait until the green PPS LED on the NEO-6M starts blinking (indicates valid 1PPS lock).
- **Cause 3: Swapped UART Pins**:
  - **Resolution**: Verify connections:
    - NEO-6M **TX** -> ESP32 **GPIO 26** (RX1).
    - NEO-6M **RX** -> ESP32 **GPIO 27** (TX1).
- **Cause 4: Baud Rate Mismatch**:
  - **Resolution**: The default baud rate for NEO-6M is **9600 baud**. Confirm `GPS_BAUDRATE 9600` in `pinout.h`.

---

## 2. TF-Luna LiDAR Issues

### Symptom: Serial Monitor reports `TF-Luna LiDAR... FAILED` or Distance is -1
- **Cause 1: Insufficient Power**: TF-Luna requires 5V ± 0.1V and pulls ~150mA during laser emission pulses. Powering from the ESP32 3.3V pin causes brownout or measurement failure.
  - **Resolution**: Power TF-Luna strictly from the **5.0V regulated power rail**.
- **Cause 2: Serial Pin Allocation**:
  - **Resolution**: Confirm:
    - TF-Luna **TX** -> ESP32 **GPIO 16** (RX2).
    - TF-Luna **RX** -> ESP32 **GPIO 17** (TX2).
- **Cause 3: Low Signal Strength (Flux < 100)**:
  - **Resolution**: Highly reflective black surfaces or targets beyond 8 meters absorb laser pulses. The driver honestly flags these as out-of-range (`is_valid = false`).

---

## 3. MPU6050 IMU Issues

### Symptom: `Initializing MPU6050 IMU... FAILED`
- **Cause 1: Missing I2C Pull-Up Resistors**:
  - **Resolution**: The ESP32 internal pullups are weak (~45kΩ). Install **4.7kΩ pull-up resistors** between SDA (GPIO 21) and 3.3V, and between SCL (GPIO 22) and 3.3V.
- **Cause 2: Wrong I2C Address**:
  - **Resolution**: If the AD0 pin of the MPU6050 is connected to 3.3V, its I2C address becomes `0x69` instead of `0x68`. Connect AD0 to GND for `0x68`.
- **Cause 3: I2C Bus Hang**:
  - **Resolution**: If the ESP32 reboots while a slave holds SDA low, the bus hangs. DrishtiGuard's driver re-initializes Wire at startup to send clock pulses that clear hung slaves.

---

## 4. DFPlayer Mini Audio Issues

### Symptom: Audio sounds distorted, clicks, or buzzes during Wi-Fi transmission
- **Cause 1: Missing Series Resistor**:
  - **Resolution**: You must place a **1kΩ series resistor** between ESP32 TX (GPIO 25) and DFPlayer Mini RX to suppress high-frequency noise and match logic levels.
- **Cause 2: Brownout on Loud Volume**:
  - **Resolution**: The internal 3W amplifier can pull up to 1A peaks on loud bass notes. Place a 470µF or 1000µF electrolytic capacitor across the DFPlayer Mini VCC and GND pins.
- **Cause 3: Folder Structure Incorrect**:
  - **Resolution**: The MicroSD card must be formatted FAT32. Tracks must be named `0001.mp3`, `0002.mp3` inside a folder named `/mp3/`.

---

## 5. ESP32-CAM Issues

### Symptom: `Camera init failed with error 0x20002` or `Brownout detector was triggered`
- **Cause 1: Low Current on 5V Rail**:
  - **Resolution**: When the OV2640 initializes and Wi-Fi transmits, peak current exceeds 500mA. Power the ESP32-CAM from a dedicated 5V rail capable of 2A.
- **Cause 2: Flashing Error (`Failed to connect to ESP32: Timed out`)**:
  - **Resolution**: Connect **GPIO 0 to GND** before powering on, then press the onboard `RST` button. Disconnect GPIO 0 after flashing.

---

## 6. Wi-Fi & Backend Connectivity Issues

### Symptom: Stick reports `POST /api/device/data failed. Code: -1`
- **Cause 1: Wrong Backend IP**:
  - **Resolution**: In `firmware/include/config.h`, replace `http://192.168.1.100:8000` with the actual LAN IP address of your host PC (find via `ipconfig` on Windows).
- **Cause 2: Host Firewall Blocking Port 8000**:
  - **Resolution**: Open Windows Defender Firewall -> Inbound Rules -> Allow TCP Port 8000 for local private network.
- **Cause 3: Offline Resilience Verification**:
  - **Resolution**: When Wi-Fi is lost, DrishtiGuard buffers emergency SOS alerts in its bounded queue (`_event_queue`). Once Wi-Fi reconnects, the queue is automatically flushed to the backend.
