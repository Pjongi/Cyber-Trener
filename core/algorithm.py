import numpy as np


class Algorithm:
    @staticmethod
    def calculate_angle_2d(a, b, c):
        # ... (ta część zostaje bez zmian, używamy wersji 2D) ...
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
    Zaawansowany filtr wykładniczy (Exponential Moving Average).
    Działa lepiej niż zwykła średnia - szybciej reaguje na ruch,
    ale mocno tłumi drobne drgania.
    """

    def __init__(self, alpha=0.1):
        """
        alpha: Współczynnik wygładzania (0.0 do 1.0).
        - 0.1: Bardzo duże wygładzanie (stabilne, ale lekkie opóźnienie).
        - 0.5: Średnie wygładzanie.
        - 0.9: Prawie brak wygładzania (bardzo czułe).
        """
        self.alpha = alpha
        self.filtered_value = None

    def update(self, new_value):
        # Jeśli to pierwsza wartość, inicjalizujemy nią filtr
        if self.filtered_value is None:
            self.filtered_value = new_value
        else:
            # Wzór na filtr wykładniczy:
            # Nowy_Wynik = (alpha * Nowa_Wartość) + ((1 - alpha) * Stary_Wynik)
            self.filtered_value = (self.alpha * new_value) + ((1 - self.alpha) * self.filtered_value)

        return self.filtered_value