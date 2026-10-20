# DrishtiGuard Hardware Integration & Bring-Up Checklist

> **CRITICAL RULE:** Do not mark any physical hardware test as completed until physical assembly is finished and the actual component has been tested with real hardware.
>
> All items below are currently marked: **NOT VERIFIED (Awaiting Physical Assembly)**.

---

## Pre-Power Safety Inspection

- [ ] **[NOT VERIFIED] Star Ground Verification**: Multimeter continuity check confirms common ground between Battery (-), Boost Converter GND, ESP32 GND, TF-Luna GND, GPS GND, MPU6050 GND, DFPlayer GND, and ESP32-CAM GND.
- [ ] **[NOT VERIFIED] Power Rail Voltage Check**: Before connecting the ESP32 or sensors, power on the battery boost converter and measure the 5V rail. Confirm voltage is strictly between **4.90V and 5.20V**.
- [ ] **[NOT VERIFIED] Flyback Diode Polarity Check**: Confirm 1N4148/1N5819 diode across vibration motor terminals has its Cathode (stripe) connected to the positive supply rail.
- [ ] **[NOT VERIFIED] Voltage Divider Safety**: Confirm resistance of R1 (100kΩ) and R2 (100kΩ). At 4.2V battery input, confirm voltage at GPIO 34 pin header does not exceed **2.15V**.

---

## Modular Subsystem Verification Steps

### Step 1: Battery Monitoring & ADC
- [ ] **[NOT VERIFIED] Raw Voltage Sampling**: Flash firmware, open Serial Monitor (115200 baud). Confirm reading matches multimeter reading within ±0.05V.
- [ ] **[NOT VERIFIED] Percentage Mapping**: Confirm a 3.7V nominal battery reports approximately 50-55%.
- [ ] **[NOT VERIFIED] Disconnected Circuit Behavior**: Disconnect battery sensing pin. Confirm firmware reports `battery: null` ("No data available") rather than an arbitrary number.

### Step 2: TF-Luna LiDAR Distance Sensor
- [ ] **[NOT VERIFIED] UART Communication**: Confirm 9-byte packet reception on Serial2 (GPIO 16 RX, GPIO 17 TX) at 115200 baud.
- [ ] **[NOT VERIFIED] Range Verification**: Place target at measured distances (30cm, 100cm, 200cm). Confirm LiDAR readings match physical tape measure within ±2cm.
- [ ] **[NOT VERIFIED] Signal Flux Validation**: Confirm readings with signal strength < 100 are properly rejected as invalid.
- [ ] **[NOT VERIFIED] Local Obstacle Warning**: Place hand closer than 50cm. Verify immediate vibration and audio warning trigger locally with zero latency, even with Wi-Fi disabled.

### Step 3: NEO-6M GPS Receiver
- [ ] **[NOT VERIFIED] UART Communication**: Confirm raw NMEA `$GPGGA` and `$GPRMC` strings arrive on Serial1 (GPIO 26 RX, GPIO 27 TX) at 9600 baud.
- [ ] **[NOT VERIFIED] Outdoor Satellite Lock**: Take stick outdoors with open view of sky. Wait 1-3 minutes for cold start. Confirm green PPS LED blinks.
- [ ] **[NOT VERIFIED] Fix Quality & Satellites**: Confirm satellite count >= 4 and valid latitude/longitude coordinates match true physical location.
- [ ] **[NOT VERIFIED] Zero Coordinate Rejection**: Verify that during indoor startup (no fix), coordinates (0,0) are NOT transmitted to backend.

### Step 4: MPU6050 6-Axis Motion & Fall Pipeline
- [ ] **[NOT VERIFIED] I2C Bus Detection**: Confirm MPU6050 responds at address `0x68` without bus hangs.
- [ ] **[NOT VERIFIED] Rest Calibration**: Place stick vertical. Confirm total acceleration $|a| \approx 1.00g \pm 0.05g$.
- [ ] **[NOT VERIFIED] Freefall & Impact Simulation**: Perform controlled drop onto soft cushion. Confirm state transitions:
  - `FREEFALL_CANDIDATE` ($|a| < 0.55g$)
  - `IMPACT_DETECTED` ($|a| > 2.6g$)
  - `WAITING_CONFIRMATION` (2.5s stillness window)
  - `FALL_CONFIRMED`
- [ ] **[NOT VERIFIED] False Positive Rejection**: Tap stick on floor and immediately resume walking motion. Confirm candidate event recovers to `FALSE_POSITIVE_RECOVERED` without sending emergency alert.

### Step 5: DFPlayer Mini Audio Output
- [ ] **[NOT VERIFIED] MicroSD Card Initialization**: Confirm DFPlayer recognizes FAT32 MicroSD card.
- [ ] **[NOT VERIFIED] Voice Prompt Playback**: Verify clean playback of:
  - Track 1: Obstacle close warning.
  - Track 3: Fall detected alert.
  - Track 4: SOS activated confirmation.
  - Track 7: System online chime.
- [ ] **[NOT VERIFIED] Serial Resistor Isolation**: Confirm no digital clicking or background buzzing in speaker during Wi-Fi transmission.

### Step 6: Physical SOS Button
- [ ] **[NOT VERIFIED] Debounce Check**: Press button rapidly. Confirm no double-triggers.
- [ ] **[NOT VERIFIED] Long-Press Trigger**: Hold button down for 1.2 seconds. Confirm immediate local Morse code haptic vibration and voice alert.
- [ ] **[NOT VERIFIED] Backend SOS Ingestion**: Confirm `POST /api/sos` creates row in database and sends notification.

### Step 7: AI-Thinker ESP32-CAM Node
- [ ] **[NOT VERIFIED] OV2640 Sensor Initialization**: Power on ESP32-CAM from 5V rail. Confirm camera initializes with `esp_camera_init() == ESP_OK`.
- [ ] **[NOT VERIFIED] Snapshot Capture**: Verify JPEG buffer captures clean image at QVGA (320x240).
- [ ] **[NOT VERIFIED] HTTP Inference Relay**: Confirm camera uploads frame to `/api/vision/infer` and receives structured YOLOv8n detections with valid bounding boxes.

### Step 8: Guardian Mobile App End-to-End Pairing
- [ ] **[NOT VERIFIED] Guardian Account Registration**: Register guardian account in React Native Expo app.
- [ ] **[NOT VERIFIED] Device Pairing**: Pair `STICK_001` to guardian account via `/api/guardian/devices`.
- [ ] **[NOT VERIFIED] Live Telemetry Dashboard**: Confirm real battery level, real GPS location, and genuine sensor health display on Dashboard.
- [ ] **[NOT VERIFIED] Real-Time SOS Alert**: Trigger physical stick SOS. Confirm guardian phone receives push notification and displays emergency banner in real-time.
