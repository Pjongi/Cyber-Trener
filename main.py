import cv2
import config
from core.pose_detector import PoseDetector
from core.algorithm import Algorithm, SignalSmoother
from ui.visualizer import Visualizer


def main():
    # Inicjalizacja klas
    detector = PoseDetector(min_conf=config.MIN_CONFIDENCE)
    vis = Visualizer()

    # Filtr do wygładzania (żeby wynik nie latał)
    elbow_smoother = SignalSmoother(alpha=0.15)

    # Odpalamy kamerę
    cap = cv2.VideoCapture(config.CAMERA_ID)

    # Ustawienie rozdziałki na sztywno (czasem poprawia FPS)
    cap.set(3, config.WIDTH)
    cap.set(4, config.HEIGHT)

    print(f"Start: {config.WINDOW_NAME}")
    print("Q = wyjście")

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Błąd klatki, pomijam.")
            continue

        # Detekcja pozy
        results = detector.find_pose(frame)

        # Rysowanie linii na obrazie
        frame = vis.draw_skeleton(frame, results)

        # Jeśli wykryto człowieka, liczymy kąty
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            h, w, _ = frame.shape

            # Pomocnicza: zamiana 0.0-1.0 na piksele
            def get_coords(landmark):
                return [landmark.x * w, landmark.y * h]

            # Punkty prawej ręki: 12=bark, 14=łokieć, 16=nadgarstek
            # Sprawdzamy, czy w ogóle widać łokieć (pewność > 50%)
            elbow_visibility = landmarks[14].visibility

            if elbow_visibility > 0.5:
                p_shoulder = get_coords(landmarks[12])
                p_elbow = get_coords(landmarks[14])
                p_wrist = get_coords(landmarks[16])

                # Liczymy kąt 2D (oś Z z kamery internetowej jest słaba)
                raw_angle = Algorithm.calculate_angle_2d(p_shoulder, p_elbow, p_wrist)

                # Wygładzanie wyniku
                smooth_angle = elbow_smoother.update(raw_angle)

                # Wyświetlanie wartości przy stawie
                display_angle = int(round(smooth_angle))
                vis.draw_angle(frame, (int(p_elbow[0]), int(p_elbow[1])), display_angle)

                # Logika oceniania - proste warunki
                # Tło pod napisy
                cv2.rectangle(frame, (0, 0), (300, 80), (245, 117, 16), -1)

                if smooth_angle > 160:
                    status = "PROSTA REKA"
                    color = (0, 255, 0)  # Zielony
                elif smooth_angle < 90:
                    status = "ZGIETA"
                    color = (0, 0, 255)  # Czerwony
                else:
                    status = "RUCH..."
                    color = (255, 255, 255)  # Biały

                cv2.putText(frame, status, (10, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 2, cv2.LINE_AA)
            else:
                # Jak ręka ucieknie z kadru
                cv2.putText(frame, "NIE WIDZE REKI", (10, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Wyświetlenie okna
        cv2.imshow(config.WINDOW_NAME, frame)

        # Zamknięcie na 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()