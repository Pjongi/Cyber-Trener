import cv2
import numpy as np
import datetime


class CyberDashboard:
    def __init__(self, width=1920, height=1080):
        self.W = width
        self.H = height

        # Kolory
        self.C_BG = (5, 10, 5)
        self.C_MAIN = (0, 255, 0)  # Zieleń Matrix
        self.C_DIM = (0, 80, 0)  # Ciemna zieleń
        self.C_ALERT = (0, 0, 255)  # Czerwień
        self.C_WHITE = (200, 255, 200)
        self.C_YELLOW = (0, 255, 255)

        self.side_w = 480
        self.FONT = cv2.FONT_HERSHEY_PLAIN

        # Definicja obszarów suwaków
        self.slider_conf_rect = (550, 30, 300, 20)
        self.slider_smooth_rect = (900, 30, 300, 20)

        # Optymalizacja pamięci (Canvas i Cache)
        self.canvas = np.zeros((self.H, self.W, 3), dtype=np.uint8)
        self.noise_cache = {}
        self.img_cache = {}  # Cache dla obrazków instruktażowych

    def _draw_box(self, img, x, y, w, h, title=""):
        cv2.rectangle(img, (x, y), (x + w, y + h), self.C_DIM, 1)
        cv2.rectangle(img, (x, y), (x + w, y + h), self.C_MAIN, 1)
        if title:
            cv2.putText(img, f" {title} ", (x + 20, y + 20), self.FONT, 1.2, self.C_MAIN, 1)

    def _draw_data_row(self, img, x, y, w, label, value):
        cv2.putText(img, label, (x + 10, y), self.FONT, 1.2, self.C_WHITE, 1)
        if value is None:
            cv2.putText(img, "---", (x + w - 80, y), self.FONT, 1.2, (100, 100, 100), 1)
        else:
            val_str = f"{int(value)}"
            cv2.putText(img, val_str, (x + w - 80, y), self.FONT, 1.2, self.C_YELLOW, 1)
            bar_max = w - 130
            bar_cur = int((value / 180) * bar_max)
            bar_cur = max(0, min(bar_cur, bar_max))
            cv2.rectangle(img, (x + 10, y + 8), (x + 10 + bar_cur, y + 14), self.C_MAIN, -1)

    def _draw_slider(self, img, rect, value, label):
        x, y, w, h = rect
        cv2.rectangle(img, (x, y), (x + w, y + h), self.C_DIM, -1)
        cv2.rectangle(img, (x, y), (x + w, y + h), self.C_MAIN, 1)

        fill_w = int(w * value)
        cv2.rectangle(img, (x, y), (x + fill_w, y + h), (0, 100, 0), -1)

        knob_x = x + fill_w
        cv2.line(img, (knob_x, y - 5), (knob_x, y + h + 5), self.C_YELLOW, 2)

        text = f"{label}: {int(value * 100)}%"
        cv2.putText(img, text, (x, y - 10), self.FONT, 1.0, self.C_WHITE, 1)

    def _get_noise(self, width, height):
        key = (width, height)
        if key not in self.noise_cache:
            noise = np.random.randint(0, 50, (height, width), dtype=np.uint8)
            noise_bgr = cv2.cvtColor(noise, cv2.COLOR_GRAY2BGR)
            noise_bgr[:, :, 1] += 20
            self.noise_cache[key] = noise_bgr
        return self.noise_cache[key]

    def _get_cached_image(self, path):
        if not path: return None
        if path not in self.img_cache:
            img = cv2.imread(path)
            if img is not None:
                self.img_cache[path] = cv2.resize(img, (250, 250))  # Skalujemy raz
            else:
                self.img_cache[path] = None
        return self.img_cache[path]

    def compose(self, frame_front, frame_side, angles_dict, status, fps, conf_val, smooth_val, use_dual_cam,
                trainer_info=None):
        self.canvas[:] = self.C_BG
        canvas = self.canvas

        # --- 1. NAGŁÓWEK ---
        self._draw_box(canvas, 20, 20, self.W - 40, 60)
        date = datetime.datetime.now().strftime("%H:%M:%S")
        head = f"CYBER TRENER | FPS: {int(fps)} | {date}"
        cv2.putText(canvas, head, (40, 60), self.FONT, 1.3, self.C_MAIN, 1)

        self._draw_slider(canvas, self.slider_conf_rect, conf_val, "MIN CONF")
        self._draw_slider(canvas, self.slider_smooth_rect, smooth_val, "SMOOTH")

        # --- 2. PANEL DANYCH ---
        px, py = 20, 100
        ph = self.H - 120
        self._draw_box(canvas, px, py, self.side_w, ph, "ANALIZA RUCHU")

        y = py + 60
        gap = 40
        keys_order = ["Lokiec (L)", "Lokiec (P)", "Bark (L)", "Bark (P)",
                      "Biodro (L)", "Biodro (P)", "Kolano (L)", "Kolano (P)"]

        for key in keys_order:
            val = angles_dict.get(key)
            if "Bark (P)" in key or "Biodro (P)" in key: y += 15
            self._draw_data_row(canvas, px + 10, y, self.side_w - 20, key, val)
            y += gap

        y += 50
        cv2.putText(canvas, "STATUS SYSTEMU:", (px + 20, y), self.FONT, 1.2, self.C_WHITE, 1)
        y += 40
        c_stat = self.C_MAIN if "ACTIVE" in status or "COMPUTING" in status else self.C_YELLOW
        cv2.putText(canvas, status, (px + 20, y), self.FONT, 1.8, c_stat, 2)

        # --- 3. WIDEO ---
        vx = self.side_w + 40
        vw = self.W - vx - 20
        vh = (self.H - 130) // 2

        # CAM 1 (FRONT)
        self._draw_box(canvas, vx, 100, vw, vh, "CAM 1: FRONT (YOLO/GPU)")

        # Ramka trenera dla kamery 1
        trainer_color = self.C_MAIN
        if trainer_info:
            trainer_color = trainer_info["color"]
            # Rysujemy ramkę stanu wokół kamery
            cv2.rectangle(canvas, (vx - 2, 98), (vx + vw + 2, 100 + vh + 2), trainer_color, 3)

        if frame_front is not None:
            try:
                resized = cv2.resize(frame_front, (vw - 4, vh - 30))
                canvas[100 + 25: 100 + 25 + resized.shape[0], vx + 2: vx + 2 + resized.shape[1]] = resized
            except:
                pass
        else:
            noise = self._get_noise(vw - 4, vh - 30)
            canvas[100 + 25: 100 + 25 + noise.shape[0], vx + 2: vx + 2 + noise.shape[1]] = noise
            cv2.putText(canvas, "NO SIGNAL", (vx + vw // 2 - 80, 100 + vh // 2), self.FONT, 2, self.C_ALERT, 2)

        # --- UI TRENERA (NAŁOŻONE NA EKRAN) ---
        if trainer_info:
            # 1. Wiadomość statusu (nad kamerą)
            cv2.putText(canvas, trainer_info["message"], (vx, 90), self.FONT, 1.5, trainer_color, 2)

            # 2. Pasek postępu (między nagłówkiem a kamerą)
            if trainer_info["progress"] > 0:
                bar_w = int(vw * trainer_info["progress"])
                cv2.rectangle(canvas, (vx, 95), (vx + bar_w, 100), trainer_color, -1)

            # 3. Zdjęcie wzorcowe (w prawym dolnym rogu ekranu, lub pod kamerą)
            img_path = trainer_info.get("ref_image")
            if img_path:
                ref_img = self._get_cached_image(img_path)
                if ref_img is not None:
                    # Pozycjonujemy w prawym dolnym rogu aplikacji
                    rh, rw, _ = ref_img.shape
                    # Rysujemy w lewym dolnym rogu obszaru wideo (żeby nie zasłaniać kamery 2)
                    ry_pos = 100 + vh - rh - 10
                    rx_pos = vx + 10

                    try:
                        canvas[ry_pos:ry_pos + rh, rx_pos:rx_pos + rw] = ref_img
                        cv2.rectangle(canvas, (rx_pos, ry_pos), (rx_pos + rw, ry_pos + rh), (255, 255, 255), 2)
                        cv2.putText(canvas, "WZORZEC", (rx_pos, ry_pos - 5), self.FONT, 1.2, (255, 255, 255), 1)
                    except:
                        pass

            # 4. Feedback błędów (Pod kamerami, duża czcionka)
            err_y = 100 + vh + vh + 50  # Pod drugą kamerą
            if trainer_info["feedback"]:
                cv2.putText(canvas, "KOREKTA:", (vx, err_y), self.FONT, 2.0, (0, 0, 255), 3)
                for i, err in enumerate(trainer_info["feedback"]):
                    cv2.putText(canvas, f"- {err}", (vx + 220, err_y + (i * 40)), self.FONT, 1.7, (100, 100, 255), 2)

        # CAM 2 (SIDE)
        y2 = 100 + vh + 10
        title_c2 = "CAM 2: SIDE (MediaPipe/CPU)"
        if not use_dual_cam: title_c2 += " [OFFLINE]"

        self._draw_box(canvas, vx, y2, vw, vh, title_c2)

        if use_dual_cam:
            if frame_side is not None:
                try:
                    resized = cv2.resize(frame_side, (vw - 4, vh - 30))
                    canvas[y2 + 25: y2 + 25 + resized.shape[0], vx + 2: vx + 2 + resized.shape[1]] = resized
                except:
                    pass
            else:
                noise = self._get_noise(vw - 4, vh - 30)
                canvas[y2 + 25: y2 + 25 + noise.shape[0], vx + 2: vx + 2 + noise.shape[1]] = noise
                cv2.putText(canvas, "SEARCHING...", (vx + vw // 2 - 90, y2 + vh // 2), self.FONT, 2, self.C_YELLOW, 2)
        else:
            cv2.putText(canvas, "CAMERA DISABLED", (vx + vw // 2 - 120, y2 + vh // 2), self.FONT, 2, (50, 50, 50), 2)
            cv2.putText(canvas, "(Enable in Launcher)", (vx + vw // 2 - 100, y2 + vh // 2 + 30), self.FONT, 1,
                        (50, 50, 50), 1)

        return self.canvas