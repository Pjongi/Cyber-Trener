import cv2
import time
import config
from core.pose_detector import PoseDetector
from core.algorithm import Algorithm, SignalSmoother
from core.camera import ThreadedCamera  # <--- WĄTKI
from ui.visualizer import Visualizer
from ui.dashboard import CyberDashboard


def main():
    # 1. Inicjalizacja
    # Używamy configu z lżejszym modelem (core/pose_detector.py)
    detector = PoseDetector(min_conf=config.MIN_CONFIDENCE)
    visualizer = Visualizer()
    tui = CyberDashboard(width=1920, height=1080)

    joints = ["Lokiec (L)", "Lokiec (P)", "Bark (L)", "Bark (P)",
              "Biodro (L)", "Biodro (P)", "Kolano (L)", "Kolano (P)"]
    smoothers = {name: SignalSmoother(0.2) for name in joints}  # Alpha 0.2 = szybsza reakcja

    # 2. Uruchomienie kamery w tle
    print(f"Start kamery: {config.CAMERA_ID}")
    cam1 = ThreadedCamera(config.CAMERA_ID)
    cam_thread = cam1.start()

    if cam_thread is None:
        print("Krytyczny błąd kamery. Zamykanie.")
        return

    # Okno Fullscreen
    cv2.namedWindow(config.WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(config.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    prev_time = 0

    while True:
        # Odczyt z wątku (nie blokuje programu!)
        success, frame = cam1.read()

        if not success or frame is None:
            # Jeśli klatka nie dotarła, czekamy chwilkę i próbujemy dalej (nie zamykamy programu)
            time.sleep(0.01)
            continue

        # FPS
        curr_time = time.time()
        fps = 1 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
        prev_time = curr_time

        # --- DETEKCJA I ANALIZA ---
        # Zmniejszamy obraz do detekcji (przyspieszenie AI), ale wyświetlamy duży
        frame_small = cv2.resize(frame, (800, 600))
        results = detector.find_pose(frame_small)

        # Rysujemy na oryginale (frame) skalując punkty
        processed_frame = visualizer.draw_skeleton(frame, results)

        angles_data = {k: None for k in smoothers.keys()}
        status_msg = "SKANOWANIE..."

        if results.pose_landmarks:
            lm = results.pose_landmarks.landmark
            h, w, _ = frame.shape  # Wymiary oryginału

            def get_xy(i):
                return [lm[i].x * w, lm[i].y * h]

            def vis(i):
                return lm[i].visibility > 0.5

            def process(name, i1, i2, i3):
                if vis(i1) and vis(i2) and vis(i3):
                    raw = Algorithm.calculate_angle_2d(get_xy(i1), get_xy(i2), get_xy(i3))
                    val = smoothers[name].update(raw)
                    angles_data[name] = val
                    visualizer.draw_angle(processed_frame, (int(get_xy(i2)[0]), int(get_xy(i2)[1])), val)

            process("Lokiec (L)", 11, 13, 15)
            process("Lokiec (P)", 12, 14, 16)
            process("Bark (L)", 13, 11, 23)
            process("Bark (P)", 14, 12, 24)
            process("Biodro (L)", 11, 23, 25)
            process("Biodro (P)", 12, 24, 26)
            process("Kolano (L)", 23, 25, 27)
            process("Kolano (P)", 24, 26, 28)

            if angles_data["Lokiec (P)"]: status_msg = "WIDZE CIE"

        # --- GUI ---
        ui = tui.compose(processed_frame, angles_data, status_msg, fps)
        cv2.imshow(config.WINDOW_NAME, ui)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam1.stop()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()