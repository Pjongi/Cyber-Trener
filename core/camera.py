from threading import Thread
import cv2
import time


class ThreadedCamera:
    def __init__(self, source):
        self.source = source
        self.capture = cv2.VideoCapture(source)

        # Optymalizacja bufora
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        # Próba wymuszenia niższej rozdzielczości na wejściu (szybsza transmisja)
        self.capture.set(3, 800)
        self.capture.set(4, 600)

        self.status = False
        self.frame = None
        self.stopped = False
        self.fps = 0
        self.prev_time = 0

        # Próba pobrania pierwszej klatki
        if self.capture.isOpened():
            self.status, self.frame = self.capture.read()

    def start(self):
        if not self.status:
            print(f"❌ Błąd: Nie można połączyć z kamerą: {self.source}")
            return None

        # Uruchomienie wątku w tle
        Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            if self.capture.isOpened():
                # Pobieramy klatkę, ale nie blokujemy głównego programu
                (self.status, self.frame) = self.capture.read()
            else:
                time.sleep(0.1)

    def read(self):
        # Zwraca ostatnią dostępną klatkę
        return self.status, self.frame

    def stop(self):
        self.stopped = True
        self.capture.release()