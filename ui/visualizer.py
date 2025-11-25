import mediapipe as mp
import cv2
import numpy as np


class Visualizer:
    def __init__(self):
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_pose = mp.solutions.pose
        self.style = self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2)

    def draw_skeleton(self, frame, results):
        if results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.style
            )
        return frame

    def draw_angle(self, frame, point_coords, angle_value):
        """
        Rysuje wartość kąta obok stawu.
        point_coords: krotka (x, y) w pikselach
        angle_value: liczba float
        """
        x, y = point_coords

        # Tło dla tekstu (żeby było czytelnie)
        text = f"{int(angle_value)}"
        (w, h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)

        # Rysuj czarny prostokąt pod tekstem
        cv2.rectangle(frame, (x, y - h - 10), (x + w, y), (0, 0, 0), -1)

        # Rysuj biały tekst
        cv2.putText(frame, text, (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        return frame