# config.py

# ==========================================
# KONFIGURACJA ŹRÓDEŁ OBRAZU
# ==========================================
# Możesz używać:
# 1. Liczb (int): np. 0, 1 (Kamery USB wpięte do komputera)
# 2. Tekstu (str): np. "http://..." (IP Webcam z telefonu)

# --- KAMERA 1: FRONT (Widok Główny) ---
# Odkomentuj jedną z opcji:

# Opcja A: Kamera USB (Domyślna w laptopie)
CAM_FRONT_ID = 0

# Opcja B: Kamera IP (Telefon)
# CAM_FRONT_ID = "http://192.168.0.101:8080/video"


# --- KAMERA 2: SIDE (Widok Boczny) ---
# Odkomentuj jedną z opcji:

# Opcja A: Druga kamera USB (np. na kablu)
# CAM_SIDE_ID = 1

# Opcja B: Kamera IP (Telefon)
CAM_SIDE_ID = "http://10.77.20.83:8080/video"


# --- TRYB PRACY ---
# True = Uruchom obie kamery (jeśli zdefiniowane)
# False = Tylko kamera FRONT
USE_DUAL_CAMERA = True


# --- POZOSTAŁE USTAWIENIA ---
WINDOW_NAME = "Cyber Trener v2.2 - Hybrid Source"
WIDTH = 1280
HEIGHT = 720
MIN_CONFIDENCE = 0.5