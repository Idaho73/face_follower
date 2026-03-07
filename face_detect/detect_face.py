import time
import cv2
import mediapipe as mp
import serial

# --- KONFIGURÁCIÓ ---
SERIAL_PORT = "COM8"
BAUD = 115200

SERVO_MIN = 10
SERVO_MAX = 350
SERVO_START = 90

# PI Szabályzó paraméterek
KP = 40              # Arányos tag (mennyire gyorsan induljon meg)
KI = 2               # Integrál tag (lassú finomhangolás a zóna széléhez)
EMA = 0.35           # Hibajel szűrése (0.1 - 1.0 között, minél kisebb, annál simább)
MAX_STEP_DEG = 3     # Maximális elmozdulás egy ciklus alatt (fok)

SEND_HZ = 40         # Küldési gyakoriság (Hz)
NO_FACE_HOLD_SEC = 1.0

# Zóna határai (0.0 - 1.0 skálán)
ZONE_LEFT = 0.4
ZONE_RIGHT = 0.6

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def main():
    # Soros port inicializálása
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD, timeout=0.1)
        time.sleep(2) # Várunk az Arduino újraindulására
    except Exception as e:
        print(f"Hiba a soros porttal: {e}")
        return

    cap = cv2.VideoCapture(1) # Próbáld a 0-át, ha az 1 nem működik
    if not cap.isOpened():
        raise RuntimeError("Kamera nem található")

    det = mp.solutions.face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.6)

    angle = SERVO_START
    err_f = 0.0
    integ = 0.0
    last_t = time.time()
    last_send = 0.0
    last_sent = None

    print("Fut a követés... Kilépés: ESC")

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        frame = cv2.flip(frame, 1) # Tükrözés, hogy természetes legyen a mozgás
        h, w = frame.shape[:2]

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = det.process(rgb)

        face_found = False
        current_err = 0.0

        if res.detections:
            # Legnagyobb arc kiválasztása
            best = max(res.detections, key=lambda d: d.location_data.relative_bounding_box.width * d.location_data.relative_bounding_box.height)
            
            b = best.location_data.relative_bounding_box
            cx_norm = b.xmin + (b.width / 2) # Arc közepének relatív X pozíciója
            
            # --- ZÓNA LOGIKA ---
            if cx_norm > ZONE_RIGHT:
                current_err = cx_norm - ZONE_RIGHT # Pozitív hiba (jobbra kell menni)
            elif cx_norm < ZONE_LEFT:
                current_err = cx_norm - ZONE_LEFT  # Negatív hiba (balra kell menni)
            else:
                current_err = 0.0  # Zónán belül vagyunk
                integ = 0.0        # Reseteljük az integrált a zónában a túlfutás ellen

            face_found = True
            last_face_t = time.time()

            # Megjelenítés
            bx, by = int(b.xmin * w), int(b.ymin * h)
            bw, bh = int(b.width * w), int(b.height * h)
            cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), (0, 255, 0), 2)
            cv2.circle(frame, (int(cx_norm * w), by + bh // 2), 5, (0, 255, 0), -1)

        # Időmérés a szabályzóhoz
        now = time.time()
        dt = max(1e-3, now - last_t)
        last_t = now

        if face_found:
            # Szűrt hibajel (EMA) a rángatózás ellen
            err_f = (1 - EMA) * err_f + EMA * current_err
            
            # Integrál számítása
            integ += err_f * dt
            integ = clamp(integ, -0.2, 0.2) # Anti-windup

            # PI szabályzó kimenete
            # Ha a motor fordítva mozog, tegyél egy mínusz jelet a zárójel elé!
            control_signal = (KP * err_f + KI * integ)

            # Sebességkorlát és szervó állítás
            step = clamp(control_signal, -MAX_STEP_DEG, MAX_STEP_DEG)
            angle = clamp(angle + step, SERVO_MIN, SERVO_MAX)

            # Küldés az Arduinonak (ha változott az érték)
            if (now - last_send) >= (1.0 / SEND_HZ):
                target_angle = int(round(angle))
                if target_angle != last_sent:
                    ser.write(f"A:{target_angle}\n".encode())
                    last_sent = target_angle
                last_send = now
        
            if (current_err == 0.0):
                ser.write(f"G:1\n".encode()) # Zónában vagyunk
            else:
                ser.write(f"R:1\n".encode()) # Zónán kívül vagyunk

        # --- VIZUÁLIS SEGÉDLETEK ---
        # Zóna határok rajzolása (0.4 és 0.6)
        cv2.line(frame, (int(ZONE_LEFT * w), 0), (int(ZONE_LEFT * w), h), (255, 0, 0), 2)
        cv2.line(frame, (int(ZONE_RIGHT * w), 0), (int(ZONE_RIGHT * w), h), (255, 0, 0), 2)
        
        status_color = (0, 255, 0) if face_found and current_err == 0 else (0, 0, 255)
        cv2.putText(frame, f"Ang: {int(angle)} | Err: {err_f:.2f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

        cv2.imshow("Face Tracking Zone", frame)
        if (cv2.waitKey(1) & 0xFF) == 27: # ESC a kilépéshez
            break

    cap.release()
    cv2.destroyAllWindows()
    ser.close()

if __name__ == "__main__":
    main()