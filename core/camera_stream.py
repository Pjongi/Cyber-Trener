import cv2
import threading
import time

class CameraStream:
    def __init__(self, src=0, name="Camera"):
        """
        Inicjalizuje strumień wideo w oddzielnym wątku.
        src: 0, 1 (USB) lub "http://..." (IP Webcam)
        """
        self.stream = cv2.VideoCapture(src)
        self.name = name
        self.src = src
        self.stopped = False

        # --- OPTYMALIZACJA (Hybrid Mode) ---

        # 1. Tryb USB (lokalny) - jeśli źródło to liczba (np. 0)
        if isinstance(src, int):
            # Ustawiamy HD 1280x720
            self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            # MJPG jest znacznie szybszy na USB 2.0 (unikamy lagów przy HD)
            self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

        # 2. Tryb IP / Sieciowy (WiFi) - jeśli źródło to tekst (URL)
        else:
            # Kluczowe dla IP Webcam: Zmniejszamy bufor do 1 klatki.
            # Dzięki temu program zawsze bierze "najświeższą" klatkę,
            # zamiast przetwarzać te sprzed 3 sekund (narastający lag).
            self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Próba pobrania pierwszej klatki (inicjalizacja)
        # Jeśli się nie uda, self.frame pozostanie None (obsłużone w main.py)
        (self.grabbed, self.frame) = self.stream.read()

    def start(self):
        # Uruchamiamy wątek w tle
        t = threading.Thread(target=self.update, args=())
        t.daemon = True # Wątek zginie automatycznie razem z głównym programem
        t.start()
        return self

    def update(self):
        # Pętla nieskończona działająca w tle
        while True:
            if self.stopped:
                self.stream.release()
                return

            (grabbed, frame) = self.stream.read()

            if grabbed:
                # Aktualizujemy klatkę tylko gdy pobranie się uda
                self.frame = frame
            else:
                # Jeśli zerwie połączenie (np. WiFi), czekamy chwilę
                # Zapobiega to obciążeniu procesora w 100% pustymi pętlami
                time.sleep(0.1)

    def read(self):
        # Zwraca ostatnią pomyślnie pobraną klatkę z bufora
        return self.frame

    def stop(self):
        # Sygnał do zatrzymania wątku
        self.stopped = True