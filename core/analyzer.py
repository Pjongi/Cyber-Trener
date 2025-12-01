# core/analyzer.py
from core.algorithm import Algorithm, SignalSmoother
import config


class MotionAnalyzer:
    def __init__(self):
        # Definicja stawów do śledzenia
        self.joints = [
            "Lokiec (L)", "Lokiec (P)",
            "Bark (L)", "Bark (P)",
            "Biodro (L)", "Biodro (P)",
            "Kolano (L)", "Kolano (P)"
        ]

        # Inicjalizacja wygładzania dla każdego stawu
        self.smoothers = {name: SignalSmoother(alpha=0.15) for name in self.joints}

        # Przechowywanie aktualnych wartości
        self.current_angles = {k: None for k in self.joints}

    def update_params(self, smooth_factor):
        """Aktualizacja siły wygładzania na żywo z suwaka"""
        for s in self.smoothers.values():
            s.alpha = smooth_factor

    def process_yolo(self, keypoints, min_conf):
        """Przetwarza wyniki YOLO i zwraca zaktualizowane kąty"""
        kp_map = config.KP_YOLO

        # Helper do obliczeń
        def calc(name, k1, k2, k3):
            p1, p2, p3 = keypoints[kp_map[k1]], keypoints[kp_map[k2]], keypoints[kp_map[k3]]
            # Sprawdzenie pewności (confidence > min_conf)
            if p1[2] > min_conf and p2[2] > min_conf and p3[2] > min_conf:
                raw_angle = Algorithm.calculate_angle_2d(p1[:2], p2[:2], p3[:2])
                return self.smoothers[name].update(raw_angle)
            return None

        # Jeśli nie wykryto lewego barku, uznajemy że nikogo nie ma
        if keypoints is None or keypoints[kp_map["L_SH"]][2] < min_conf:
            return False

        # Aktualizacja słownika kątów
        self.current_angles["Lokiec (L)"] = calc("Lokiec (L)", "L_SH", "L_EL", "L_WR")
        self.current_angles["Lokiec (P)"] = calc("Lokiec (P)", "R_SH", "R_EL", "R_WR")
        self.current_angles["Bark (L)"] = calc("Bark (L)", "L_HIP", "L_SH", "L_EL")
        self.current_angles["Bark (P)"] = calc("Bark (P)", "R_HIP", "R_SH", "R_EL")
        self.current_angles["Biodro (L)"] = calc("Biodro (L)", "L_SH", "L_HIP", "L_KN")
        self.current_angles["Biodro (P)"] = calc("Biodro (P)", "R_SH", "R_HIP", "R_KN")
        self.current_angles["Kolano (L)"] = calc("Kolano (L)", "L_HIP", "L_KN", "L_ANK")
        self.current_angles["Kolano (P)"] = calc("Kolano (P)", "R_HIP", "R_KN", "R_ANK")

        return True

    def process_mediapipe(self, landmarks, width, height, min_conf):
        """Przetwarza wyniki MediaPipe i nadpisuje kluczowe kąty (Side View)"""

        def get_pos(idx):
            return [landmarks[idx].x * width, landmarks[idx].y * height]

        def is_visible(idx):
            return landmarks[idx].visibility > min_conf

        def calc(name, i1, i2, i3):
            if is_visible(i1) and is_visible(i2) and is_visible(i3):
                raw = Algorithm.calculate_angle_2d(get_pos(i1), get_pos(i2), get_pos(i3))
                return self.smoothers[name].update(raw)
            return None  # Jeśli nie widać, nie zwracamy nic (zostanie stara wartość z YOLO)

        # Nadpisujemy tylko to, co lepiej widać z boku
        vals = {
            "Kolano (L)": calc("Kolano (L)", 23, 25, 27),
            "Kolano (P)": calc("Kolano (P)", 24, 26, 28),
            "Biodro (L)": calc("Biodro (L)", 11, 23, 25)
        }

        # Aktualizujemy tylko te, które udało się obliczyć
        for k, v in vals.items():
            if v is not None:
                self.current_angles[k] = v

        return True