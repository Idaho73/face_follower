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

# Project Roadmap

Future improvements:

* Face detection
* Automatic camera tracking
* Pan/tilt mount with two servos
* Mobile app control

---

# License

MIT License
C:\Users\gergo.LOQI\Documents\PlatformIO\Projects\face_follower\README.md