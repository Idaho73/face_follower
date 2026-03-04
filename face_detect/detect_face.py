import time
import cv2
import mediapipe as mp
import serial

SERIAL_PORT = "COM8"
BAUD = 115200

SERVO_MIN = 10
SERVO_MAX = 170
SERVO_START = 90

DEADZONE = 0.06      # ha ennyin belül van, nem mozog
EMA = 0.25           # err szűrés

KP = 35              # arányos tag (kezdő)
KI = 8               # integrál tag (kezdő) -> ettől lesz "pont középen"
INTEGRAL_CLAMP = 0.25  # integrál korlát (képarányban)

MAX_STEP_DEG = 2     # max fok változás ciklusonként
SEND_HZ = 20

NO_FACE_HOLD_SEC = 1.0

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def main():
    ser = serial.Serial(SERIAL_PORT, BAUD, timeout=0.1)
    time.sleep(1.2)

    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        raise RuntimeError("Camera not found")

    det = mp.solutions.face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.6)

    angle = SERVO_START
    err_f = 0.0
    integ = 0.0
    last_t = time.time()
    last_send = 0.0
    last_sent = None
    last_face_t = 0.0

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = det.process(rgb)

        face_found = False
        err = 0.0

        if res.detections:
            # legnagyobb arc
            best = None
            best_area = 0.0
            for d in res.detections:
                b = d.location_data.relative_bounding_box
                area = b.width * b.height
                if area > best_area:
                    best_area = area
                    best = b

            if best:
                x = int(best.xmin * w)
                y = int(best.ymin * h)
                bw = int(best.width * w)
                bh = int(best.height * h)

                cx = x + bw // 2
                cy = y + bh // 2

                x_norm = cx / w
                err = x_norm - 0.5
                face_found = True
                last_face_t = time.time()

                cv2.rectangle(frame, (x, y), (x + bw, y + bh), (255, 255, 255), 2)
                cv2.circle(frame, (cx, cy), 5, (255, 255, 255), -1)
                cv2.putText(frame, f"x={x_norm:.3f}", (x, max(20, y - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.line(frame, (w//2, 0), (w//2, h), (255, 255, 255), 1)

        now = time.time()
        dt = max(1e-3, now - last_t)
        last_t = now

        # ha nincs arc, ne vadásszon
        if (not face_found) and (now - last_face_t) > NO_FACE_HOLD_SEC:
            cv2.putText(frame, "NO FACE", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            # opcionális: integ lassú lecsengés
            integ *= 0.95
        else:
            # deadzone
            if abs(err) < DEADZONE:
                err = 0.0

            # err szűrés
            err_f = (1 - EMA) * err_f + EMA * err

            # integrál (anti-windup)
            integ += err_f * dt
            integ = clamp(integ, -INTEGRAL_CLAMP, INTEGRAL_CLAMP)

            # PI kimenet: ez "mennyi fokot lépjünk" jellegű
            # Ha fordítva mozog a szervó, cseréld meg az előjelet itt:
            control = +(KP * err_f + KI * integ)

            # rate limit
            step = clamp(control, -MAX_STEP_DEG, MAX_STEP_DEG)
            angle = clamp(angle + step, SERVO_MIN, SERVO_MAX)

            # küldés
            if (now - last_send) >= (1.0 / SEND_HZ):
                a = int(round(angle))
                if last_sent is None or abs(a - last_sent) >= 1:
                    ser.write(f"A:{a}\n".encode("utf-8"))
                    last_sent = a
                last_send = now

            cv2.putText(frame, f"err={err_f:+.3f} ang={int(angle)}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        cv2.imshow("Keep Face Centered", frame)
        if (cv2.waitKey(1) & 0xFF) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    ser.close()

if __name__ == "__main__":
    main()