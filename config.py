# config.py

# --- WARTOŚCI DOMYŚLNE (Nadpisywane przez Launcher) ---
CAM_FRONT_ID = 0
CAM_SIDE_ID = None
USE_DUAL_CAMERA = False

# --- KONFIGURACJA MODELI AI (Nowe) ---
# YOLO: 'n' (nano), 's' (small), 'm' (medium), 'l' (large)
MODEL_YOLO_SIZE = 'n'
# MediaPipe: 0 (Lite), 1 (Full), 2 (Heavy)
MODEL_MP_COMPLEXITY = 1

# --- USTAWIENIA GUI ---
WINDOW_NAME = "Cyber Trener v4.0 - Refactored"
WIDTH = 1280
HEIGHT = 720

# Wartości startowe dla suwaków
MIN_CONFIDENCE = 0.5
SMOOTH_FACTOR = 0.15

# --- MAPOWANIE YOLO (Format COCO) ---
KP_YOLO = {
    "L_SH": 5, "R_SH": 6, "L_EL": 7, "R_EL": 8, "L_WR": 9, "R_WR": 10,
    "L_HIP": 11, "R_HIP": 12, "L_KN": 13, "R_KN": 14, "L_ANK": 15, "R_ANK": 16
}