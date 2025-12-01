import cv2
import time
import sys
import config
from core.pose_detector import PoseDetector
from core.algorithm import Algorithm, SignalSmoother
from core.camera_stream import CameraStream
from ui.visualizer import Visualizer
from ui.dashboard import CyberDashboard


def main():
    print("URUCHAMIANIE CYBER TRENERA...")

    # --- 1. INICJALIZACJA DETEKTORÓW ---
    # Tworzymy osobne detektory dla każdej kamery
    # complexity=0 lub 1 jest szybsze (ważne przy dwóch kamerach)
    detector_front = PoseDetector(min_conf=0.5)
    detector_side = PoseDetector(min_conf=0.5)

    visualizer = Visualizer()
    tui = CyberDashboard(width=1920, height=1080)

    # Filtry wygładzające
    joints = [
        "Lokiec (L)", "Lokiec (P)", "Bark (L)", "Bark (P)",
        "Biodro (L)", "Biodro (P)", "Kolano (L)", "Kolano (P)"
    ]
    smoothers = {name: SignalSmoother(alpha=0.15) for name in joints}

    # --- 2. START KAMER ---
    # Front (USB)
    cam_front = CameraStream(src=config.CAM_FRONT_ID, name="Front").start()

    # Side (IP / USB)
    cam_side = None
    if config.USE_DUAL_CAMERA:
        cam_side = CameraStream(src=config.CAM_SIDE_ID, name="Side").start()
        print("Czekam na stabilizację kamer...")
        time.sleep(2.0)

    cv2.namedWindow(config.WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(config.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    prev_frame_time = 0

    while True:
        # A. Pobranie klatek
        frame_front = cam_front.read()
        frame_side = cam_side.read() if cam_side else None

        if frame_front is None:
            continue

        # FPS
        new_frame_time = time.time()
        fps = 1 / (new_frame_time - prev_frame_time) if (new_frame_time - prev_frame_time) > 0 else 0
        prev_frame_time = new_frame_time

        # --- B. DETEKCJA NA OBU KAMERACH ---

        # 1. Analiza Front
        results_front = detector_front.find_pose(frame_front)
        frame_front = visualizer.draw_skeleton(frame_front, results_front)

        # 2. Analiza Side (JEŚLI ISTNIEJE)
        results_side = None
        if frame_side is not None:
            # Tutaj dzieje się magia dla drugiej kamery
            results_side = detector_side.find_pose(frame_side)
            frame_side = visualizer.draw_skeleton(frame_side, results_side)

        # --- C. OBLICZENIA BIOMECHANIKI ---
        # Teraz możemy decydować, z której kamery brać dane.
        # Domyślnie bierzemy z Front, ale jak Front nie widzi, spróbujmy z Side.

        current_angles = {k: None for k in smoothers.keys()}
        status_msg = "SZUKAM SYLWETKI"

        # Funkcja pomocnicza do wyboru najlepszych punktów
        def get_best_landmarks(res_f, res_s):
            # Jeśli front widzi, bierz front. Jak nie, bierz side.
            if res_f.pose_landmarks: return res_f.pose_landmarks.landmark, 1  # 1 = Front
            if res_s and res_s.pose_landmarks: return res_s.pose_landmarks.landmark, 2  # 2 = Side
            return None, 0

        landmarks, source_id = get_best_landmarks(results_front, results_side)

        if landmarks:
            # Ustalamy wymiary właściwej klatki (żeby dobrze przeliczyć pozycję X,Y)
            if source_id == 1:
                h, w, _ = frame_front.shape
            else:
                h, w, _ = frame_side.shape

            def get_coords(i):
                return [landmarks[i].x * w, landmarks[i].y * h]

            def check_vis(i):
                return landmarks[i].visibility > 0.5

            def calc(name, i1, i2, i3):
                if check_vis(i1) and check_vis(i2) and check_vis(i3):
                    raw = Algorithm.calculate_angle_2d(get_coords(i1), get_coords(i2), get_coords(i3))
                    return smoothers[name].update(raw)
                return None

            # Obliczenia
            current_angles["Lokiec (L)"] = calc("Lokiec (L)", 11, 13, 15)
            current_angles["Lokiec (P)"] = calc("Lokiec (P)", 12, 14, 16)
            current_angles["Bark (L)"] = calc("Bark (L)", 13, 11, 23)
            current_angles["Bark (P)"] = calc("Bark (P)", 14, 12, 24)
            current_angles["Biodro (L)"] = calc("Biodro (L)", 11, 23, 25)
            current_angles["Biodro (P)"] = calc("Biodro (P)", 12, 24, 26)
            current_angles["Kolano (L)"] = calc("Kolano (L)", 23, 25, 27)
            current_angles["Kolano (P)"] = calc("Kolano (P)", 24, 26, 28)

            src_name = "FRONT" if source_id == 1 else "SIDE"
            status_msg = f"AKTYWNA: {src_name}"

        # --- D. RYSOWANIE DASHBOARDU ---
        # Przekazujemy oba obrazy do nowej funkcji compose
        final_interface = tui.compose(
            frame_front=frame_front,
            frame_side=frame_side,
            angles_dict=current_angles,
            status=status_msg,
            fps=fps
        )

        cv2.imshow(config.WINDOW_NAME, final_interface)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam_front.stop()
    if cam_side: cam_side.stop()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()