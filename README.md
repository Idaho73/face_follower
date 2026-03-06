# 🎯 ESP32 Serial Face Tracking

A high-performance face-tracking system that uses **Python (MediaPipe)** for computer vision and an **ESP32** to control a servo motor via **Serial (USB)** communication.

---

## 🔌 Hardware Setup

| Component | ESP32 Pin | Notes |
| :--- | :--- | :--- |
| **Servo Signal (Yellow)** | **GPIO 25** | Configurable in `main.cpp` |
| **Servo VCC (Red)** | **5V** | Use a stable 5V source (e.g., Arduino 5V pin) |
| **Servo GND (Brown)** | **GND** | **Crucial:** Must share a common ground with ESP32 |

> **Pro Tip:** If the servo vibrates or resets the ESP32, add a **100µF - 470µF capacitor** between the Servo VCC and GND to smooth out current spikes.

---

## ⚙️ Software Installation

### 1. ESP32 Firmware
* Install the **ESP32Servo** library in your Arduino IDE or PlatformIO.
* Flash the provided code to your ESP32.
* The board is configured for **115200 Baud**.

### 2. Python Environment
Install the required libraries using pip:
```bash
pip install mediapipe opencv-python pyserial
```

# 🤖 Control Logic: The "Comfort Zone"

This system implements a **Deadzone (0.4 - 0.6)**. Instead of constantly fighting to keep the face at exactly $x=0.5$, the motor remains idle as long as the face stays within the center 20% of the frame. This prevents jitter and reduces motor wear.

### How it works:
* **$x < 0.4$**: Face moved too far left $\rightarrow$ Servo adjusts left.
* **$0.4 < x < 0.6$**: Face is in the Comfort Zone $\rightarrow$ **Servo holds position**.
* **$x > 0.6$**: Face moved too far right $\rightarrow$ Servo adjusts right.

### Mathematical Error Calculation:
The error ($err$) is calculated relative to the boundaries of the comfort zone:

$$err = \begin{cases} x_{norm} - 0.6 & \text{if } x_{norm} > 0.6 \\ x_{norm} - 0.4 & \text{if } x_{norm} < 0.4 \\ 0 & \text{otherwise} \end{cases}$$

---

# 🚀 Usage

1.  **Connect** your ESP32 to your PC via USB.
2.  **Identify** your Serial Port (e.g., `COM8` on Windows or `/dev/ttyUSB0` on Linux).
3.  **Ensure** the `SERIAL_PORT` variable in your Python script matches your port.
4.  **Run** the tracking script:

```bash
python track_center.py
```

## 🛠️ Tuning Parameters

You can fine-tune the behavior in the Python script:



| Parameter | Default | Effect |
| :--- | :--- | :--- |
| **KP** | 40 | **Proportional Gain:** Higher values make the motor move faster. |
| **KI** | 2 | **Integral Gain:** Helps the motor "reach" the zone edge if it gets stuck. |
| **EMA** | 0.35 | **Smoothing:** Lower values reduce jitter but add slight delay. |
| **MAX_STEP_DEG** | 3 | **Speed Limit:** Prevents the servo from moving too violently. |