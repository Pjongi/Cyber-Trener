# core/engine.py
import cv2
import time
import numpy as np
import threading
import copy
import config
from core.pose_detector_yolo import PoseDetectorYOLO
from core.pose_detector import PoseDetector
from core.camera_stream import CameraStream
from ui.dashboard import CyberDashboard
from ui.visualizer import Visualizer
from core.analyzer import MotionAnalyzer
from core.trainer import CyberTrainer  # <--- IMPORT NOWEGO MODUŁU


class CyberEngine:
    def __init__(self):
        self.running = True
        self.mode = config.MODE

        # --- USTAWIENIA ---
        self.conf_val = config.MIN_CONFIDENCE
        self.smooth_val = 0.15

        # --- ZMIENNE DLA WĄTKÓW (Thread Safety) ---
        self.lock = threading.Lock()

        self.shared_frame_front = None
        self.shared_frame_side = None

        self.last_kp_y = None
        self.last_mp_res = None
        self.ai_busy = False

        self._init_window()

        self.src_front = None
        self.src_side = None
        self.rec_front = None
        self.rec_side = None

        if self.mode != 'RECORD':
            self.vis = Visualizer()
            self.dashboard = CyberDashboard()
            self.analyzer = MotionAnalyzer()
            # INICJALIZACJA TRENERA
            # Szuka pliku poses.json w głównym folderze
            self.trainer = CyberTrainer("poses.json")

            yolo_size = getattr(config, 'MODEL_YOLO_SIZE', 'n')
            mp_complex = getattr(config, 'MODEL_MP_COMPLEXITY', 0)

            print(f"[AI] Ładowanie YOLO ({yolo_size}) i MediaPipe ({mp_complex})...")
            self.detector_yolo = PoseDetectorYOLO(yolo_size, self.conf_val)
            self.detector_mp = PoseDetector(self.conf_val, mp_complex)

        self._setup_sources()
        if self.mode == 'RECORD':
            self._setup_recorders()

        self.prev_time = time.time()

        if self.mode == 'LIVE':
            self.thread = threading.Thread(target=self._ai_worker, daemon=True)
            self.thread.start()

    def _init_window(self):
        cv2.namedWindow(config.WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(config.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.setMouseCallback(config.WINDOW_NAME, self._on_mouse)

    def _setup_sources(self):
        if self.mode == 'FILE':
            self.src_front = cv2.VideoCapture(config.INPUT_FILE_FRONT)
            if config.USE_DUAL_CAMERA:
                self.src_side = cv2.VideoCapture(config.INPUT_FILE_SIDE)
        else:
            self.src_front = CameraStream(config.CAM_FRONT_ID, "Front").start()
            if config.USE_DUAL_CAMERA:
                self.src_side = CameraStream(config.CAM_SIDE_ID, "Side").start()

    def _setup_recorders(self):
        fps = 30.0
        w, h = 1280, 720
        self.rec_front = cv2.VideoWriter(f"{config.OUTPUT_BASE_NAME}_front.avi", cv2.VideoWriter_fourcc(*'MJPG'), fps,
                                         (w, h))
        if config.USE_DUAL_CAMERA:
            self.rec_side = cv2.VideoWriter(f"{config.OUTPUT_BASE_NAME}_side.avi", cv2.VideoWriter_fourcc(*'MJPG'), fps,
                                            (w, h))

    def _ai_worker(self):
        while self.running:
            frm_f = None
            frm_s = None

            with self.lock:
                if self.shared_frame_front is not None:
                    frm_f = self.shared_frame_front.copy()
                if self.shared_frame_side is not None:
                    frm_s = self.shared_frame_side.copy()

            if frm_f is None:
                time.sleep(0.01)
                continue

            self.ai_busy = True

            res_y = self.detector_yolo.find_pose(frm_f)
            kp_y = self.detector_yolo.get_landmarks(res_y)

            res_mp = None
            if frm_s is not None:
                mp_in = cv2.resize(frm_s, (640, 480))
                res_mp = self.detector_mp.find_pose(mp_in)

            with self.lock:
                self.last_kp_y = kp_y
                self.last_mp_res = res_mp

            self.ai_busy = False
            time.sleep(0.001)

    def run(self):
        while self.running:
            self._update_settings()

            frame_front = self._read_frame(self.src_front)
            frame_side = self._read_frame(self.src_side)

            if frame_front is None:
                if self.mode == 'FILE': break
                time.sleep(0.005)
                continue

            if self.mode == 'RECORD':
                if self.rec_front: self.rec_front.write(cv2.resize(frame_front, (1280, 720)))
                if self.rec_side and frame_side is not None: self.rec_side.write(cv2.resize(frame_side, (1280, 720)))
                cam_fps = getattr(self.src_front, 'real_fps', 0)
                cv2.putText(frame_front, f"REC RAW | CAM FPS: {int(cam_fps)}", (50, 50), cv2.FONT_HERSHEY_PLAIN, 2,
                            (0, 0, 255), 2)
                cv2.imshow(config.WINDOW_NAME, frame_front)

            else:
                # --- PRZETWARZANIE DANYCH ---

                # 1. Przekaż klatki do wątku AI (LIVE)
                if self.mode == 'LIVE':
                    with self.lock:
                        self.shared_frame_front = frame_front
                        self.shared_frame_side = frame_side
                    status_txt = "AI: COMPUTING" if self.ai_busy else "AI: READY"
                else:
                    # FILE - tryb synchroniczny
                    status_txt = "FILE: ANALYZING"
                    res_y = self.detector_yolo.find_pose(frame_front)
                    self.last_kp_y = self.detector_yolo.get_landmarks(res_y)
                    if frame_side is not None:
                        mp_in = cv2.resize(frame_side, (640, 480))
                        self.last_mp_res = self.detector_mp.find_pose(mp_in)

                # 2. Pobierz wyniki AI i oblicz kąty
                cur_kp = None
                cur_mp = None
                with self.lock:
                    cur_kp = self.last_kp_y
                    cur_mp = self.last_mp_res

                # WAŻNE: Czyścimy stare kąty przed nową analizą
                self.analyzer.current_angles = {}

                # Analizujemy na nowo na podstawie ostatnich punktów
                self.analyzer.process_yolo(cur_kp, self.conf_val)
                if cur_mp and cur_mp.pose_landmarks:
                    self.analyzer.process_mediapipe(cur_mp.pose_landmarks.landmark, 640, 480, self.conf_val)

                # 3. Aktualizacja TRENERA
                trainer_info = None
                if self.trainer:
                    trainer_info = self.trainer.update(self.analyzer.current_angles)

                # --- RYSOWANIE ---
                frame_front_draw = self.vis.draw_yolo_skeleton(frame_front, cur_kp, self.conf_val)
                frame_side_draw = frame_side
                if frame_side is not None:
                    frame_side_draw = self.vis.draw_mp_skeleton(frame_side, cur_mp, self.conf_val)

                now = time.time()
                app_fps = 1 / (now - self.prev_time) if (now - self.prev_time) > 0 else 0
                self.prev_time = now
                cam_fps = getattr(self.src_front, 'real_fps', 0)
                if self.mode == 'FILE': cam_fps = 30

                fps_display = f"CAM: {int(cam_fps)} | APP: {int(app_fps)}"

                # Przekazujemy trainer_info do Dashboardu
                final = self.dashboard.compose(
                    frame_front_draw, frame_side_draw, self.analyzer.current_angles,
                    status_txt, 0, self.conf_val, self.smooth_val, config.USE_DUAL_CAMERA,
                    trainer_info
                )

                cv2.rectangle(final, (350, 40), (700, 80), (5, 10, 5), -1)
                cv2.putText(final, fps_display, (360, 70), cv2.FONT_HERSHEY_PLAIN, 1.5, (0, 255, 255), 1)

                cv2.imshow(config.WINDOW_NAME, final)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.running = False

        self._cleanup()

    def _read_frame(self, source):
        if source is None: return None
        if hasattr(source, 'read'): return source.read()
        ret, frame = source.read()
        return frame if ret else None

    def _on_mouse(self, event, x, y, flags, param):
        if hasattr(self, 'dashboard'):
            if event == cv2.EVENT_LBUTTONDOWN or (event == cv2.EVENT_MOUSEMOVE and flags == cv2.EVENT_FLAG_LBUTTON):
                rx, ry, rw, rh = self.dashboard.slider_conf_rect
                if rx <= x <= rx + rw and ry <= y <= ry + rh:
                    self.conf_val = max(0.01, min(1.0, (x - rx) / rw))
                rx, ry, rw, rh = self.dashboard.slider_smooth_rect
                if rx <= x <= rx + rw and ry <= y <= ry + rh:
                    self.smooth_val = max(0.01, min(1.0, (x - rx) / rw))

    def _update_settings(self):
        if hasattr(self, 'detector_yolo'):
            self.detector_yolo.min_conf = self.conf_val
            self.detector_mp.pose.min_detection_confidence = self.conf_val
            self.analyzer.update_params(self.smooth_val)

    def _cleanup(self):
        print("[SYSTEM] Zamykanie...")
        self.running = False
        if self.mode != 'FILE':
            if self.src_front: self.src_front.stop()
            if self.src_side: self.src_side.stop()
        if self.rec_front: self.rec_front.release()
        cv2.destroyAllWindows()