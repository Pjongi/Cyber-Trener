import cv2
import numpy as np
import datetime


class CyberDashboard:
    def __init__(self, width=1920, height=1080):
        self.W = width
        self.H = height
        self.side_w = 500
        self.FONT = cv2.FONT_HERSHEY_PLAIN

        # Kolory
        self.C_BG = (5, 10, 5)
        self.C_MAIN = (0, 255, 0)
        self.C_DIM = (0, 80, 0)
        self.C_ALERT = (0, 0, 255)
        self.C_WHITE = (200, 255, 200)
        self.C_YELLOW = (0, 255, 255)

        # --- OPTYMALIZACJA: Pre-renderowanie tła ---
        self.static_bg = np.zeros((self.H, self.W, 3), dtype=np.uint8)
        self.static_bg[:] = self.C_BG
        self._draw_static_interface()

    def _draw_box(self, img, x, y, w, h, title=""):
        cv2.rectangle(img, (x, y), (x + w, y + h), self.C_DIM, 1)
        cv2.rectangle(img, (x, y), (x + w, y + h), self.C_MAIN, 1)
        # Rogi
        l = 15
        for px, py in [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]:
            dx = -l if px > x else l
            dy = -l if py > y else l
            cv2.line(img, (px, py), (px + dx, py), self.C_MAIN, 2)
            cv2.line(img, (px, py), (px, py + dy), self.C_MAIN, 2)

        if title:
            cv2.putText(img, f" {title} ", (x + 20, y + 10), self.FONT, 1.2, self.C_MAIN, 1)

    def _draw_static_interface(self):
        """Rysuje elementy, które się nie zmieniają"""
        # Nagłówek
        self._draw_box(self.static_bg, 20, 20, self.W - 40, 50)

        # Panel Boczny
        ph = self.H - 110
        self._draw_box(self.static_bg, 20, 90, self.side_w, ph, "TELEMETRIA (L/P)")

        # Ramki wideo
        vx = self.side_w + 40
        vw = self.W - vx - 20
        vh = int((self.H - 120) / 2)

        self._draw_box(self.static_bg, vx, 90, vw, vh, "KAMERA GLOWNA")
        self._draw_box(self.static_bg, vx, 90 + vh + 10, vw, vh, "KAMERA BOCZNA")

        # Stopka
        cv2.putText(self.static_bg, "[Q] WYJSCIE", (50, 90 + ph - 30), self.FONT, 1.2, (100, 100, 100), 1)

    def compose(self, frame_main, angles_dict, status, fps):
        # Kopiujemy gotowe tło (bardzo szybkie)
        canvas = self.static_bg.copy()

        # 1. Dane dynamiczne - Nagłówek
        date = datetime.datetime.now().strftime("%H:%M:%S")
        cv2.putText(canvas, f"SYSTEM ONLINE | FPS: {int(fps)} | {date}", (50, 55), self.FONT, 1.4, self.C_MAIN, 1)

        # 2. Panel Boczny
        y = 160
        for key, val in angles_dict.items():
            if "Bark (P)" in key or "Biodro (P)" in key: y += 20

            # Label
            cv2.putText(canvas, key, (40, y), self.FONT, 1.2, self.C_WHITE, 1)

            if val is None:
                cv2.putText(canvas, "---", (400, y), self.FONT, 1.2, (100, 100, 100), 1)
            else:
                color = self.C_YELLOW if 80 < val < 170 else self.C_ALERT
                cv2.putText(canvas, f"{int(val)}", (400, y), self.FONT, 1.2, color, 1)
                # Pasek
                bar_w = int((val / 180) * 200)
                cv2.rectangle(canvas, (180, y - 10), (180 + bar_w, y), color, -1)

            y += 40

        # Status
        cv2.putText(canvas, status, (40, y + 50), self.FONT, 2.0, self.C_WHITE, 2)

        # 3. Wideo (Wklejanie)
        vx = self.side_w + 40
        vw = self.W - vx - 20
        vh = int((self.H - 120) / 2)

        if frame_main is not None:
            rs = cv2.resize(frame_main, (vw - 6, vh - 30))
            canvas[90 + 25: 90 + 25 + vh - 30, vx + 3: vx + 3 + vw - 6] = rs

        return canvas