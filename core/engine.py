# core/engine.py
import cv2
import time
import numpy as np
import torch
import config
from core.pose_detector import PoseDetector
from core.pose_detector_yolo import PoseDetectorYOLO
from core.camera_stream import CameraStream
from ui.dashboard import CyberDashboard
from ui.visualizer import Visualizer
from core.analyzer import MotionAnalyzer


class CyberEngine:
    def __init__(self):
        # 1. Konfiguracja stanu
        self.running = True
        self.conf_val = config.MIN_CONFIDENCE
        self.smooth_val = 0.15

        # 2. Inicjalizacja komponentów
        self._init_window()
        self._show_boot_sequence()

        # Modele AI
        yolo_size = getattr(config, 'MODEL_YOLO_SIZE', 'n')
        mp_complex = getattr(config, 'MODEL_MP_COMPLEXITY', 1)

        self.detector_yolo = PoseDetectorYOLO(model_size=yolo_size, min_conf=self.conf_val)
        self.detector_mp = PoseDetector(min_conf=self.conf_val, complexity=mp_complex)

        # Logika i UI
        self.analyzer = MotionAnalyzer()
        self.vis = Visualizer()
        self.dashboard = CyberDashboard(width=1920, height=1080)

        # 3. Kamery
        self.cam_front = CameraStream(src=config.CAM_FRONT_ID, name="Front").start()
        self.cam_side = None
        if config.USE_DUAL_CAMERA:
            self.cam_side = CameraStream(src=config.CAM_SIDE_ID, name="Side").start()

        # Zmienne pętli
        self.prev_time = time.time()

    def _init_window(self):
        cv2.namedWindow(config.WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(config.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.setMouseCallback(config.WINDOW_NAME, self._on_mouse)

    def _sanitize_text(self, text):
        """Usuwa polskie znaki dla OpenCV"""
        replacements = {'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
                        'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N', 'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'}
        for pl, lat in replacements.items(): text = text.replace(pl, lat)
        return text

    def _show_boot_sequence(self):
        """Wyświetla logi startowe"""
        logs = [
            "Inicjalizacja kernela...",
            f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'BRAK (CPU)'}",
            "Ladowanie modeli AI...",
            "Laczenie z sensorami wizyjnymi...",
            "System gotowy."
        ]
        img = np.zeros((720, 1280, 3), dtype=np.uint8)
        img[:] = (5, 10, 5)

        cv2.putText(img, "SYSTEM BOOT...", (50, 100), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
        y = 300
        for line in logs:
            safe_line = self._sanitize_text(line)
            cv2.putText(img, f"> {safe_line}", (50, y), cv2.FONT_HERSHEY_PLAIN, 1.5, (200, 255, 200), 1)
            y += 40
            cv2.imshow(config.WINDOW_NAME, img)
            cv2.waitKey(200)  # Symulacja ładowania
        time.sleep(0.5)

    def _on_mouse(self, event, x, y, flags, param):
        """Obsługa myszy wewnątrz klasy"""
        if event == cv2.EVENT_LBUTTONDOWN or (event == cv2.EVENT_MOUSEMOVE and flags == cv2.EVENT_FLAG_LBUTTON):
            # Confidence Slider
            rx, ry, rw, rh = self.dashboard.slider_conf_rect
            if rx <= x <= rx + rw and ry <= y <= ry + rh:
                self.conf_val = max(0.01, min(1.0, (x - rx) / rw))

            # Smooth Slider
            rx, ry, rw, rh = self.dashboard.slider_smooth_rect
            if rx <= x <= rx + rw and ry <= y <= ry + rh:
                self.smooth_val = max(0.01, min(1.0, (x - rx) / rw))

    def _update_settings(self):
        """Przekazuje zmienne z UI do logiki"""
        self.detector_yolo.min_conf = self.conf_val
        self.detector_mp.pose.min_detection_confidence = self.conf_val
        self.analyzer.update_params(self.smooth_val)

    def run(self):
        """Główna pętla aplikacji"""
        while self.running:
            self._update_settings()

            # 1. Pobranie danych
            frame_front = self.cam_front.read()
            frame_side = self.cam_side.read() if self.cam_side else None

            # FPS Calculation
            now = time.time()
            fps = 1 / (now - self.prev_time) if (now - self.prev_time) > 0 else 0
            self.prev_time = now

            status_msg = "SCANNING..."

            # 2. Przetwarzanie FRONT (YOLO)
            if frame_front is not None:
                res_y = self.detector_yolo.find_pose(frame_front)
                kp_y = self.detector_yolo.get_landmarks(res_y)
                frame_front = self.vis.draw_yolo_skeleton(frame_front, kp_y, self.conf_val)

                if self.analyzer.process_yolo(kp_y, self.conf_val):
                    status_msg = "YOLO: ACTIVE"

            # 3. Przetwarzanie SIDE (MediaPipe)
            if frame_side is not None:
                mp_in = cv2.resize(frame_side, (640, 480))
                res_mp = self.detector_mp.find_pose(mp_in)

                if res_mp.pose_landmarks:
                    mp_drawn = self.vis.draw_mp_skeleton(mp_in, res_mp, self.conf_val)
                    frame_side = cv2.resize(mp_drawn, (frame_side.shape[1], frame_side.shape[0]))

                    if self.analyzer.process_mediapipe(res_mp.pose_landmarks.landmark,
                                                       mp_in.shape[1], mp_in.shape[0], self.conf_val):
                        if "YOLO" not in status_msg: status_msg = "MP: ACTIVE"

            # 4. Renderowanie UI
            final_frame = self.dashboard.compose(
                frame_front, frame_side,
                self.analyzer.current_angles,
                status_msg, fps,
                self.conf_val, self.smooth_val,
                config.USE_DUAL_CAMERA
            )

            cv2.imshow(config.WINDOW_NAME, final_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.running = False

        self._cleanup()

    def _cleanup(self):
        print("[SYSTEM] Shutdown initiated.")
        self.cam_front.stop()
        if self.cam_side: self.cam_side.stop()
        cv2.destroyAllWindows()