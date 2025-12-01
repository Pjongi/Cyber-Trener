import mediapipe as mp
import cv2

class PoseDetector:
    def __init__(self, min_conf=0.5, complexity=1): # <-- Dodano parametr complexity
        self.mp_pose = mp.solutions.pose

        # complexity: 0=Lite, 1=Full, 2=Heavy
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=complexity, # <-- Użycie parametru
            smooth_landmarks=True,
            enable_segmentation=False,
            min_detection_confidence=0.3,
            min_tracking_confidence=min_conf
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