# Cyber-Trener

## O projekcie
**Cyber Trener** to stacjonarny system wizyjny wspomagający trening siłowy i rehabilitacyjny. W przeciwieństwie do smartwatchy, które mierzą jedynie parametry witalne, nasz system wykorzystuje **Computer Vision** do analizy biomechaniki ruchu w czasie rzeczywistym.

System analizuje obraz z **dwóch kamer jednocześnie** (przód + bok), co pozwala na precyzyjną weryfikację poprawności wykonywania ćwiczeń i zapobieganie kontuzjom poprzez natychmiastową korektę głosową.
**Możliwe ćwiczenia do wyboru:**
- Ćwiczenia rozciągające
- Podnoszenie sztangi lub hantli
- Sztuki walki (karate,tai-chi), Joga
- Gimnastyka artystyczna
- Elementy gier zespołowych (tenis, siatkówka)
- Rehabilitacja (stany niedowładu, powrót po operacji)
### Główne cele
* **Weryfikacja techniki:** Wykrywanie błędów takich jak "koci grzbiet", koślawienie kolan czy zbyt płytki przysiad.
* **Bezdotykowa obsługa:** Interfejs głosowy (instruktor-ćwiczący) pozwalający na skupienie się na ruchu.
* **Autorska analityka:** Implementacja własnych algorytmów geometrycznych do obliczania kątów i trajektorii, niezależna od gotowych rozwiązań "black-box".

---

## Zespół (Autorzy)
| Imię i Nazwisko | Indeks |
| :--- | :--- |
| **Tobiasz Grala** | 251146 |
| **Urszula Szmit** | 252830 |
| **Tymoteusz Kot** | 252803 |
| **Szymon Pokora** | 251205 |

---

## Technologie
Projekt wykorzystuje stos technologiczny oparty na języku **Python 3.10+**:

* **Analiza obrazu:** `OpenCV`, `MediaPipe` / `YOLOv8`
* **Matematyka/Obliczenia:** `NumPy`, autorskie moduły geometryczne
* **Audio:** `SpeechRecognition`, `Pygame` (do odtwarzania komend), `pyttsx3`
* **Baza danych:** `SQLite` / `PostgreSQL` (historia treningów)
* **Wizualizacja:** `Matplotlib` (wykresy po treningu)

---

## Instalacja i Uruchomienie

* Instalacja bibliotek:
   * *pip install opencv-python mediapipe numpy*
   * *pip install pyttsx3 SpeechRecognition pygame matplotlib types-PyYAML*
  
* Głowny plik: *main.py*

## Harmonogram pracy

- [x] **Dokumentacja bibliotek oraz możliwych rozwiązań**
- [x] **Etap 1: Fundamenty (MVP)**
    - [x] Komunikacja program - kamera
    - [x] Rozpoznawanie szkieletu człowieka (MediaPipe)
    - [x] **Implementacja modułu matematycznego (Core)**
        - [x] Autorska funkcja obliczania kątów 3D z wektorów (wymóg "funkcji niskopoziomowych")
        - [x] Wygładzanie drgań punktów (filtracja sygnału, np. średnia krocząca)
    - [x] Prosta wizualizacja kątów na ekranie (np. przy łokciu/kolanie)
- [x] **Etap 2: Obsługa Drugiej Kamery**
    - [x] Konfiguracja zewnętrznego źródła (np. aplikacja IP Webcam na telefonie)
    - [x] **Implementacja wielowątkowości (Threading)** – pobieranie dwóch strumieni bez opóźnień
    - [x] Synchronizacja czasowa klatek (pobieranie klatek z tego samego momentu)
    - [x] Kalibracja (oznaczenie w kodzie, która kamera jest "Front", a która "Side")
- [ ] **Etap 3: Logika Trenera (Algorytmy Regułowe)**
    - [ ] **Definicja reguł biomechanicznych** dla wybranego ćwiczenia (np. Przysiad):
        - [ ] Warunek: Głębokość (kąt kolanowy < 90 st.)
        - [ ] Warunek: Proste plecy (analiza linii biodro-barki)
    - [ ] Implementacja Maszyny Stanów (State Machine):
        - [ ] Wykrycie pozycji startowej
        - [ ] Faza ruchu (w dół / w górę)
        - [ ] Zaliczenie powtórzenia lub rejestracja błędu
    - [ ] Zapisywanie wyników sesji do bazy danych (SQLite)
- [ ] **Etap 4: Interfejs i Audio**
    - [ ] Implementacja Syntezy Mowy (TTS offline - `pyttsx3`) – komendy korygujące
    - [ ] Obsługa Mikrofonu (`SpeechRecognition`) – komendy sterujące ("Start", "Stop")
    - [ ] Raport końcowy na ekranie (wykresy z `matplotlib`)
