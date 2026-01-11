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

        # Inicjalizacja wygładzania (Smart Smoothing)
        # min_alpha=0.05 (bardzo stabilne statycznie)
        # max_alpha=0.5 (responsywne w ruchu - wartość domyślna)
        self.smoothers = {
            name: SignalSmoother(min_alpha=0.05, max_alpha=0.5, threshold=15.0)
            for name in self.joints
        }

        # Słownik na aktualne kąty
        self.current_angles = {}

    def update_params(self, smooth_factor):
        """
        Aktualizacja z suwaka.
        Suwak w Dashboardzie (smooth_val) steruje teraz 'max_alpha',
        czyli jak bardzo system ma być responsywny w ruchu.
        """
        # smooth_factor z suwaka to 0.0 - 1.0.
        # Mapujemy to na sensowny zakres max_alpha (np. 0.1 do 0.9)
        new_max = max(0.1, float(smooth_factor))

        for s in self.smoothers.values():
            s.max_alpha = new_max

    def _set_angle(self, source, name, value):
        """Pomocnicza funkcja do zapisywania kąta z odpowiednim prefiksem"""
        if value is not None:
            # 1. Zapisz z prefiksem dla Trenera (np. "FRONT_Lokiec (L)")
            key_prefixed = f"{source}_{name}"
            self.current_angles[key_prefixed] = value

            # 2. Zapisz bez prefiksu dla Dashboardu (wyświetlanie w tabeli)
            self.current_angles[name] = value

    def process_yolo(self, keypoints, min_conf):
        """Przetwarza wyniki YOLO (Kamera PRZEDNIA)"""
        kp_map = config.KP_YOLO

        def calc(name, k1, k2, k3):
            if keypoints is None: return None
            p1, p2, p3 = keypoints[kp_map[k1]], keypoints[kp_map[k2]], keypoints[kp_map[k3]]
            if p1[2] > min_conf and p2[2] > min_conf and p3[2] > min_conf:
                raw_angle = Algorithm.calculate_angle_2d(p1[:2], p2[:2], p3[:2])
                if name in self.smoothers:
                    return self.smoothers[name].update(raw_angle)
                return raw_angle
            return None

        if keypoints is None: return False

        # Obliczamy i zapisujemy jako FRONT
        self._set_angle("FRONT", "Lokiec (L)", calc("Lokiec (L)", "L_SH", "L_EL", "L_WR"))
        self._set_angle("FRONT", "Lokiec (P)", calc("Lokiec (P)", "R_SH", "R_EL", "R_WR"))
        self._set_angle("FRONT", "Bark (L)", calc("Bark (L)", "L_HIP", "L_SH", "L_EL"))
        self._set_angle("FRONT", "Bark (P)", calc("Bark (P)", "R_HIP", "R_SH", "R_EL"))
        self._set_angle("FRONT", "Biodro (L)", calc("Biodro (L)", "L_SH", "L_HIP", "L_KN"))
        self._set_angle("FRONT", "Biodro (P)", calc("Biodro (P)", "R_SH", "R_HIP", "R_KN"))
        self._set_angle("FRONT", "Kolano (L)", calc("Kolano (L)", "L_HIP", "L_KN", "L_ANK"))
        self._set_angle("FRONT", "Kolano (P)", calc("Kolano (P)", "R_HIP", "R_KN", "R_ANK"))

        return True

    def process_mediapipe(self, landmarks, width, height, min_conf):
        """Przetwarza wyniki MediaPipe (Kamera BOCZNA)"""

        def get_pos(idx):
            return [landmarks[idx].x * width, landmarks[idx].y * height]

        def is_visible(idx):
            return landmarks[idx].visibility > min_conf

        def calc(name, i1, i2, i3):
            if is_visible(i1) and is_visible(i2) and is_visible(i3):
                raw = Algorithm.calculate_angle_2d(get_pos(i1), get_pos(i2), get_pos(i3))
                if name in self.smoothers:
                    return self.smoothers[name].update(raw)
                return raw
            return None

        # Obliczamy i zapisujemy jako SIDE
        self._set_angle("SIDE", "Kolano (L)", calc("Kolano (L)", 23, 25, 27))
        self._set_angle("SIDE", "Kolano (P)", calc("Kolano (P)", 24, 26, 28))
        self._set_angle("SIDE", "Biodro (L)", calc("Biodro (L)", 11, 23, 25))
        self._set_angle("SIDE", "Biodro (P)", calc("Biodro (P)", 12, 24, 26))

        # Opcjonalnie plecy/barki z boku
        self._set_angle("SIDE", "Bark (L)", calc("Bark (L)", 23, 11, 13))

        return True