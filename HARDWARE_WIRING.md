# DrishtiGuard Hardware Wiring & Electrical Architecture Specification

> **STATUS:** Complete software architecture implemented. Physical connections marked as **Awaiting Physical Assembly Verification**.

---

## 1. System Overview

DrishtiGuard utilizes a dual-microcontroller architecture:
1. **ESP32 DevKit V1 (Main Controller)**: Handles all real-time sensory perception (TF-Luna LiDAR, NEO-6M GPS, MPU6050 6-axis IMU, Battery ADC), local autonomous obstacle warnings, DFPlayer Mini voice synthesis, haptic vibration/buzzer feedback, physical SOS button handling, and telemetry dispatch to the FastAPI backend.
2. **AI-Thinker ESP32-CAM (AI Vision Node)**: Companion camera module capturing genuine visual frames (QVGA 320x240) and dispatching them over Wi-Fi directly to the FastAPI YOLOv8n companion inference pipeline.
3. **No Raspberry Pi**: The design strictly avoids Raspberry Pi, keeping weight, bulk, and power consumption within handheld mobility stick parameters.

---

## 2. Complete ESP32 DevKit V1 Pin Allocation Table

| Component | Pin / Signal | ESP32 GPIO | Logic Level | Operating Voltage | Current Req. | Circuit Protection / Driving Requirement |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TF-Luna LiDAR** | TX | GPIO 16 (RX2) | 3.3V TTL | 5.0V ± 0.1V | ~80mA (150mA peak) | Direct connection to RX2. Powered from 5V rail. |
| **TF-Luna LiDAR** | RX | GPIO 17 (TX2) | 3.3V TTL | 5.0V ± 0.1V | Signal | Direct connection to TX2. |
| **NEO-6M GPS** | TX | GPIO 26 (RX1) | 3.3V TTL | 3.3V - 5.0V | ~45mA | Direct connection to RX1. Powered from 3.3V or 5V. |
| **NEO-6M GPS** | RX | GPIO 27 (TX1) | 3.3V TTL | 3.3V - 5.0V | Signal | Direct connection to TX1. |
| **MPU6050 IMU** | SDA | GPIO 21 (SDA) | 3.3V I2C | 3.3V | ~4mA | Requires 4.7kΩ pull-up resistor to 3.3V. |
| **MPU6050 IMU** | SCL | GPIO 22 (SCL) | 3.3V I2C | 3.3V | ~4mA | Requires 4.7kΩ pull-up resistor to 3.3V. |
| **DFPlayer Mini** | RX | GPIO 25 (TX) | 3.3V -> 5V | 3.3V - 5.0V | Signal | **1kΩ series resistor** on ESP32 TX to DFPlayer RX. |
| **DFPlayer Mini** | TX | GPIO 33 (RX) | 3.3V TTL | 3.3V - 5.0V | Signal | Direct connection to GPIO 33. |
| **DFPlayer Mini** | BUSY | GPIO 35 (Input) | 3.3V TTL | 3.3V - 5.0V | Signal | Active LOW during audio playback. |
| **Vibration Motor**| Gate Drive | GPIO 23 | 3.3V PWM | 3.7V - 5.0V | ~80mA - 120mA | **N-Channel MOSFET** (e.g., AO3400 / 2N7000), 10kΩ gate pulldown, flyback diode (1N4148) across motor terminals. |
| **Active Buzzer** | Drive | GPIO 19 | 3.3V Digital | 3.3V - 5.0V | ~30mA | Driven via NPN transistor (2N2222) or N-MOSFET. |
| **SOS Button** | Switch | GPIO 4 | 3.3V Logic | - | < 1mA | Momentary switch to GND with internal `INPUT_PULLUP`. |
| **Battery Divider**| Analog In | GPIO 34 (ADC1_CH6)| 0V - 3.1V Max | Li-ion (3.2V-4.2V)| < 0.1mA | **Resistor Voltage Divider**: 100kΩ (R1) + 100kΩ (R2) 1% tolerance. |
| **Status LED** | Anode | GPIO 18 | 3.3V Digital | 3.3V | ~5mA | 330Ω current-limiting resistor to GND. |

---

## 3. ESP32-CAM Pinout Table (AI-Thinker Model)

| Component / Function | Camera Signal | ESP32-CAM Pin | Electrical Constraints |
| :--- | :--- | :--- | :--- |
| **OV2640 Data** | Y2, Y3, Y4, Y5 | GPIO 5, 18, 19, 21 | Dedicated to camera sensor. Do not attach external sensors. |
| **OV2640 Data** | Y6, Y7, Y8, Y9 | GPIO 36, 39, 34, 35 | Dedicated to camera sensor. |
| **OV2640 Clock** | XCLK | GPIO 0 | 20MHz external clock generator. |
| **OV2640 Sync** | PCLK, VSYNC, HREF | GPIO 22, 25, 23 | Pixel, Frame, and Line sync lines. |
| **I2C SCCB Control** | SIOD (SDA), SIOC (SCL)| GPIO 26, 27 | Camera SCCB register configuration bus. |
| **Power Down** | PWDN | GPIO 32 | Active HIGH power-down control. |
| **Flash LED** | Onboard White LED | GPIO 4 | High-power illumination LED. Controlled via PWM/digital. |
| **UART Programming** | U0TXD, U0RXD | GPIO 1, GPIO 3 | Used with external FTDI USB-UART adapter for flashing. |
| **Boot Mode** | GPIO 0 | GPIO 0 | Connect to GND to enter flashing mode; open for normal run. |

---

## 4. Electrical Safety, Power Rails & Driving Circuits

### 4.1 Power Supply Distribution
- **Battery Pack**: 1S 18650 or LiPo cell (nominal 3.7V, fully charged 4.2V, discharge cutoff 3.0V).
- **Boost Converter (Step-Up)**: High-efficiency 5.0V synchronous boost converter (e.g., MT3608 or TP4056 + Boost combo module) providing:
  - Stable **5.0V rail** (minimum 1.5A peak capacity).
  - Supplies ESP32 DevKit `5V/VIN` pin (fed into onboard 3.3V AMS1117 LDO).
  - Supplies TF-Luna LiDAR `5V` pin.
  - Supplies DFPlayer Mini `VCC` pin.
  - Supplies ESP32-CAM `5V` pin (requires separate clean filtering).
- **Common Ground**: All sensor grounds, power grounds, motor grounds, and microcontroller grounds **MUST** be tied to a star ground reference to prevent ground loops and measurement jitter.

### 4.2 High-Current Peripheral Drivers (Vibration & Buzzer)
> **CAUTION:** The ESP32 GPIO pins can supply a maximum of 12mA (recommended) to 40mA (absolute maximum limit). Connecting an inductive DC vibration motor directly to a GPIO will destroy the ESP32 pin!

- **Vibration Motor Circuit**:
  - ESP32 GPIO 23 -> 220Ω resistor -> Gate of N-Channel Logic-Level MOSFET (AO3400 / IRLML2502).
  - Gate to GND: 10kΩ pull-down resistor (prevents floating gate turn-on during ESP32 boot).
  - Drain of MOSFET -> Negative (-) lead of vibration motor.
  - Positive (+) lead of vibration motor -> 5V rail or Battery VCC.
  - Flyback Diode: 1N4148 or Schottky 1N5819 connected in parallel across motor terminals (Cathode to (+), Anode to (-)) to absorb inductive kickback spikes.

### 4.3 DFPlayer Mini Level Protection
- The DFPlayer Mini operates with internal 5V-tolerant pull-ups on its UART lines.
- Connecting ESP32 GPIO 25 directly to DFPlayer RX without resistance causes audio hum, static distortion, and thermal stress on the module.
- A **1kΩ series resistor** must be placed in-line between ESP32 TX (GPIO 25) and DFPlayer Mini RX.

### 4.4 Battery ADC Sensing Divider
- Maximum safe input voltage to an ESP32 ADC pin is 3.3V (with 11dB attenuation, linear range is ~0.15V to 3.1V).
- Connect Battery (+) -> R1 (100kΩ, 1%) -> GPIO 34 -> R2 (100kΩ, 1%) -> GND.
- Division ratio: $V_{pin} = V_{bat} \times \frac{R_2}{R_1 + R_2} = 0.5 \times V_{bat}$.
- For a 4.2V full battery: $V_{pin} = 2.10V$ (well within safe linear ADC range).
- Add a 100nF ceramic capacitor between GPIO 34 and GND to filter high-frequency ADC noise.

---

## 5. Bootstrapping Pin Conflicts & Constraints Checklist

1. **GPIO 0**: Strapping pin. Kept free on the main ESP32 stick (used for boot mode). On ESP32-CAM, used for XCLK.
2. **GPIO 2**: Strapping pin (must be floating or LOW during flash). Left unconnected.
3. **GPIO 12 (MTDI)**: Strapping pin for flash voltage (1.8V vs 3.3V). If pulled HIGH during boot, flash is under-volted and ESP32 enters a crash loop. **Intentionally unassigned.**
4. **GPIO 15**: Strapping pin (silences ROM boot messages). Left unassigned.
5. **GPIO 6 - 11**: Internally connected to the SPI flash IC. Never expose or connect to external components.
6. **GPIO 34, 35, 36 (VP), 39 (VN)**: Input-only pins without software-configurable internal pullups. Allocated exclusively to analog inputs (Battery ADC) and digital inputs with external pullups/signals (DFPlayer BUSY).
