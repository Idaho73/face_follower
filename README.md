
# 🎯 ESP32 Serial Face Tracking

A high‑performance face‑tracking system that uses **Python (MediaPipe)** for computer vision and an **ESP32** to control a servo motor via **Serial (USB)** communication.

The system can:
- Track a face and keep it centered with a servo motor
- Zoom the camera digitally using a **remote control**
- Take a **photo after a 3‑second delay** using a remote button
- Display a **visual countdown** and **camera flash effect** when a photo is taken

---

# 🔌 Hardware Setup

| Component | ESP32 Pin | Notes |
| :--- | :--- | :--- |
| **Servo Signal (Yellow)** | **GPIO 25** | Configurable in `main.cpp` |
| **Servo VCC (Red)** | **5V** | Use a stable 5V source |
| **Servo GND (Brown)** | **GND** | Must share ground with ESP32 |
| **IR Receiver OUT** | **GPIO 27** | Used for remote control |
| **Green LED** | **GPIO 32** | Indicates face centered |
| **Red LED** | **GPIO 33** | Indicates face outside zone |
| **Buzzer** | **GPIO 22** | Audible feedback |

<img width="704" height="380" alt="image" src="https://github.com/user-attachments/assets/a39b7da9-49ae-4e94-bcdc-fa7a88aaa8e2" />


⚠️ **Important:** Servo and ESP32 must share a common ground.

If the servo causes resets, place a **100µF – 470µF capacitor** between **Servo VCC and GND**.

---

# ⚙️ Software Installation

## 1. ESP32 Firmware

Required libraries:

- `ESP32Servo`
- `IRremote`

PlatformIO example:

```
lib_deps =
    madhephaestus/ESP32Servo
    IRremote
```

Upload the firmware to the ESP32.

Serial communication speed:

```
115200 baud
```

---

## 2. Python Environment

Install dependencies:

```bash
pip install mediapipe opencv-python pyserial
```

---

# 🤖 Face Tracking Logic – Comfort Zone

Instead of constantly forcing the face to the exact center, the system uses a **deadzone (comfort zone)**.

```
ZONE_LEFT  = 0.4
ZONE_RIGHT = 0.6
```

This means the face can move freely within the **center 20% of the frame** without moving the servo.

### Behavior

| Face Position | Servo Action |
|---|---|
| x < 0.4 | Rotate left |
| 0.4 < x < 0.6 | Hold position |
| x > 0.6 | Rotate right |

Error calculation:

err = x_norm - 0.6 if x_norm > 0.6  
err = x_norm - 0.4 if x_norm < 0.4  
err = 0 otherwise

This prevents jitter and reduces servo wear.

---

# 🎮 Remote Control Features

The IR remote can control additional features.

### 🔎 Camera Zoom

Buttons can send:

```
Z:IN
Z:OUT
Z:RESET
```

Python receives these commands and performs **digital zoom** on the camera image.

Zoom range:

```
1.0x – 3.0x
```

Digital zoom is implemented by cropping the frame center and resizing it back to full resolution.

---

# 📸 Remote Photo Capture

A dedicated remote button sends:

```
P:START
```

When Python receives this command:

1️⃣ A **3‑second countdown** starts  
2️⃣ Countdown is displayed on screen  
3️⃣ The image is saved automatically  
4️⃣ A **white flash effect** simulates a camera shutter

Saved images are stored in:

```
/photos/
```

File format:

```
photo_YYYYMMDD_HHMMSS.jpg
```

Example:

```
photo_20260307_142530.jpg
```

---

# 💡 Visual Feedback

When a photo is taken:

- Large **countdown numbers** appear
- A **white screen flash** occurs
- A message confirms the photo was saved

This gives the system a **camera‑like behavior**.

---

# 🚀 Usage

1. Connect ESP32 via USB
2. Identify the serial port

Examples:

Windows

```
COM8
```

Linux

```
/dev/ttyUSB0
```

3. Set the port in the Python script:

```python
SERIAL_PORT = "COM8"
```

4. Run the program:

```bash
python track_center.py
```

---

# 🛠️ Tuning Parameters

These parameters control motor behavior.

| Parameter | Default | Description |
|---|---|---|
| **KP** | 40 | Proportional control strength |
| **KI** | 2 | Integral correction |
| **EMA** | 0.35 | Signal smoothing |
| **MAX_STEP_DEG** | 3 | Maximum servo step per cycle |

Lower **EMA** = smoother but slower response.

Higher **KP** = faster but more aggressive movement.

---

# 📂 Project Structure

```
project/
│
├── src/
│   └── main.cpp
│
├── track_center.py
│
├── photos/
│
└── README.md
```

---

# 🧠 System Overview

Camera → Python (MediaPipe) → Face detection  
Python → Serial → ESP32  
ESP32 → Servo motor control

Remote control → ESP32 → Serial → Python

---

# 📷 Features Summary

✔ Face tracking with servo motor  
✔ Comfort zone deadband control  
✔ Remote‑controlled zoom  
✔ Remote‑triggered photo capture  
✔ 3‑second countdown overlay  
✔ Camera flash effect  
✔ Automatic photo saving  

---

# 🏁 Future Ideas

Possible upgrades:

• automatic face re‑centering  
• multi‑face selection  
• auto zoom based on face distance  
• WiFi streaming interface  
• mobile app control  

---

Built with:

**ESP32 • Python • OpenCV • MediaPipe**
