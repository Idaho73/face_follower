# ESP32 Servo Web Control

Simple ESP32 project to control an **SG90 servo motor from a phone via Wi-Fi**.
The ESP32 creates its own Wi-Fi network and hosts a small web interface where the servo can be moved left, right, centered, or controlled with a slider.

This project is the first step toward a **face-tracking camera system**.

---

# Features

* ESP32 creates its own Wi-Fi access point
* Simple web UI to control the servo
* Works from any phone browser
* Built with **PlatformIO + Arduino framework**
* Designed to be easily extended (e.g. face tracking)

---

# Hardware

Required components:

* ESP32 development board
* SG90 servo motor
* Arduino board (used as 5V power supply)
* 12V battery for the Arduino
* jumper wires

---

# Wiring

Servo connections:

| Servo wire    | Connect to                            |
| ------------- | ------------------------------------- |
| Brown         | GND                                   |
| Red           | 5V (from Arduino board)               |
| Yellow/Orange | ESP32 GPIO (configured in `config.h`) |

Important:

* The **servo is powered from the Arduino 5V pin**
* The **ESP32 and Arduino GND must be connected together**

Example:

ESP32 GPIO → Servo signal
Arduino 5V → Servo VCC
Arduino GND → Servo GND
ESP32 GND → Arduino GND

---

# Software Setup

## 1. Install tools

Install:

* **VS Code**
* **PlatformIO extension**

---

## 2. Clone the project

---

## 3. Configure the project

Edit:

```
include/config.h
```

Set:

* Wi-Fi name
* Wi-Fi password
* Servo pin
* Servo limits

Example:

```
#define WIFI_AP_SSID "ESP32-Servo"
#define WIFI_AP_PASS "password123"

#define SERVO_PIN 25
#define SERVO_MIN_DEG 0
#define SERVO_MAX_DEG 180
#define SERVO_CENTER_DEG 90
```

---

## 4. Upload the filesystem (web UI)

The web interface is stored in **LittleFS**.

Run:

```bash
pio run -t uploadfs
```

---

## 5. Upload firmware

```bash
pio run -t upload
```

---

# Usage

1. Power the ESP32
2. Connect your phone to the Wi-Fi network:

```
ESP32-Servo
```

3. Open your browser and navigate to:

```
192.168.4.1
```

4. Use the buttons or slider to move the servo.

---

## Face Tracking (New Feature)

The project now includes a **basic face tracking system**.

A Python script detects a face using the camera and automatically moves the servo so that the face stays in the **center of the camera image**.

The system works as follows:

```
Camera → Face Detection → X position of face → Control algorithm → ESP32 → Servo motor
```

The servo continuously adjusts its angle until the detected face is centered in the frame.

---

## How It Works

1. The Python script captures frames from the camera.
2. MediaPipe detects the face.
3. The **horizontal center of the face** is calculated.
4. The difference between the face position and the image center is computed:

```
error = face_x - 0.5
```

5. A control algorithm (PI controller) calculates the required servo movement.
6. The target servo angle is sent to the ESP32 through **Serial (USB)**.

---

## Required Python Dependencies

Install the required packages:

```bash
pip install mediapipe opencv-python pyserial
```

---

## Running Face Tracking

1. Upload the firmware to the ESP32:

```bash
pio run -t upload
```

2. Make sure the ESP32 stays connected via USB.

3. Close any Serial Monitor.

4. Run the tracking script:

```bash
python track_center.py
```

---

## Camera Setup

The camera can be:

* a USB webcam
* an external camera
* a capture device

If the camera does not start, change the index in the script:

```python
cap = cv2.VideoCapture(0)
```

Try values `1` or `2` if necessary.

---

## Servo Control Algorithm

The control system keeps the face centered by minimizing the error:

```
error = x_norm - 0.5
```

Where:

| Value | Meaning            |
| ----- | ------------------ |
| 0.0   | face at left edge  |
| 0.5   | face centered      |
| 1.0   | face at right edge |

The algorithm uses:

* **Proportional control (P)** for fast movement
* **Integral control (I)** to remove small steady errors
* **Deadzone** to prevent jitter
* **Exponential smoothing** for stability
* **Step limiting** to prevent oscillation

---

## Tuning Parameters

The following parameters can be adjusted in the Python script:

| Parameter      | Purpose                     |
| -------------- | --------------------------- |
| `KP`           | responsiveness of tracking  |
| `KI`           | correction of steady errors |
| `DEADZONE`     | prevents small jitter       |
| `EMA`          | smoothing factor            |
| `MAX_STEP_DEG` | limits servo speed          |

Typical stable values:

```
KP = 35
KI = 8
DEADZONE = 0.06
EMA = 0.25
MAX_STEP_DEG = 2
```

---

## Hardware Notes

For stable operation:

* The servo should be powered from a **stable 5V source**
* The **ESP32 and servo power supply must share a common GND**
* Adding a **100–470µF capacitor** near the servo can reduce jitter

---

## Next Planned Improvements

Future versions of the project may include:

* full **pan–tilt camera mount**
* **multiple face tracking**
* running detection directly on an **ESP32-CAM**
* mobile application control


# License

MIT License
