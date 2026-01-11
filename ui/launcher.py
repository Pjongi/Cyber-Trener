import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import cv2
import config


class CyberLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CYBER TRENER - SYSTEM LOGIN")
        self.root.geometry("650x950")
        self.root.configure(bg="#050a05")

        # Stylizacja
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TLabel", background="#050a05", foreground="#00ff00", font=("Consolas", 10))
        self.style.configure("TButton", background="#003300", foreground="#00ff00", bordercolor="#00ff00")
        self.style.configure("TCheckbutton", background="#050a05", foreground="#00ff00")
        self.style.configure("TRadiobutton", background="#050a05", foreground="#00ff00")
        self.style.configure("TCombobox", fieldbackground="#002200", background="#003300", foreground="#00ff00",
                             arrowcolor="#00ff00")

        # ZMIENNE STANU (Definiujemy na początku)
        self.mode_var = tk.StringVar(value="LIVE")
        self.use_c2 = tk.BooleanVar(value=False)  # Wspólna zmienna dla Dual Cam i Dual File
        self.c1_source_type = tk.StringVar(value="USB")
        self.c2_source_type = tk.StringVar(value="USB")

        # SKANOWANIE KAMER
        self.detected_cameras = self.scan_cameras()
        if not self.detected_cameras:
            self.detected_cameras = ["Brak kamer USB"]

        # --- UI: NAGŁÓWEK ---
        tk.Label(self.root, text="SYSTEM CONFIGURATION", bg="#050a05", fg="#00ff00",
                 font=("Consolas", 18, "bold")).pack(pady=10)

        # --- UI: 1. TRYB PRACY ---
        frame_mode = tk.LabelFrame(self.root, text=" 1. TRYB PRACY ", bg="#050a05", fg="#00ff00", font=("Consolas", 12))
        frame_mode.pack(fill="x", padx=20, pady=5)

        modes = [
            ("Analiza na żywo (Kamera + AI)", "LIVE"),
            ("Tylko Nagrywanie (RAW - 2 pliki)", "RECORD"),
            ("Analiza Plików (Odtwarzanie)", "FILE")
        ]
        for text, val in modes:
            ttk.Radiobutton(frame_mode, text=text, variable=self.mode_var, value=val, command=self.update_ui).pack(
                anchor="w", padx=10, pady=2)

        # --- SEKCJA PLIKÓW (Dla trybu FILE) ---
        self.frame_files = tk.Frame(frame_mode, bg="#050a05")

        # Checkbox "Analizuj dwa pliki" (NOWOŚĆ - widoczny w trybie FILE)
        self.cb_dual_file = ttk.Checkbutton(self.frame_files, text="Analizuj dwa wideo (Front + Side)",
                                            variable=self.use_c2, command=self.update_ui)
        self.cb_dual_file.grid(row=0, column=0, columnspan=3, sticky="w", padx=5, pady=5)

        # Plik FRONT
        tk.Label(self.frame_files, text="Plik FRONT:", bg="#050a05", fg="#aaa").grid(row=1, column=0, sticky="w",
                                                                                     padx=5)
        self.entry_file_front = tk.Entry(self.frame_files, bg="#002200", fg="#fff", width=35)
        self.entry_file_front.grid(row=1, column=1, padx=5)
        tk.Button(self.frame_files, text="...", bg="#004400", fg="#fff",
                  command=lambda: self.browse_file(self.entry_file_front)).grid(row=1, column=2)

        # Plik SIDE
        self.lbl_file_side = tk.Label(self.frame_files, text="Plik SIDE:", bg="#050a05", fg="#aaa")
        self.entry_file_side = tk.Entry(self.frame_files, bg="#002200", fg="#fff", width=35)
        self.btn_file_side = tk.Button(self.frame_files, text="...", bg="#004400", fg="#fff",
                                       command=lambda: self.browse_file(self.entry_file_side))

        # --- UI: 2. KONFIGURACJA KAMER (Dla trybu LIVE/RECORD) ---
        self.frame_cams = tk.LabelFrame(self.root, text=" 2. KONFIGURACJA KAMER ", bg="#050a05", fg="#00ff00",
                                        font=("Consolas", 12))

        # > KAMERA 1 (FRONT)
        self.frame_c1_container = tk.Frame(self.frame_cams, bg="#050a05")
        self.frame_c1_container.pack(fill="x", padx=10, pady=5)
        tk.Label(self.frame_c1_container, text="Kamera Front:", bg="#050a05", fg="#00ff00", font=("bold")).pack(
            anchor="w")

        self.c1_usb_combo = None
        self.c1_ip_entry = None
        self._build_cam_selector(self.frame_c1_container, self.c1_source_type, "c1")

        # > KAMERA 2 (SIDE)
        # Checkbox "Aktywuj Widok Boczny" (widoczny w trybie KAMERY)
        self.cb_dual_cam = ttk.Checkbutton(self.frame_cams, text="Aktywuj Widok Boczny (Dual Cam)",
                                           variable=self.use_c2, command=self.update_ui)
        self.cb_dual_cam.pack(anchor="w", padx=10, pady=10)

        self.frame_c2_container = tk.Frame(self.frame_cams, bg="#050a05")
        tk.Label(self.frame_c2_container, text="Kamera Side:", bg="#050a05", fg="#00ff00", font=("bold")).pack(
            anchor="w")

        self.c2_usb_combo = None
        self.c2_ip_entry = None
        self._build_cam_selector(self.frame_c2_container, self.c2_source_type, "c2")

        # --- UI: 3. AI ENGINE ---
        frame_ai = tk.LabelFrame(self.root, text=" 3. AI ENGINE ", bg="#050a05", fg="#00ff00", font=("Consolas", 12))
        frame_ai.pack(fill="x", padx=20, pady=10)

        tk.Label(frame_ai, text="YOLO (Front):", bg="#050a05", fg="#aaa").pack(side="left", padx=5)
        self.combo_yolo = ttk.Combobox(frame_ai, values=["Nano", "Small", "Medium", "Large"], state="readonly",
                                       width=10)
        self.combo_yolo.current(0)
        self.combo_yolo.pack(side="left", padx=5)

        tk.Label(frame_ai, text="MediaPipe (Side):", bg="#050a05", fg="#aaa").pack(side="left", padx=5)
        self.combo_mp = ttk.Combobox(frame_ai, values=["Lite", "Full", "Heavy"], state="readonly", width=10)
        self.combo_mp.current(1)
        self.combo_mp.pack(side="left", padx=5)

        # --- START ---
        tk.Button(self.root, text=">> URUCHOM SYSTEM <<", bg="#004400", fg="#00ff00", font=("Consolas", 14, "bold"),
                  command=self.start_app).pack(pady=20, ipady=10, fill="x", padx=50)

        self.load_settings()
        self.update_ui()
        self.should_start = False
        self.root.mainloop()

    def scan_cameras(self):
        available = []
        for i in range(4):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(f"Kamera {i}")
                cap.release()
        return available

    def _build_cam_selector(self, parent, type_var, prefix):
        frame_opts = tk.Frame(parent, bg="#050a05")
        frame_opts.pack(fill="x", pady=2)
        ttk.Radiobutton(frame_opts, text="Fizyczna (USB)", variable=type_var, value="USB", command=self.update_ui).pack(
            side="left", padx=10)
        ttk.Radiobutton(frame_opts, text="Sieciowa (Wi-Fi)", variable=type_var, value="IP",
                        command=self.update_ui).pack(side="left", padx=10)

        frame_inputs = tk.Frame(parent, bg="#050a05")
        frame_inputs.pack(fill="x", pady=2)

        combo = ttk.Combobox(frame_inputs, values=self.detected_cameras, state="readonly", width=30)
        if self.detected_cameras: combo.current(0)

        entry = tk.Entry(frame_inputs, bg="#002200", fg="#fff", width=30)
        entry.insert(0, "http://192.168.0.x:8080/video")

        if prefix == "c1":
            self.c1_usb_combo = combo
            self.c1_ip_entry = entry
        else:
            self.c2_usb_combo = combo
            self.c2_ip_entry = entry

    def browse_file(self, entry_widget):
        f = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv")])
        if f:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, f)

    def update_ui(self):
        mode = self.mode_var.get()
        dual = self.use_c2.get()

        # 1. Obsługa PLIKÓW
        if mode == "FILE":
            self.frame_files.pack(fill="x", padx=10, pady=5)
            self.frame_cams.pack_forget()  # Ukryj kamery

            # W trybie pliku, pole SIDE pokazuje się jeśli zaznaczono checkbox W SEKCJI PLIKÓW
            if dual:
                self.lbl_file_side.grid(row=2, column=0, sticky="w", padx=5, pady=5)
                self.entry_file_side.grid(row=2, column=1, padx=5, pady=5)
                self.btn_file_side.grid(row=2, column=2)
            else:
                self.lbl_file_side.grid_forget()
                self.entry_file_side.grid_forget()
                self.btn_file_side.grid_forget()
        else:
            self.frame_files.pack_forget()
            self.frame_cams.pack(fill="x", padx=20, pady=5)  # Pokaż kamery

            # 2. Obsługa KAMER
            if self.c1_source_type.get() == "USB":
                self.c1_usb_combo.pack(side="left", padx=10)
                self.c1_ip_entry.pack_forget()
            else:
                self.c1_usb_combo.pack_forget()
                self.c1_ip_entry.pack(side="left", padx=10)

            if dual:
                self.frame_c2_container.pack(fill="x", padx=10, pady=5)
                if self.c2_source_type.get() == "USB":
                    self.c2_usb_combo.pack(side="left", padx=10)
                    self.c2_ip_entry.pack_forget()
                else:
                    self.c2_usb_combo.pack_forget()
                    self.c2_ip_entry.pack(side="left", padx=10)
            else:
                self.frame_c2_container.pack_forget()

    def get_cam_id(self, source_type, combo, entry):
        if source_type == "USB":
            val = combo.get()
            try:
                return int(val.split(" ")[-1])
            except:
                return 0
        else:
            return entry.get()

    def load_settings(self):
        if os.path.exists(config.SETTINGS_FILE):
            try:
                with open(config.SETTINGS_FILE, 'r') as f:
                    d = json.load(f)
                    self.mode_var.set(d.get("mode", "LIVE"))
                    self.entry_file_front.insert(0, d.get("file_front", ""))
                    self.entry_file_side.insert(0, d.get("file_side", ""))
                    self.use_c2.set(d.get("dual", False))
                    self.c1_source_type.set(d.get("c1_type", "USB"))
                    self.c2_source_type.set(d.get("c2_type", "USB"))
                    self.c1_ip_entry.delete(0, tk.END)
                    self.c1_ip_entry.insert(0, d.get("c1_ip", "http://..."))
                    self.c2_ip_entry.delete(0, tk.END)
                    self.c2_ip_entry.insert(0, d.get("c2_ip", "http://..."))
                    self.combo_yolo.set(d.get("yolo", "Nano"))
                    self.combo_mp.set(d.get("mp", "Full"))
            except Exception as e:
                print(f"Błąd ustawień: {e}")

    def start_app(self):
        c1_final = self.get_cam_id(self.c1_source_type.get(), self.c1_usb_combo, self.c1_ip_entry)
        c2_final = self.get_cam_id(self.c2_source_type.get(), self.c2_usb_combo, self.c2_ip_entry)

        data = {
            "mode": self.mode_var.get(),
            "file_front": self.entry_file_front.get(),
            "file_side": self.entry_file_side.get(),
            "dual": self.use_c2.get(),
            "c1_type": self.c1_source_type.get(),
            "c2_type": self.c2_source_type.get(),
            "c1_ip": self.c1_ip_entry.get(),
            "c2_ip": self.c2_ip_entry.get(),
            "yolo": self.combo_yolo.get(),
            "mp": self.combo_mp.get()
        }
        try:
            with open(config.SETTINGS_FILE, 'w') as f:
                json.dump(data, f)
        except:
            pass

        config.MODE = data["mode"]
        config.INPUT_FILE_FRONT = data["file_front"]
        config.INPUT_FILE_SIDE = data["file_side"]
        config.CAM_FRONT_ID = c1_final
        config.CAM_SIDE_ID = c2_final
        config.USE_DUAL_CAMERA = data["dual"]

        yolo_map = {"Nano": 'n', "Small": 's', "Medium": 'm', "Large": 'l'}
        mp_map = {"Lite": 0, "Full": 1, "Heavy": 2}
        config.MODEL_YOLO_SIZE = yolo_map.get(data["yolo"], 'n')
        config.MODEL_MP_COMPLEXITY = mp_map.get(data["mp"], 1)

        if config.MODE == "FILE":
            if not os.path.exists(config.INPUT_FILE_FRONT):
                messagebox.showerror("Błąd", "Brak pliku Front!")
                return
            if config.USE_DUAL_CAMERA and not os.path.exists(config.INPUT_FILE_SIDE):
                messagebox.showerror("Błąd", "Wybrano Dual View, ale brak pliku Side!")
                return

        self.should_start = True
        self.root.destroy()