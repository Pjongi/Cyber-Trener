import cv2
import numpy as np
import datetime


class CyberDashboard:
    def __init__(self, width=1920, height=1080):
        self.W = width
        self.H = height

        # Kolory (Cyberpunk / Matrix Theme)
        self.C_BG = (5, 10, 5)
        self.C_MAIN = (0, 255, 0)  # Zieleń
        self.C_DIM = (0, 80, 0)  # Ciemna zieleń
        self.C_ALERT = (0, 0, 255)  # Czerwień
        self.C_WHITE = (200, 255, 200)
        self.C_YELLOW = (0, 255, 255)

        self.side_w = 480  # Jeszcze szerszy panel, żeby pomieścić dane L/P
        self.FONT = cv2.FONT_HERSHEY_PLAIN

    def _draw_box(self, img, x, y, w, h, title=""):
        # Tło i Ramka
        cv2.rectangle(img, (x, y), (x + w, y + h), self.C_DIM, 1)
        cv2.rectangle(img, (x, y), (x + w, y + h), self.C_MAIN, 1)
        # Ozdobniki (Rogi)
        l = 15
        cv2.line(img, (x, y), (x + l, y), self.C_MAIN, 2)
        cv2.line(img, (x, y), (x, y + l), self.C_MAIN, 2)
        cv2.line(img, (x + w, y), (x + w - l, y), self.C_MAIN, 2)
        cv2.line(img, (x + w, y), (x + w, y + l), self.C_MAIN, 2)
        cv2.line(img, (x, y + h), (x + l, y + h), self.C_MAIN, 2)
        cv2.line(img, (x, y + h), (x, y + h - l), self.C_MAIN, 2)
        cv2.line(img, (x + w, y + h), (x + w - l, y + h), self.C_MAIN, 2)
        cv2.line(img, (x + w, y + h), (x + w, y + h - l), self.C_MAIN, 2)

        if title:
            cv2.putText(img, f" {title} ", (x + 20, y + 10), self.FONT, 1.2, self.C_MAIN, 1)

    def _draw_data_row(self, img, x, y, w, label, value):
        """Rysuje wiersz. Jeśli value jest None, pokazuje '---'"""
        # Label
        cv2.putText(img, label, (x + 10, y), self.FONT, 1.2, self.C_WHITE, 1)

        if value is None:
            # Brak danych
            cv2.putText(img, "---", (x + w - 80, y), self.FONT, 1.2, (100, 100, 100), 1)
            cv2.rectangle(img, (x + 10, y + 8), (x + w - 10, y + 14), (30, 30, 30), -1)
        else:
            # Wartość
            val_str = f"{int(value)}"
            cv2.putText(img, val_str, (x + w - 80, y), self.FONT, 1.2, self.C_YELLOW, 1)

            # Pasek
            bar_max = w - 20
            bar_cur = int((value / 180) * bar_max)
            bar_cur = max(0, min(bar_cur, bar_max))

            # Kolor paska (zielony jeśli > 150, czerwony jeśli < 90 - przykładowa logika)
            c_bar = self.C_MAIN
            if value < 90: c_bar = self.C_ALERT

            cv2.rectangle(img, (x + 10, y + 8), (x + 10 + bar_max, y + 14), self.C_DIM, -1)
            cv2.rectangle(img, (x + 10, y + 8), (x + 10 + bar_cur, y + 14), c_bar, -1)

    def compose(self, frame_main, angles_dict, status, fps):
        canvas = np.zeros((self.H, self.W, 3), dtype=np.uint8)
        canvas[:] = self.C_BG

        # 1. Nagłówek
        self._draw_box(canvas, 20, 20, self.W - 40, 50)
        date = datetime.datetime.now().strftime("%H:%M:%S")
        head = f"CYBER TRENER SYSTEM  |  CPU: ONLINE  |  FPS: {int(fps)}  |  {date}"
        cv2.putText(canvas, head, (50, 55), self.FONT, 1.4, self.C_MAIN, 1)

        # 2. Panel Boczny (Dane)
        px, py = 20, 90
        ph = self.H - 110
        self._draw_box(canvas, px, py, self.side_w, ph, "PARAMETRY RUCHU (L/P)")

        # Lista kątów
        y = py + 60
        gap = 40  # Mniejszy odstęp żeby zmieścić 8 wierszy

        # Kolejność wyświetlania
        keys_order = [
            "Lokiec (L)", "Lokiec (P)",
            "Bark (L)", "Bark (P)",
            "Biodro (L)", "Biodro (P)",
            "Kolano (L)", "Kolano (P)"
        ]

        for key in keys_order:
            val = angles_dict.get(key)
            # Rysujemy separator co 2 elementy (żeby oddzielić ręce od nóg)
            if "Bark (P)" in key or "Biodro (P)" in key:
                y += 10

            self._draw_data_row(canvas, px + 10, y, self.side_w - 20, key, val)
            y += gap

        # Status na dole panelu
        cv2.line(canvas, (px + 20, y + 10), (px + self.side_w - 20, y + 10), self.C_MAIN, 1)
        y += 50
        cv2.putText(canvas, "ANALIZA:", (px + 20, y), self.FONT, 1.2, self.C_WHITE, 1)
        y += 40

        c_stat = self.C_MAIN
        if "BLAD" in status:
            c_stat = self.C_ALERT
        elif "BRAK" in status:
            c_stat = (100, 100, 100)

        cv2.putText(canvas, status, (px + 20, y), self.FONT, 2.0, c_stat, 2)

        # Footer (Instrukcja)
        cv2.putText(canvas, "WYJSCIE: [Q]  |  RESET: [R]", (px + 30, py + ph - 20), self.FONT, 1.1, (150, 150, 150), 1)

        # 3. Wideo (Reszta ekranu)
        vx = self.side_w + 40
        vy = 90
        vw = self.W - vx - 20
        vh = int(vw * 9 / 16)  # Zachowujemy 16:9 dla głównej kamery

        # Jeśli wideo jest za wysokie i wychodzi poza ekran, skalujemy w dół
        if vy + vh > self.H - 20:
            vh = self.H - vy - 40
            vw = int(vh * 16 / 9)

        self._draw_box(canvas, vx, vy, vw, vh, "PODGLAD GLOWNY")

        if frame_main is not None:
            # Resize
            resized = cv2.resize(frame_main, (vw - 6, vh - 30))
            canvas[vy + 25: vy + 25 + vh - 30, vx + 3: vx + 3 + vw - 6] = resized

            # Celownik (ozdobnik)
            cx, cy = vx + vw // 2, vy + vh // 2
            cv2.line(canvas, (cx - 20, cy), (cx + 20, cy), self.C_MAIN, 1)
            cv2.line(canvas, (cx, cy - 20), (cx, cy + 20), self.C_MAIN, 1)

        return canvas