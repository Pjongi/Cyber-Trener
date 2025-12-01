import cv2
import numpy as np
import datetime
import time


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

        # Definicja obszarów suwaków (x, y, w, h) - potrzebne do obsługi myszki w main.py
        # Umieszczamy je na górze, obok nagłówka
        self.slider_conf_rect = (550, 30, 300, 20)
        self.slider_smooth_rect = (900, 30, 300, 20)

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
        """Rysuje suwak w stylu Cyberpunk"""
        x, y, w, h = rect

        # Tło suwaka
        cv2.rectangle(img, (x, y), (x + w, y + h), self.C_DIM, -1)
        cv2.rectangle(img, (x, y), (x + w, y + h), self.C_MAIN, 1)

        # Wypełnienie (Progress)
        # value jest od 0.0 do 1.0
        fill_w = int(w * value)
        cv2.rectangle(img, (x, y), (x + fill_w, y + h), (0, 100, 0), -1)  # Ciemniejsze wypełnienie

        # Uchwyt (Knob)
        knob_x = x + fill_w
        cv2.line(img, (knob_x, y - 5), (knob_x, y + h + 5), self.C_YELLOW, 2)

        # Etykieta i Wartość
        text = f"{label}: {int(value * 100)}%"
        cv2.putText(img, text, (x, y - 10), self.FONT, 1.0, self.C_WHITE, 1)

    def _draw_noise(self, width, height):
        noise = np.random.randint(0, 50, (height, width), dtype=np.uint8)  # Ciemniejszy szum
        noise_bgr = cv2.cvtColor(noise, cv2.COLOR_GRAY2BGR)
        # Dodajemy zielony odcień
        noise_bgr[:, :, 1] += 20
        return noise_bgr

    def compose(self, frame_front, frame_side, angles_dict, status, fps, conf_val, smooth_val, use_dual_cam):
        canvas = np.zeros((self.H, self.W, 3), dtype=np.uint8)
        canvas[:] = self.C_BG

        # --- 1. NAGŁÓWEK ---
        self._draw_box(canvas, 20, 20, self.W - 40, 60)
        date = datetime.datetime.now().strftime("%H:%M:%S")
        head = f"CYBER TRENER | FPS: {int(fps)} | {date}"
        cv2.putText(canvas, head, (40, 60), self.FONT, 1.3, self.C_MAIN, 1)

        # --- SUWAKI (Rysowane ręcznie) ---
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
        c_stat = self.C_MAIN if "ACTIVE" in status else self.C_YELLOW
        cv2.putText(canvas, status, (px + 20, y), self.FONT, 1.8, c_stat, 2)

        # --- 3. WIDEO ---
        vx = self.side_w + 40
        vw = self.W - vx - 20
        vh = (self.H - 130) // 2

        # CAM 1
        self._draw_box(canvas, vx, 100, vw, vh, "CAM 1: FRONT (YOLO/GPU)")
        if frame_front is not None:
            try:
                resized = cv2.resize(frame_front, (vw - 4, vh - 30))
                canvas[100 + 25: 100 + 25 + resized.shape[0], vx + 2: vx + 2 + resized.shape[1]] = resized
            except:
                pass
        else:
            # Szum przy braku sygnału (ale włączonej kamerze)
            noise = self._draw_noise(vw - 4, vh - 30)
            canvas[100 + 25: 100 + 25 + noise.shape[0], vx + 2: vx + 2 + noise.shape[1]] = noise
            cv2.putText(canvas, "NO SIGNAL", (vx + vw // 2 - 80, 100 + vh // 2), self.FONT, 2, self.C_ALERT, 2)

        # CAM 2
        y2 = 100 + vh + 10
        title_c2 = "CAM 2: SIDE (MediaPipe/CPU)"
        if not use_dual_cam:
            title_c2 += " [OFFLINE]"

        self._draw_box(canvas, vx, y2, vw, vh, title_c2)

        if use_dual_cam:
            # Jeśli włączona w konfigu
            if frame_side is not None:
                try:
                    resized = cv2.resize(frame_side, (vw - 4, vh - 30))
                    canvas[y2 + 25: y2 + 25 + resized.shape[0], vx + 2: vx + 2 + resized.shape[1]] = resized
                except:
                    pass
            else:
                # Włączona, ale brak sygnału -> Szum
                noise = self._draw_noise(vw - 4, vh - 30)
                canvas[y2 + 25: y2 + 25 + noise.shape[0], vx + 2: vx + 2 + noise.shape[1]] = noise
                cv2.putText(canvas, "SEARCHING...", (vx + vw // 2 - 90, y2 + vh // 2), self.FONT, 2, self.C_YELLOW, 2)
        else:
            # Wyłączona w konfigu -> Czerń + napis OFFLINE
            cv2.putText(canvas, "CAMERA DISABLED", (vx + vw // 2 - 120, y2 + vh // 2), self.FONT, 2, (50, 50, 50), 2)
            cv2.putText(canvas, "(Enable in Launcher)", (vx + vw // 2 - 100, y2 + vh // 2 + 30), self.FONT, 1,
                        (50, 50, 50), 1)

        return canvas