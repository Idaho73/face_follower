#pragma once

// Wi-Fi AP (telefon erről csatlakozik)
#define WIFI_AP_SSID "ESP32-Servo"
#define WIFI_AP_PASS "password123"   // min 8 char

// Servo pin (ESP32 GPIO, olyan, ami nem strap-pin)
#define SERVO_PIN 25

// Servo szög határok (SG90-nél érdemes óvatosan)
#define SERVO_MIN_DEG 0
#define SERVO_MAX_DEG 180
#define SERVO_CENTER_DEG 90