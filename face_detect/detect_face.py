import time
import cv2
import mediapipe as mp
import serial
import os
from datetime import datetime

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

ZOOM_MIN = 1.0
ZOOM_MAX = 3.0
ZOOM_STEP = 0.1
ZOOM_START = 1.0

FACE_DETECT = False

PHOTO_DELAY_SEC = 3.0
SAVE_DIR = "photos"

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def main():
    # Soros port inicializálása
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD, timeout=0.1)
        time.sleep(2) # Várunk az Arduino újraindulására
        ser.reset_input_buffer()
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
    zoom_factor = ZOOM_START

    photo_requested = False
    photo_start_time = None
    photo_flash_until = 0.0
    last_saved_path = ""

    print("Fut a követés... Kilépés: ESC")

    while True:
        zoom_factor, photo_requested, photo_start_time = handle_incoming_serial(
            ser, zoom_factor, photo_requested, photo_start_time
        )

        ok, frame = cap.read()
        if not ok:
            break

        frame = apply_digital_zoom(frame, zoom_factor)
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]

        #frame = cv2.flip(frame, 1) # Tükrözés, hogy természetes legyen a mozgás
        #h, w = frame.shape[:2]

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = det.process(rgb)

        face_found = False
        current_err = 0.0

        countdown_text = None

        if photo_requested and photo_start_time is not None:
            elapsed = now - photo_start_time
            remaining = PHOTO_DELAY_SEC - elapsed

            if remaining > 0:
                countdown_text = str(int(remaining) + 1)
            else:
                photo_path = save_photo(frame)
                last_saved_path = photo_path
                print(f"Kép elmentve: {photo_path}")

                photo_requested = False
                photo_start_time = None
                photo_flash_until = now + 0.20

        if FACE_DETECT and res.detections:
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
            #cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), (0, 255, 0), 2)
            #cv2.circle(frame, (int(cx_norm * w), by + bh // 2), 5, (0, 255, 0), -1)

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

        # --- VIZUÁLIS SEGÉDLETEK ---
        # Zóna határok rajzolása (0.4 és 0.6)
        #cv2.line(frame, (int(ZONE_LEFT * w), 0), (int(ZONE_LEFT * w), h), (255, 0, 0), 2)
        #cv2.line(frame, (int(ZONE_RIGHT * w), 0), (int(ZONE_RIGHT * w), h), (255, 0, 0), 2)
        
        status_color = (0, 255, 0) if face_found and current_err == 0 else (0, 0, 255)
        cv2.putText(frame, f"Ang: {int(angle)} | Err: {err_f:.2f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        cv2.putText(frame, f"Zoom: {zoom_factor:.1f}x", (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.putText(frame, f"Face Detect: {'ON' if FACE_DETECT else 'OFF'}", (10, 90),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        if countdown_text is not None:
            cv2.putText(frame, countdown_text, (w // 2 - 30, h // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 3.0, (0, 255, 255), 5)
            cv2.putText(frame, "Foto keszul...", (w // 2 - 140, h // 2 + 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
            
        if now < photo_flash_until:
            white = frame.copy()
            white[:] = 255
            frame = cv2.addWeighted(white, 0.6, frame, 0.4, 0)
        
        cv2.imshow("Face Tracking Zone", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:   # ESC
            break
        elif key == ord('+') or key == ord('='):
            zoom_factor = min(3.0, zoom_factor + 0.1)
        elif key == ord('-') or key == ord('_'):
            zoom_factor = max(1.0, zoom_factor - 0.1)

    cap.release()
    cv2.destroyAllWindows()
    ser.close()

def apply_digital_zoom(frame, zoom_factor=1.0):
    if zoom_factor <= 1.0:
        return frame

    h, w = frame.shape[:2]
    new_w = int(w / zoom_factor)
    new_h = int(h / zoom_factor)

    x1 = (w - new_w) // 2
    y1 = (h - new_h) // 2
    x2 = x1 + new_w
    y2 = y1 + new_h

    cropped = frame[y1:y2, x1:x2]
    zoomed = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)
    return zoomed

def handle_incoming_serial(ser, zoom_factor, photo_requested, photo_start_time):
    while ser.in_waiting:
        try:
            line = ser.readline().decode(errors="ignore").strip()
        except Exception:
            break

        if not line:
            continue

        if line == "Z:IN":
            zoom_factor = clamp(zoom_factor + ZOOM_STEP, ZOOM_MIN, ZOOM_MAX)
            print(f"Zoom in -> {zoom_factor:.1f}x")
        elif line == "Z:OUT":
            zoom_factor = clamp(zoom_factor - ZOOM_STEP, ZOOM_MIN, ZOOM_MAX)
            print(f"Zoom out -> {zoom_factor:.1f}x")
        elif line == "Z:RESET":
            zoom_factor = ZOOM_START
            print(f"Zoom reset -> {zoom_factor:.1f}x")
        elif line == "Z:FACE_DETECT":
            global FACE_DETECT
            FACE_DETECT = not FACE_DETECT
            ser.write(f"F:{1 if FACE_DETECT else 0}\n".encode()) # Visszajelzés az Arduinonak
            print(f"Face detection toggled -> {'ON' if FACE_DETECT else 'OFF'}")
        elif line == "P:START":
            if not photo_requested:
                photo_requested = True
                photo_start_time = time.time()
                print("Fotó indul, 3 másodperc múlva készül kép.")
        else:
            print(f"ESP: {line}")

    return zoom_factor, photo_requested, photo_start_time

def ensure_save_dir():
    os.makedirs(SAVE_DIR, exist_ok=True)

def save_photo(frame):
    ensure_save_dir()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(SAVE_DIR, f"photo_{ts}.jpg")
    cv2.imwrite(path, frame)
    return path

if __name__ == "__main__":
    main()

