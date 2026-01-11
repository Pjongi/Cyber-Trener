# core/camera_stream.py
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

        # Licznik FPS
        self.real_fps = 0.0
        self._fps_counter = 0
        self._fps_timer = time.time()

        self._connect()

    def start(self):
        t = threading.Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def _connect(self):
        if self.stream is not None:
            self.stream.release()

        # --- ROZRÓŻNIENIE TYPU ŹRÓDŁA ---
        # Sprawdzamy czy to link (napis) czy numer USB (liczba)
        is_usb = isinstance(self.src, int)

        if is_usb:
            print(f"[{self.name}] Łączenie z USB {self.src} (DirectShow)...")
        else:
            # Dla pewności upewniamy się, że link kończy się na /video jeśli to IP Webcam
            if "192.168" in str(self.src) or "10." in str(self.src):
                if not str(self.src).endswith("/video"):
                    print(f"[{self.name}] UWAGA: Dla IP Webcam adres powinien kończyć się na '/video'")
            print(f"[{self.name}] Łączenie z siecią: {self.src}...")

        try:
            if is_usb:
                # === LOGIKA DLA USB (Fizyczna kamera) ===
                self.stream = cv2.VideoCapture(self.src, cv2.CAP_DSHOW)
                self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
                self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                self.stream.set(cv2.CAP_PROP_FPS, 30)
                self.stream.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Auto ekspozycja

            else:
                # === LOGIKA DLA WI-FI (IP Webcam) ===
                # Tutaj NIE używamy DirectShow, bo to zabija strumień sieciowy!
                self.stream = cv2.VideoCapture(self.src)

                # Kluczowe dla Wi-Fi: Bufor musi być minimalny, żeby nie było opóźnień
                self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)

                # Opcjonalnie: Zmniejszenie czasu oczekiwania na klatkę
                # (Większość ustawień kamery IP trzeba zmieniać W TELEFONIE, a nie tutaj)

            self.grabbed, self.frame = self.stream.read()
            self.error = not self.grabbed

            if not self.error:
                print(f"[{self.name}] SUKCES. Połączono.")
            else:
                print(f"[{self.name}] Błąd: Nie można pobrać obrazu z {self.src}")

        except Exception as e:
            print(f"[{self.name}] Wyjątek krytyczny: {e}")
            self.error = True

    def update(self):
        reconnect_interval = 2.0
        last_reconnect_time = time.time()

        while True:
            if self.stopped:
                if self.stream: self.stream.release()
                return

            if self.stream and self.stream.isOpened():
                (grabbed, frame) = self.stream.read()
                if grabbed:
                    self.frame = frame
                    self.grabbed = True
                    self.error = False

                    # Licznik FPS
                    self._fps_counter += 1
                    if time.time() - self._fps_timer >= 1.0:
                        self.real_fps = self._fps_counter
                        self._fps_counter = 0
                        self._fps_timer = time.time()
                else:
                    self.grabbed = False
                    self.error = True
            else:
                self.error = True

            if self.error:
                # Próba ponownego połączenia co 2 sekundy
                if time.time() - last_reconnect_time > reconnect_interval:
                    self._connect()
                    last_reconnect_time = time.time()
                else:
                    time.sleep(0.1)

    def read(self):
        if self.error or not self.grabbed:
            return None
        return self.frame

    def stop(self):
        self.stopped = True