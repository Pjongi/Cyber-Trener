# config.py

# --- PLIK ZAPISU USTAWIEŃ (Tworzony automatycznie) ---
SETTINGS_FILE = "settings.json"

# --- TRYBY PRACY ---
# 'LIVE'   - Analiza z kamery na żywo + AI
# 'RECORD' - Tylko nagrywanie surowego wideo (bez AI, wysoki FPS)
# 'FILE'   - Analiza nagranych wcześniej plików wideo
MODE = 'LIVE'

# --- WEJŚCIE (PLIKI WIDEO) ---
# Używane tylko w trybie 'FILE'
INPUT_FILE_FRONT = ""          # Ścieżka do pliku wideo (PRZÓD)
INPUT_FILE_SIDE = ""           # Ścieżka do pliku wideo (BOK)

# --- WYJŚCIE (NAGRYWANIE) ---
# Bazowa nazwa pliku. System doda _front.avi i _side.avi
OUTPUT_BASE_NAME = "recording"
RECORD_RESULT = False          # Czy zapisywać też wynik z nałożonym Dashboardem?

# --- WARTOŚCI DOMYŚLNE (KAMERY) ---
CAM_FRONT_ID = 0
CAM_SIDE_ID = 1
USE_DUAL_CAMERA = False

# --- KONFIGURACJA AI ---
# YOLO: 'n' (nano), 's' (small), 'm' (medium), 'l' (large)
MODEL_YOLO_SIZE = 'n'
# MediaPipe: 0 (Lite), 1 (Full), 2 (Heavy)
MODEL_MP_COMPLEXITY = 1

# --- USTAWIENIA GUI ---
WINDOW_NAME = "Cyber Trener"
WIDTH = 1280
HEIGHT = 720
MIN_CONFIDENCE = 0.25
SMOOTH_FACTOR = 0.15

# --- MAPOWANIE YOLO (Format COCO) ---
KP_YOLO = {
    "L_SH": 5, "R_SH": 6, "L_EL": 7, "R_EL": 8, "L_WR": 9, "R_WR": 10,
    "L_HIP": 11, "R_HIP": 12, "L_KN": 13, "R_KN": 14, "L_ANK": 15, "R_ANK": 16
}