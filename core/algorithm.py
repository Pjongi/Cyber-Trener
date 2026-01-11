# core/algorithm.py
import numpy as np


class Algorithm:
    @staticmethod
    def calculate_angle_2d(a, b, c):
        a = np.array(a[:2])
        b = np.array(b[:2])
        c = np.array(c[:2])

        ba = a - b
        bc = c - b

        angle_ba = np.arctan2(ba[1], ba[0])
        angle_bc = np.arctan2(bc[1], bc[0])

        angle = angle_ba - angle_bc
        angle = np.abs(np.degrees(angle))

        if angle > 180.0:
            angle = 360.0 - angle

        return angle


class SignalSmoother:
    """
    Inteligentny filtr (Smart Smoothing).
    Dostosowuje siłę wygładzania dynamicznie:
    - Gdy stoisz w miejscu -> Duże wygładzanie (brak drgań).
    - Gdy robisz szybki ruch -> Małe wygładzanie (brak opóźnień).
    """

    def __init__(self, min_alpha=0.05, max_alpha=0.8, threshold=10.0):
        """
        min_alpha: Siła wygładzania przy braku ruchu (im mniej tym stabilniej).
        max_alpha: Siła wygładzania przy szybkim ruchu (im więcej tym szybciej).
        threshold: Próg różnicy kątów, przy którym przełączamy się na szybki tryb.
        """
        self.min_alpha = min_alpha
        self.max_alpha = max_alpha
        self.threshold = threshold
        self.filtered_value = None

    def update(self, new_value):
        if self.filtered_value is None:
            self.filtered_value = new_value
            return new_value

        # Oblicz różnicę (jak szybko zmienił się kąt w tej klatce)
        diff = abs(new_value - self.filtered_value)

        # Dynamicznie dobierz alpha
        # Interpolacja liniowa między min_alpha a max_alpha w zależności od prędkości ruchu
        factor = min(1.0, diff / self.threshold)
        alpha = self.min_alpha + (self.max_alpha - self.min_alpha) * factor

        # Filtr wykładniczy
        self.filtered_value = (alpha * new_value) + ((1 - alpha) * self.filtered_value)

        return self.filtered_value