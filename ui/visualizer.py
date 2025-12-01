import cv2
import mediapipe as mp


class Visualizer:
    def __init__(self):
        # Kolory (B, G, R)
        self.C_SKELETON = (0, 255, 0)  # Zielony
        self.C_JOINTS = (0, 0, 255)  # Czerwony

        # Definicje połączeń dla MediaPipe (uproszczone dla sylwetki)
        self.MP_CONNECTIONS = [
            (11, 12), (11, 13), (13, 15),  # Barki i Lewa ręka
            (12, 14), (14, 16),  # Prawa ręka
            (11, 23), (12, 24), (23, 24),  # Tułów
            (23, 25), (25, 27),  # Lewa noga
            (24, 26), (26, 28)  # Prawa noga
        ]

    def draw_yolo_skeleton(self, frame, keypoints, conf_thresh=0.5):
        """Rysuje szkielet YOLO z uwzględnieniem progu pewności"""
        if keypoints is None: return frame

        # Połączenia YOLO (indeksy COCO)
        connections = [
            (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
            (5, 11), (6, 12), (11, 12), (11, 13), (13, 15), (12, 14), (14, 16)
        ]

        # Linie
        for idx1, idx2 in connections:
            p1, p2 = keypoints[idx1], keypoints[idx2]
            if p1[2] > conf_thresh and p2[2] > conf_thresh:
                cv2.line(frame, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), self.C_SKELETON, 2)

        # Kropki
        for pt in keypoints:
            if pt[2] > conf_thresh:
                cv2.circle(frame, (int(pt[0]), int(pt[1])), 4, self.C_JOINTS, -1)

        return frame

    def draw_mp_skeleton(self, frame, results, conf_thresh=0.5):
        """
        Customowe rysowanie MediaPipe.
        Naprawia problem 'eksplodującego szkieletu' poprzez filtrację visibility.
        """
        if not results.pose_landmarks:
            return frame

        lm = results.pose_landmarks.landmark
        h, w, _ = frame.shape

        # Słownik współrzędnych: {index: (x, y, vis)}
        points = {}

        # 1. Pobierz i przelicz widoczne punkty
        for idx, landmark in enumerate(lm):
            if landmark.visibility > conf_thresh:
                cx, cy = int(landmark.x * w), int(landmark.y * h)
                points[idx] = (cx, cy)
                # Rysuj staw
                if idx in [11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]:  # Tylko główne stawy
                    cv2.circle(frame, (cx, cy), 4, self.C_JOINTS, -1)

        # 2. Rysuj linie tylko jeśli OBA punkty są widoczne
        for idx1, idx2 in self.MP_CONNECTIONS:
            if idx1 in points and idx2 in points:
                cv2.line(frame, points[idx1], points[idx2], self.C_SKELETON, 2)

        return frame