import cv2
import numpy as np
import datetime


class CyberDashboard:
    def __init__(self, width=1920, height=1080):
        self.W = width
        self.H = height

        # Kolory
        self.C_BG = (5, 10, 5)
        self.C_MAIN = (0, 255, 0)
        self.C_DIM = (0, 80, 0)
        self.C_ALERT = (0, 0, 255)
        self.C_WHITE = (200, 255, 200)
        self.C_YELLOW = (0, 255, 255)

        self.side_w = 480  # Szerokość panelu bocznego
        self.FONT = cv2.FONT_HERSHEY_PLAIN

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
            # Pasek postępu
            bar_max = w - 130
            bar_cur = int((value / 180) * bar_max)
            bar_cur = max(0, min(bar_cur, bar_max))
            cv2.rectangle(img, (x + 10, y + 8), (x + 10 + bar_cur, y + 14), self.C_MAIN, -1)

    def compose(self, frame_front, frame_side, angles_dict, status, fps):
        # Tworzymy puste płótno 1920x1080
        canvas = np.zeros((self.H, self.W, 3), dtype=np.uint8)
        canvas[:] = self.C_BG

        # --- 1. NAGŁÓWEK ---
        self._draw_box(canvas, 20, 20, self.W - 40, 50)
        date = datetime.datetime.now().strftime("%H:%M:%S")
        head = f"CYBER TRENER SYSTEM | FPS: {int(fps)} | {date}"
        cv2.putText(canvas, head, (50, 55), self.FONT, 1.4, self.C_MAIN, 1)

        # --- 2. PANEL BOCZNY (WYNIKI) ---
        px, py = 20, 90
        ph = self.H - 110
        self._draw_box(canvas, px, py, self.side_w, ph, "ANALIZA RUCHU")

        y = py + 60
        gap = 40
        keys_order = [
            "Lokiec (L)", "Lokiec (P)", "Bark (L)", "Bark (P)",
            "Biodro (L)", "Biodro (P)", "Kolano (L)", "Kolano (P)"
        ]

        for key in keys_order:
            val = angles_dict.get(key)
            if "Bark (P)" in key or "Biodro (P)" in key: y += 15
            self._draw_data_row(canvas, px + 10, y, self.side_w - 20, key, val)
            y += gap

        # Status
        y += 40
        cv2.putText(canvas, "STATUS:", (px + 20, y), self.FONT, 1.2, self.C_WHITE, 1)
        y += 40
        cv2.putText(canvas, status, (px + 20, y), self.FONT, 2.0, self.C_MAIN, 2)

        # --- 3. OBSZAR WIDEO (Prawa strona) ---
        # Dzielimy pozostałą wysokość na dwa okna
        video_area_x = self.side_w + 40
        video_area_w = self.W - video_area_x - 20

        # Wysokość jednego okna wideo (żeby zmieściły się dwa w pionie)
        video_h = (self.H - 120) // 2

        # KAMERA 1 (GÓRA)
        self._draw_box(canvas, video_area_x, 90, video_area_w, video_h, "CAM 1: FRONT (USB)")
        if frame_front is not None:
            # Skalowanie z zachowaniem proporcji lub rozciągnięcie by wypełnić ramkę
            resized = cv2.resize(frame_front, (video_area_w - 4, video_h - 30))
            canvas[90 + 25: 90 + 25 + resized.shape[0], video_area_x + 2: video_area_x + 2 + resized.shape[1]] = resized

        # KAMERA 2 (DÓŁ)
        y_cam2 = 90 + video_h + 10
        self._draw_box(canvas, video_area_x, y_cam2, video_area_w, video_h, "CAM 2: SIDE (WIFI)")
        if frame_side is not None:
            resized_side = cv2.resize(frame_side, (video_area_w - 4, video_h - 30))
            canvas[y_cam2 + 25: y_cam2 + 25 + resized_side.shape[0],
            video_area_x + 2: video_area_x + 2 + resized_side.shape[1]] = resized_side
        else:
            cv2.putText(canvas, "BRAK SYGNALU", (video_area_x + 100, y_cam2 + 100), self.FONT, 2, (50, 50, 50), 2)

        return canvas