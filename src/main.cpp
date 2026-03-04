#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <LittleFS.h>
#include <ESP32Servo.h>

#include "config.h"

WebServer server(80);
Servo servo;

static int clampInt(int v, int lo, int hi) {
  if (v < lo) return lo;
  if (v > hi) return hi;
  return v;
}

static int currentDeg = SERVO_CENTER_DEG;

// --- Web handlers ---
void handleIndex() {
  File f = LittleFS.open("/index.html", "r");
  if (!f) {
    server.send(500, "text/plain", "index.html missing (upload LittleFS)");
    return;
  }
  server.streamFile(f, "text/html");
  f.close();
}

void handleAngle() {
  if (!server.hasArg("v")) {
    server.send(400, "text/plain", "Missing v");
    return;
  }

  int v = server.arg("v").toInt();
  v = clampInt(v, SERVO_MIN_DEG, SERVO_MAX_DEG);

  currentDeg = v;
  servo.write(currentDeg);

  server.send(200, "text/plain", "OK");
}

void handleCenter() {
  currentDeg = clampInt(SERVO_CENTER_DEG, SERVO_MIN_DEG, SERVO_MAX_DEG);
  servo.write(currentDeg);
  server.send(200, "text/plain", "OK");
}

void handleNudge() {
  if (!server.hasArg("dir")) {
    server.send(400, "text/plain", "Missing dir");
    return;
  }
  int dir = server.arg("dir").toInt(); // -1 vagy +1

  // “léptetés” fokban – állítsd a saját igényedre
  const int stepDeg = 2;

  currentDeg = clampInt(currentDeg + dir * stepDeg, SERVO_MIN_DEG, SERVO_MAX_DEG);
  servo.write(currentDeg);

  server.send(200, "text/plain", "OK");
}

void setup() {
  Serial.begin(115200);

  // FS
  if (!LittleFS.begin(true)) {
    Serial.println("LittleFS mount failed");
  }

  // WiFi AP
  WiFi.mode(WIFI_AP);
  WiFi.softAP(WIFI_AP_SSID, WIFI_AP_PASS);
  Serial.print("AP IP: ");
  Serial.println(WiFi.softAPIP());

  // Servo init (ESP32-n fontos a PWM timer)
  servo.setPeriodHertz(50); // tipikusan 50Hz, de írd be te
  servo.attach(SERVO_PIN, 500, 2400);
  servo.write(currentDeg);

  // Routes
  server.on("/", handleIndex);
  server.on("/angle", handleAngle);
  server.on("/center", handleCenter);
  server.on("/nudge", handleNudge);

  server.begin();
  Serial.println("HTTP server started");
}

void loop() {
  server.handleClient();
}