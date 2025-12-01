import cv2
import time
import sys
import numpy as np
import config
import torch

# --- IMPORTY MODUŁÓW PROJEKTU ---
from core.pose_detector import PoseDetector
from core.pose_detector_yolo import PoseDetectorYOLO
from core.algorithm import Algorithm, SignalSmoother
from core.camera_stream import CameraStream
from ui.dashboard import CyberDashboard
from ui.visualizer import Visualizer
from ui.launcher import CyberLauncher

# --- ZMIENNE GLOBALNE (Dla obsługi myszy) ---
g_conf_val = config.MIN_CONFIDENCE
g_smooth_val = 0.15
dashboard_ref = None  # Referencja do dashboardu


def on_mouse(event, x, y, flags, param):
    """Obsługa kliknięć w suwaki na Dashboardzie"""
    global g_conf_val, g_smooth_val, dashboard_ref

    if event == cv2.EVENT_LBUTTONDOWN or (event == cv2.EVENT_MOUSEMOVE and flags == cv2.EVENT_FLAG_LBUTTON):
        if dashboard_ref is None: return

        # 1. Obsługa suwaka CONFIDENCE
        rx, ry, rw, rh = dashboard_ref.slider_conf_rect
        if rx <= x <= rx + rw and ry <= y <= ry + rh:
            val = (x - rx) / rw
            g_conf_val = max(0.01, min(1.0, val))

        # 2. Obsługa suwaka SMOOTH
        rx, ry, rw, rh = dashboard_ref.slider_smooth_rect
        if rx <= x <= rx + rw and ry <= y <= ry + rh:
            val = (x - rx) / rw
            g_smooth_val = max(0.01, min(1.0, val))


def sanitize_text(text):
    """
    Zamienia polskie znaki na ASCII, aby OpenCV (cv2.putText)
    nie wyświetlał 'krzaczków' (znaków zapytania).
    """
    replacements = {
        'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
        'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N', 'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'
    }
    for pl, lat in replacements.items():
        text = text.replace(pl, lat)
    return text


def show_loading(text_lines):
    """Wyświetla ekran ładowania w stylu konsoli"""
    img = np.zeros((720, 1280, 3), dtype=np.uint8)
    # Tło (bardzo ciemna zieleń)
    img[:] = (5, 10, 5)

    y = 300
    if isinstance(text_lines, str):
        text_lines = [text_lines]

    cv2.putText(img, "SYSTEM BOOT SEQUENCE...", (50, 100), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)

    for line in text_lines:
        # Czyścimy tekst z polskich znaków przed wyświetleniem
        safe_line = sanitize_text(line)
        cv2.putText(img, f"> {safe_line}", (50, y), cv2.FONT_HERSHEY_PLAIN, 1.5, (200, 255, 200), 1)
        y += 40

    cv2.imshow(config.WINDOW_NAME, img)
    cv2.waitKey(1)


def main():
    global g_conf_val, g_smooth_val, dashboard_ref

    # 1. URUCHOMIENIE LAUNCHERA (KONFIGURACJA)
    launcher = CyberLauncher()
    # Jeśli użytkownik zamknął launcher "iksem", nie uruchamiamy dalej
    if not launcher.should_start:
        return

    # 2. INICJALIZACJA OKNA GŁÓWNEGO
    cv2.namedWindow(config.WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(config.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # Podpinamy callback myszy (do suwaków)
    cv2.setMouseCallback(config.WINDOW_NAME, on_mouse)

    # Inicjalizacja listy logów
    logs = ["Inicjalizacja kernela..."]
    show_loading(logs)

    # 3. DETEKTORY I AI
    logs.append("Wykrywanie akceleratora GPU...")
    show_loading(logs)

    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        # sanitize_text obsłuży ewentualne znaki specjalne w nazwie GPU
        logs.append(f"GPU OK: {gpu_name}")
    else:
        logs.append("GPU BRAK. Przelaczanie na CPU.")
    show_loading(logs)

    # Pobranie konfiguracji wybranej w Launcherze
    # Domyślne wartości na wypadek braku w configu
    yolo_size = getattr(config, 'MODEL_YOLO_SIZE', 'n')
    mp_complex = getattr(config, 'MODEL_MP_COMPLEXITY', 1)

    logs.append(f"Ladowanie modelu YOLOv8 (Size: {yolo_size})...")
    show_loading(logs)
    # Inicjalizacja YOLO
    detector_yolo = PoseDetectorYOLO(model_size=yolo_size, min_conf=g_conf_val)

    logs.append(f"Ladowanie modelu MediaPipe (Complex: {mp_complex})...")
    show_loading(logs)
    # Inicjalizacja MediaPipe (z parametrem complexity)
    detector_mp = PoseDetector(min_conf=g_conf_val, complexity=mp_complex)

    vis = Visualizer()
    tui = CyberDashboard(width=1920, height=1080)
    dashboard_ref = tui  # Przekazanie referencji do globalnej zmiennej

    # 4. ŁĄCZENIE Z KAMERAMI
    logs.append(f"Laczenie z CAM 1 (Front): {config.CAM_FRONT_ID} ...")
    show_loading(logs)
    cam_front = CameraStream(src=config.CAM_FRONT_ID, name="Front").start()

    cam_side = None
    if config.USE_DUAL_CAMERA:
        logs.append(f"Laczenie z CAM 2 (Side): {config.CAM_SIDE_ID} ...")
        show_loading(logs)
        cam_side = CameraStream(src=config.CAM_SIDE_ID, name="Side").start()
    else:
        logs.append("CAM 2: Wylaczona w konfiguracji.")
        show_loading(logs)

    logs.append("System gotowy. Uruchamianie interfejsu.")
    show_loading(logs)
    time.sleep(0.5)  # Krótka pauza na przeczytanie logów

    # 5. PRZYGOTOWANIE PĘTLI GŁÓWNEJ
    joints = ["Lokiec (L)", "Lokiec (P)", "Bark (L)", "Bark (P)",
              "Biodro (L)", "Biodro (P)", "Kolano (L)", "Kolano (P)"]

    # Inicjalizacja filtrów wygładzających
    smoothers = {name: SignalSmoother(alpha=0.15) for name in joints}

    prev_frame_time = 0

    # --- PĘTLA GŁÓWNA ---
    while True:
        # A. Aktualizacja parametrów na żywo (z suwaków)
        detector_yolo.min_conf = g_conf_val
        detector_mp.pose.min_detection_confidence = g_conf_val
        for s in smoothers.values():
            s.alpha = g_smooth_val

        # B. Pobranie klatek z wątków
        frame_front = cam_front.read()
        frame_side = cam_side.read() if cam_side else None

        # C. Obliczenie FPS
        new_frame_time = time.time()
        fps = 1 / (new_frame_time - prev_frame_time) if (new_frame_time - prev_frame_time) > 0 else 0
        prev_frame_time = new_frame_time

        current_angles = {k: None for k in joints}
        status_msg = "SCANNING..."

        # D. ANALIZA FRONT (YOLO)
        if frame_front is not None:
            # Inferencja
            res_y = detector_yolo.find_pose(frame_front)
            kp_y = detector_yolo.get_landmarks(res_y)

            # Rysowanie szkieletu
            frame_front = vis.draw_yolo_skeleton(frame_front, kp_y, conf_thresh=g_conf_val)

            kp_map = config.KP_YOLO
            # Sprawdzenie czy w ogóle widzimy osobę (np. lewy bark)
            if kp_y is not None and kp_y[kp_map["L_SH"]][2] > g_conf_val:
                status_msg = "YOLO: ACTIVE"

                # Funkcja pomocnicza do obliczania kąta dla YOLO
                def calc_y(name, k1, k2, k3):
                    # Pobieramy punkty: (x, y, conf)
                    p1 = kp_y[kp_map[k1]]
                    p2 = kp_y[kp_map[k2]]
                    p3 = kp_y[kp_map[k3]]

                    # Jeśli wszystkie 3 punkty są pewne
                    if p1[2] > g_conf_val and p2[2] > g_conf_val and p3[2] > g_conf_val:
                        val = Algorithm.calculate_angle_2d(p1[:2], p2[:2], p3[:2])
                        return smoothers[name].update(val)
                    return None

                # Obliczenia dla wszystkich stawów
                current_angles["Lokiec (L)"] = calc_y("Lokiec (L)", "L_SH", "L_EL", "L_WR")
                current_angles["Lokiec (P)"] = calc_y("Lokiec (P)", "R_SH", "R_EL", "R_WR")
                current_angles["Bark (L)"] = calc_y("Bark (L)", "L_HIP", "L_SH", "L_EL")
                current_angles["Bark (P)"] = calc_y("Bark (P)", "R_HIP", "R_SH", "R_EL")
                current_angles["Biodro (L)"] = calc_y("Biodro (L)", "L_SH", "L_HIP", "L_KN")
                current_angles["Biodro (P)"] = calc_y("Biodro (P)", "R_SH", "R_HIP", "R_KN")
                current_angles["Kolano (L)"] = calc_y("Kolano (L)", "L_HIP", "L_KN", "L_ANK")
                current_angles["Kolano (P)"] = calc_y("Kolano (P)", "R_HIP", "R_KN", "R_ANK")

        # E. ANALIZA SIDE (MediaPipe)
        if frame_side is not None:
            # Zmniejszamy obraz dla MP (optymalizacja CPU)
            mp_in = cv2.resize(frame_side, (640, 480))
            res_mp = detector_mp.find_pose(mp_in)

            if res_mp.pose_landmarks:
                # Rysowanie
                mp_drawn = vis.draw_mp_skeleton(mp_in, res_mp, conf_thresh=g_conf_val)
                # Skalowanie rysunku z powrotem do rozmiaru oryginału
                frame_side = cv2.resize(mp_drawn, (frame_side.shape[1], frame_side.shape[0]))

                if "YOLO" not in status_msg:
                    status_msg = "MP: ACTIVE"

                lm = res_mp.pose_landmarks.landmark
                h, w, _ = mp_in.shape

                # Funkcje pomocnicze dla MP
                def get_m(i):
                    return [lm[i].x * w, lm[i].y * h]

                def vis_m(i):
                    return lm[i].visibility > g_conf_val

                def calc_m(name, i1, i2, i3):
                    # i1, i2, i3 to indeksy punktów MediaPipe
                    if vis_m(i1) and vis_m(i2) and vis_m(i3):
                        raw = Algorithm.calculate_angle_2d(get_m(i1), get_m(i2), get_m(i3))
                        return smoothers[name].update(raw)
                    # Jeśli nie widzi, zwracamy starą wartość (lub None)
                    return current_angles.get(name)

                # Nadpisywanie kątów, które lepiej widać z boku (Kolana, Biodra)
                v = calc_m("Kolano (L)", 23, 25, 27)
                if v: current_angles["Kolano (L)"] = v

                v = calc_m("Kolano (P)", 24, 26, 28)
                if v: current_angles["Kolano (P)"] = v

                v = calc_m("Biodro (L)", 11, 23, 25)
                if v: current_angles["Biodro (L)"] = v

        # F. BUDOWANIE INTERFEJSU
        final_frame = tui.compose(
            frame_front=frame_front,
            frame_side=frame_side,
            angles_dict=current_angles,
            status=status_msg,
            fps=fps,
            conf_val=g_conf_val,  # Przekazujemy wartość suwaka
            smooth_val=g_smooth_val,  # Przekazujemy wartość suwaka
            use_dual_cam=config.USE_DUAL_CAMERA
        )

        # Wyświetlenie
        cv2.imshow(config.WINDOW_NAME, final_frame)

        # Wyjście klawiszem 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 6. SPRZĄTANIE PO ZAKOŃCZENIU
    print("[SYSTEM] Shutdown.")
    cam_front.stop()
    if cam_side:
        cam_side.stop()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()