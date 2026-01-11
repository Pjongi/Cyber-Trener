import json
import time
import winsound
import os
from datetime import datetime


class CyberTrainer:
    def __init__(self, config_file="poses.json"):
        self.state = "IDLE"
        self.config = self._load_config(config_file)

        # Zmienne stanu
        self.current_ex_idx = 0
        self.start_time = None
        self.hold_start = None
        self.error_start = None

        self.error_buffer = 2.0  # Zwiększamy tolerancję czasową do 2s
        self.is_holding = False

        self.session_data = []
        self.current_ex_stats = {"errors": 0}

        # Dźwięki
        self.SND_GOOD = (1000, 100)
        self.SND_BAD = (400, 300)
        self.SND_START = (1500, 500)

    def _load_config(self, path):
        if not os.path.exists(path):
            return {"t_pose_trigger": {}, "exercises": []}
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def update(self, current_angles):
        """
        current_angles: Słownik zawierający kąty.
        Ważne: Musi być zaktualizowany o źródło, np.:
        {
          "Kolano (L)": 180,  <-- Wartość domyślna (np. z FRONT)
          "SIDE_Kolano (L)": 175  <-- Wartość konkretna z SIDE (jeśli dostępna)
        }
        """
        status_info = {
            "state": self.state,
            "message": "",
            "color": (255, 255, 255),
            "progress": 0.0,
            "ref_image": None,
            "feedback": []
        }

        # 1. CZEKANIE NA START (T-POSE)
        if self.state == "IDLE":
            t_cfg = self.config.get("t_pose_trigger")
            status_info["message"] = f"START: {t_cfg['name']}"
            status_info["color"] = (0, 255, 255)  # Żółty

            is_ok, diffs = self._check_pose(current_angles, t_cfg["joints"], t_cfg["tolerance"])

            if is_ok:
                if self.hold_start is None: self.hold_start = time.time()
                held_time = time.time() - self.hold_start
                status_info["progress"] = held_time / t_cfg["hold_time"]
                status_info["color"] = (0, 255, 0)  # Zielony

                if held_time >= t_cfg["hold_time"]:
                    self._start_session()
            else:
                self.hold_start = None
                # Wyświetl max 2 błędy na raz, żeby nie zasłaniać ekranu
                status_info["feedback"] = diffs[:2]

        # 2. TRWA ĆWICZENIE
        elif self.state == "EXERCISE":
            ex = self.config["exercises"][self.current_ex_idx]
            status_info["ref_image"] = ex.get("img_path")
            status_info["message"] = ex["name"]

            is_ok, diffs = self._check_pose(current_angles, ex["joints"], ex["tolerance"])

            if is_ok:
                self.error_start = None
                status_info["color"] = (0, 255, 0)  # Zielony
                if not self.is_holding:
                    self.is_holding = True
            else:
                # Logika błędu
                if self.error_start is None: self.error_start = time.time()
                time_in_error = time.time() - self.error_start

                if time_in_error > self.error_buffer:
                    self.is_holding = False
                    status_info["color"] = (0, 0, 255)  # Czerwony
                    status_info["feedback"] = diffs

                    if int(time_in_error * 10) % 30 == 0:  # Dźwięk co 3 sek
                        winsound.Beep(*self.SND_BAD)
                        self.current_ex_stats["errors"] += 1

            # Progress czasu
            elapsed = time.time() - self.start_time
            total_dur = ex["duration"]
            remaining = max(0, total_dur - elapsed)
            status_info["progress"] = 1.0 - (remaining / total_dur)

            if remaining <= 0:
                self._next_exercise()

        elif self.state == "FINISHED":
            status_info["message"] = "KONIEC TRENINGU!"
            status_info["color"] = (0, 255, 0)
            status_info["progress"] = 1.0

        return status_info

    def _check_pose(self, current_angles, target_joints, global_tolerance):
        errors = []
        if not current_angles: return False, ["Brak osoby"]

        all_ok = True

        for joint_name, data in target_joints.items():
            target_val = data["target"]
            source = data.get("source", "FRONT")  # Domyślnie FRONT

            # Budujemy klucz do słownika kątów
            # W Analyzerze musimy to tak zapisać: "FRONT_Lokiec (L)" lub "SIDE_Lokiec (L)"
            lookup_key = f"{source}_{joint_name}"

            cur_val = current_angles.get(lookup_key)

            # Jeśli nie znaleziono z prefixem, szukamy bez (kompatybilność wsteczna)
            if cur_val is None:
                cur_val = current_angles.get(joint_name)

            if cur_val is None:
                # Jeśli kluczowy staw jest niewidoczny -> Błąd
                # Możesz to zmienić na `continue` jeśli chcesz być łagodniejszy
                return False, [f"Nie widać: {joint_name} ({source})"]

            diff = abs(cur_val - target_val)
            # Można nadpisać tolerancję dla konkretnego stawu w JSON, jeśli nie, bierzemy globalną
            tol = data.get("tolerance", global_tolerance)

            if diff > tol:
                all_ok = False
                direction = "zwieksz" if cur_val < target_val else "zmniejsz"
                # Dodajemy info, która kamera to widzi
                cam_short = "F" if source == "FRONT" else "S"
                errors.append(f"[{cam_short}] {joint_name}: {int(cur_val)}->{target_val}")

        return all_ok, errors

    def _start_session(self):
        self.state = "EXERCISE"
        self.current_ex_idx = 0
        self.start_time = time.time()
        self.session_data = []
        winsound.Beep(*self.SND_START)

    def _next_exercise(self):
        ex_name = self.config["exercises"][self.current_ex_idx]["name"]
        self.session_data.append({
            "name": ex_name,
            "errors": self.current_ex_stats["errors"]
        })
        self.current_ex_stats = {"errors": 0}

        self.current_ex_idx += 1
        if self.current_ex_idx >= len(self.config["exercises"]):
            self._finish_session()
        else:
            self.start_time = time.time()
            winsound.Beep(*self.SND_START)

    def _finish_session(self):
        self.state = "FINISHED"
        winsound.Beep(2000, 800)
        self._save_report()

    def _save_report(self):
        filename = f"raport_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        with open(filename, "w", encoding='utf-8') as f:
            f.write("=== RAPORT CYBER TRENER ===\n")
            f.write(f"Data: {datetime.now()}\n\n")
            total = 0
            for item in self.session_data:
                f.write(f"{item['name']}: {item['errors']} bledow\n")
                total += item['errors']
            f.write(f"\nSUMA BLEDOW: {total}\n")