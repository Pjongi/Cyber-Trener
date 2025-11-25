import mediapipe as mp
import cv2


class PoseDetector:
    def __init__(self, min_conf=0.5):
        self.mp_pose = mp.solutions.pose

        # ZMIANA: Dodajemy model_complexity=2 (najdokładniejszy)
        # ZMIANA: enable_segmentation=False (nie potrzebujemy wycinania tła, to przyspieszy)
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,  # 0=Lite, 1=Full, 2=Heavy (Najdokładniejszy)
            smooth_landmarks=True,
            min_detection_confidence=0.3,  # Zmniejszamy próg (łapie szybciej)
            min_tracking_confidence=0.5
        )

    def find_pose(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rgb.flags.writeable = False
        results = self.pose.process(frame_rgb)
        return results

    def get_landmarks(self, results):
        if results.pose_landmarks:
            return results.pose_landmarks.landmark
        return None