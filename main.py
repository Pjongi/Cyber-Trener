import cv2
import time
import config
from core.pose_detector import PoseDetector
from core.algorithm import Algorithm, SignalSmoother
from ui.visualizer import Visualizer
from ui.dashboard import CyberDashboard


def main():
    detector = PoseDetector(min_conf=config.MIN_CONFIDENCE)
    visualizer = Visualizer()  # ZMIANA NAZWY ZMIENNEJ DLA BEZPIECZEŃSTWA
    tui = CyberDashboard(width=1920, height=1080)

    # Inicjalizacja wygładzania dla WSZYSTKICH stawów
    joints = [
        "Lokiec (L)", "Lokiec (P)",
        "Bark (L)", "Bark (P)",
        "Biodro (L)", "Biodro (P)",
        "Kolano (L)", "Kolano (P)"
    ]
    smoothers = {name: SignalSmoother(0.15) for name in joints}

    cap = cv2.VideoCapture(config.CAMERA_ID)
    cap.set(3, 1280)
    cap.set(4, 720)

    cv2.namedWindow(config.WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(config.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    prev_frame_time = 0

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Błąd kamery.")
            break

        new_frame_time = time.time()
        fps = 1 / (new_frame_time - prev_frame_time) if (new_frame_time - prev_frame_time) > 0 else 0
        prev_frame_time = new_frame_time

        # 1. Detekcja
        results = detector.find_pose(frame)

        # Używamy zmiennej 'visualizer', nie 'vis'
        processed_frame = visualizer.draw_skeleton(frame, results)

        # Domyślnie brak danych
        current_angles = {k: None for k in smoothers.keys()}
        status_msg = "SZUKAM..."

        if results.pose_landmarks:
            lm = results.pose_landmarks.landmark
            h, w, _ = frame.shape

            def get_coords(i):
                return [lm[i].x * w, lm[i].y * h]

            # POPRAWKA: Zmiana nazwy funkcji na 'check_vis'
            def check_vis(i):
                return lm[i].visibility > 0.5

            # Funkcja pomocnicza: Licz i wygładź jeśli punkty widoczne
            def calc_and_smooth(name, i1, i2, i3):
                if check_vis(i1) and check_vis(i2) and check_vis(i3):
                    raw = Algorithm.calculate_angle_2d(get_coords(i1), get_coords(i2), get_coords(i3))
                    val = smoothers[name].update(raw)
                    current_angles[name] = val

                    # Opcjonalnie: Rysuj kąt na obrazie wideo
                    visualizer.draw_angle(processed_frame, (int(get_coords(i2)[0]), int(get_coords(i2)[1])), val)
                    return val
                return None

            # --- OBLICZENIA ---
            # RĘCE
            calc_and_smooth("Lokiec (L)", 11, 13, 15)
            calc_and_smooth("Lokiec (P)", 12, 14, 16)

            calc_and_smooth("Bark (L)", 13, 11, 23)
            calc_and_smooth("Bark (P)", 14, 12, 24)

            # NOGI
            calc_and_smooth("Biodro (L)", 11, 23, 25)
            calc_and_smooth("Biodro (P)", 12, 24, 26)

            calc_and_smooth("Kolano (L)", 23, 25, 27)
            calc_and_smooth("Kolano (P)", 24, 26, 28)

            # --- STATUS ---
            if current_angles["Lokiec (P)"] is not None:
                angle = current_angles["Lokiec (P)"]
                if angle > 160:
                    status_msg = "PRAWA: PROSTA"
                elif angle < 90:
                    status_msg = "PRAWA: ZGIETA"
                else:
                    status_msg = "PRAWA: RUCH"
            elif current_angles["Lokiec (L)"] is not None:
                angle = current_angles["Lokiec (L)"]
                if angle > 160:
                    status_msg = "LEWA: PROSTA"
                else:
                    status_msg = "LEWA: RUCH"
            else:
                status_msg = "WIDZE SYLWETKE"

        else:
            status_msg = "BRAK CELU"

        # Generowanie UI
        final_interface = tui.compose(
            frame_main=processed_frame,
            angles_dict=current_angles,
            status=status_msg,
            fps=fps
        )

        cv2.imshow(config.WINDOW_NAME, final_interface)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()