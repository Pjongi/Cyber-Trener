import cv2
import threading
import time


class CameraStream:
    def __init__(self, src=0, name="Camera"):
        self.src = src
        self.name = name
        self.stream = None
        self.frame = None
        self.grabbed = False
        self.stopped = False
        self.error = False

        # Próba pierwszego połączenia przy inicjalizacji
        self._connect()

    def start(self):
        """Uruchamia wątek i zwraca obiekt (chaining)"""
        t = threading.Thread(target=self.update, args=())
        t.daemon = True  # Wątek zginie razem z głównym programem
        t.start()
        return self

    def _connect(self):
        """Prywatna metoda do nawiązywania połączenia (z obsługą hybrydową)"""
        if self.stream is not None:
            self.stream.release()

        print(f"[{self.name}] Próba łączenia z {self.src}...")
        try:
            self.stream = cv2.VideoCapture(self.src)

            # --- OPTYMALIZACJA HYBRYDOWA ---
            if isinstance(self.src, int):
                # USB: Priorytet - Szybkość (MJPG, HD)
                self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            else:
                # IP Webcam: Priorytet - Niskie opóźnienie
                self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            self.grabbed, self.frame = self.stream.read()
            self.error = not self.grabbed

            if self.error:
                print(f"[{self.name}] Nie udało się pobrać pierwszej klatki.")

        except Exception as e:
            print(f"[{self.name}] Wyjątek przy łączeniu: {e}")
            self.error = True

    def update(self):
        """Główna pętla wątku - pobiera klatki i wznawia połączenie"""
        reconnect_interval = 3.0  # Co ile sekund próbować ponownie
        last_reconnect_time = time.time()

        while True:
            if self.stopped:
                if self.stream: self.stream.release()
                return

            # 1. Jeśli strumień działa poprawnie -> pobieraj klatki
            if self.stream and self.stream.isOpened():
                (grabbed, frame) = self.stream.read()

                if grabbed:
                    self.frame = frame
                    self.grabbed = True
                    self.error = False
                else:
                    self.grabbed = False
                    self.error = True
            else:
                self.error = True

            # 2. Logika Auto-Reconnect (tylko gdy jest błąd)
            if self.error:
                if time.time() - last_reconnect_time > reconnect_interval:
                    print(f"[{self.name}] Brak sygnału. Próba wznowienia...")
                    self._connect()
                    last_reconnect_time = time.time()
                else:
                    # Oszczędzamy procesor, gdy czekamy na reconnect
                    time.sleep(0.1)

    def read(self):
        """Zwraca ostatnią klatkę lub None (jeśli błąd)"""
        # Jeśli jest błąd, zwróć None -> Dashboard narysuje szum
        if self.error or not self.grabbed:
            return None
        return self.frame

    def stop(self):
        """Zatrzymuje wątek"""
        self.stopped = True