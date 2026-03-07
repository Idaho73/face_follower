#include <Arduino.h>
#include <ESP32Servo.h>
#include <IRremote.hpp>

static constexpr int BAUD = 115200;
static constexpr int SERVO_PIN = 25;       // állítsd a sajátodra
static constexpr int SERVO_MIN = 0;
static constexpr int SERVO_MAX = 180;
static constexpr int GREEN_LED_PIN = 32;
static constexpr int RED_LED_PIN = 33;
static constexpr int BUZZER_PIN = 22;
static constexpr int IR_RECEIVE_PIN = 27;

static constexpr uint8_t CMD_ZOOM_OUT  = 0x07;
static constexpr uint8_t CMD_ZOOM_IN   = 0x15;
static constexpr uint8_t CMD_ZOOM_RESET = 0x08;
static constexpr uint8_t CMD_FACE_DETECT = 0x09;

static constexpr uint8_t CMD_RIGHT = 0x040;
static constexpr uint8_t CMD_LEFT = 0x044;
static constexpr uint8_t CMD_RIGHT_LITTLE = 0x046;
static constexpr uint8_t CMD_LEFT_LITTLE = 0x045;

static constexpr uint8_t CMD_PHOTO = 0x043;

static bool DISABLE_FACE_DETECT = true;

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

  IrReceiver.begin(IR_RECEIVE_PIN, DISABLE_LED_FEEDBACK);

  Serial.println("READY (send: A:90)");
}

void handleSerialCommand(const String& line) {
  if (line.startsWith("A:")) {
    int angle = line.substring(2).toInt();
    angle = clampInt(angle, SERVO_MIN, SERVO_MAX);
    currentDeg = angle;
    servo.write(currentDeg);
    Serial.println("OK");
  }
  else if (line.startsWith("F:")) {
    // Ez csak visszajelzés a PC-ről, hogy a face detect be van-e kapcsolva
    String state = line.substring(2);
    DISABLE_FACE_DETECT = (state == "1") ? false : true; // Fordítva, mert a DISABLE_FACE_DETECT logika fordított
    Serial.print("Face Detect is now: ");
    Serial.println(state == "1" ? "ON" : "OFF");
  }
  else {
    Serial.println("Unknown command");
  }
}

void handleIR() {
  if (!IrReceiver.decode()) return;

  auto data = IrReceiver.decodedIRData;

  // Debug: ezzel meg tudod nézni, melyik gomb milyen command értéket ad
  Serial.print("IR protocol=");
  Serial.print(getProtocolString(data.protocol));
  Serial.print(" address=0x");
  Serial.print(data.address, HEX);
  Serial.print(" command=0x");
  Serial.println(data.command, HEX);

  if (!(data.flags & IRDATA_FLAGS_IS_REPEAT)) {
    if (data.command == CMD_ZOOM_IN) {
      Serial.println("Z:IN");
    }
    else if (data.command == CMD_ZOOM_OUT) {
      Serial.println("Z:OUT");
    }
    else if (data.command == CMD_ZOOM_RESET) {
      Serial.println("Z:RESET");
    }
    else if (data.command == CMD_FACE_DETECT) {
      Serial.println("Z:FACE_DETECT");
    }
    else if (data.command == CMD_PHOTO) {
      Serial.println("P:START");
    }
    if (DISABLE_FACE_DETECT) {
      Serial.println("Face detect is disabled, ignoring direction commands.");
      if (data.command == CMD_RIGHT) {
        currentDeg = clampInt(currentDeg + 10, SERVO_MIN, SERVO_MAX);
        servo.write(currentDeg);
      }
      else if (data.command == CMD_LEFT) {
        currentDeg = clampInt(currentDeg - 10, SERVO_MIN, SERVO_MAX);
        servo.write(currentDeg);
      }
      else if (data.command == CMD_RIGHT_LITTLE) {
        currentDeg = clampInt(currentDeg + 2, SERVO_MIN, SERVO_MAX);
        servo.write(currentDeg);
      }
      else if (data.command == CMD_LEFT_LITTLE) {
        currentDeg = clampInt(currentDeg - 2, SERVO_MIN, SERVO_MAX);
        servo.write(currentDeg);
      }
    }

  }

  IrReceiver.resume();
}

void loop() {
  handleIR();

  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.length() > 0) {
      handleSerialCommand(line);
    }
  }
  if (DISABLE_FACE_DETECT) {
    digitalWrite(RED_LED_PIN, HIGH);
    digitalWrite(GREEN_LED_PIN, LOW);
    digitalWrite(BUZZER_PIN, HIGH);
  }
  else {
    digitalWrite(RED_LED_PIN, LOW);
    digitalWrite(GREEN_LED_PIN, HIGH);
    digitalWrite(BUZZER_PIN, LOW);
  }
}