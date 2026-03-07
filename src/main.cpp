#include <Arduino.h>
#include <ESP32Servo.h>

static constexpr int BAUD = 115200;
static constexpr int SERVO_PIN = 25;       // állítsd a sajátodra
static constexpr int SERVO_MIN = 0;
static constexpr int SERVO_MAX = 180;
static constexpr int GREEN_LED_PIN = 32;
static constexpr int RED_LED_PIN = 33;
static constexpr int BUZZER_PIN = 22;

Servo servo;
int currentDeg = 90;

static int clampInt(int v, int lo, int hi) {
  if (v < lo) return lo;
  if (v > hi) return hi;
  return v;
}

void setup() {
  Serial.begin(BAUD);

  servo.setPeriodHertz(50);
  servo.attach(SERVO_PIN, 500, 2400);  // SG90 tipikus pulse range
  servo.write(currentDeg);
  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(RED_LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  Serial.println("READY (send: A:90)");
}

void loop() {
  if (!Serial.available()) return;

  String line = Serial.readStringUntil('\n');
  line.trim();

  if (line.startsWith("A:")) {
    int angle = line.substring(2).toInt();
    angle = clampInt(angle, SERVO_MIN, SERVO_MAX);
    currentDeg = angle;
    servo.write(currentDeg);
    Serial.println("OK");
  }
  if (line == "G:1") {
    digitalWrite(RED_LED_PIN, LOW);
    digitalWrite(GREEN_LED_PIN, HIGH);
    digitalWrite(BUZZER_PIN, LOW);
  }
  if (line == "R:1") {
    digitalWrite(RED_LED_PIN, HIGH);
    digitalWrite(GREEN_LED_PIN, LOW);
    digitalWrite(BUZZER_PIN, HIGH);
  }
}