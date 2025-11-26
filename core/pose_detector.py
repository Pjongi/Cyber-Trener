import mediapipe as mp
import cv2


class PoseDetector:
    def __init__(self, min_conf=0.5):
        self.mp_pose = mp.solutions.pose

        # Konfiguracja modelu MediaPipe
        # model_complexity=2 -> Najdokładniejszy model (Heavy), ale wolniejszy
        # min_detection_confidence=0.3 -> Łatwiej wykrywa osobę w słabym świetle
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            enable_segmentation=False,
            min_detection_confidence=0.3,
            min_tracking_confidence=min_conf
        )

    def find_pose(self, frame):
        """
        Przetwarza klatkę obrazu i zwraca wyniki detekcji.
        """
        # Konwersja BGR -> RGB (wymagana przez MediaPipe)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Zablokowanie zapisu dla wydajności
        frame_rgb.flags.writeable = False

        # Inferencja (Detekcja)
        results = self.pose.process(frame_rgb)

        return results

    def get_landmarks(self, results):
        """
        Zwraca listę punktów kluczowych, jeśli zostały wykryte.
        """
        if results.pose_landmarks:
            return results.pose_landmarks.landmark
        return None