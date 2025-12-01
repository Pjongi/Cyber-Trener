# main.py
from ui.launcher import CyberLauncher
from core.engine import CyberEngine
import sys

def main():
    # 1. Konfiguracja (Launcher)
    launcher = CyberLauncher()
    if not launcher.should_start:
        print("[SYSTEM] Anulowano uruchamianie.")
        sys.exit(0)

    # 2. Uruchomienie Silnika (Engine)
    # Cała trudna logika jest teraz ukryta w klasie CyberEngine
    try:
        app = CyberEngine()
        app.run()
    except Exception as e:
        print(f"[CRITICAL ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("[SYSTEM] Proces zakonczony.")

if __name__ == "__main__":
    main()