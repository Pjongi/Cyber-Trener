import cv2
import torch
from ultralytics import YOLO
import numpy as np


class PoseDetectorYOLO:
    def __init__(self, model_size='l', min_conf=0.5):
        """
        model_size: 'n' (nano - najszybszy), 's' (small), 'm' (medium), 'l' (large)
        """
        # Automatyczny wybór urządzenia (0 = GPU Nvidia, 'cpu' = Procesor)
        self.device = '0' if torch.cuda.is_available() else 'cpu'
        print(f"[AI] Uruchamianie YOLOv8 na: {torch.cuda.get_device_name(0) if self.device == '0' else 'CPU'}")

        # Ładowanie modelu (automatycznie pobierze plik przy pierwszym uruchomieniu)
        # yolov8n-pose.pt to wersja Nano - ultra szybka
        self.model = YOLO(f'yolov8{model_size}-pose.pt')
        self.min_conf = min_conf

    def find_pose(self, frame):
        # YOLO przyjmuje obraz BGR, nie trzeba konwertować na RGB
        results = self.model(frame, device=self.device, verbose=False, conf=self.min_conf)
        return results[0]  # Zwracamy pierwszy wynik (zakładamy 1 osobę lub bierzemy pierwszą)

    def get_landmarks(self, results):
        """
        Zwraca punkty w formacie (x, y, visibility)
        YOLO zwraca tensor [1, 17, 3] -> (x, y, conf)
        """
        if results.keypoints is not None and len(results.keypoints) > 0:
            # Pobieramy dane jako numpy array
            # shape: (N_people, 17, 3)
            kp = results.keypoints.data.cpu().numpy()[0]
            return kp
        return None