import tkinter as tk
from tkinter import ttk
import config


class CyberLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CYBER TRENER - KONFIGURACJA")
        self.root.geometry("500x700")  # Zwiększyłem wysokość okna
        self.root.configure(bg="#050a05")

        # Stylizacja (bez zmian)
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TLabel", background="#050a05", foreground="#00ff00", font=("Consolas", 10))
        self.style.configure("TButton", background="#003300", foreground="#00ff00", bordercolor="#00ff00")
        self.style.configure("TCheckbutton", background="#050a05", foreground="#00ff00")
        self.style.configure("TRadiobutton", background="#050a05", foreground="#00ff00")
        self.style.configure("TCombobox", fieldbackground="#002200", background="#003300", foreground="#00ff00",
                             arrowcolor="#00ff00")

        # --- NAGŁÓWEK ---
        lbl_title = tk.Label(self.root, text="SYSTEM CONFIGURATION", bg="#050a05", fg="#00ff00",
                             font=("Consolas", 18, "bold"))
        lbl_title.pack(pady=15)

        # --- SEKCJA 1: KAMERY (Skrócona w kodzie tutaj, ale zachowaj starą logikę) ---
        # ... (Tutaj wklej kod obsługi KAMERA 1 i KAMERA 2 z poprzedniej wersji pliku) ...
        # Dla czytelności wklejam tylko nową sekcję poniżej Frame Camera 2

        # --- KAMERA 1 (FRONT) ---
        frame_c1 = tk.LabelFrame(self.root, text=" KAMERA 1 (FRONT) ", bg="#050a05", fg="#00ff00",
                                 font=("Consolas", 12))
        frame_c1.pack(fill="x", padx=20, pady=5)
        self.c1_type = tk.StringVar(value="USB")
        # ... (Reszta logiki C1 jak w oryginale) ...
        frame_c1_type = tk.Frame(frame_c1, bg="#050a05")
        frame_c1_type.pack(fill="x", padx=10, pady=5)
        ttk.Radiobutton(frame_c1_type, text="USB", variable=self.c1_type, value="USB", command=self.update_ui).pack(
            side="left", padx=10)
        ttk.Radiobutton(frame_c1_type, text="Wi-Fi", variable=self.c1_type, value="WIFI", command=self.update_ui).pack(
            side="left", padx=10)
        self.entry_c1_usb = tk.Entry(frame_c1, bg="#002200", fg="#fff", insertbackground='white')
        self.entry_c1_usb.insert(0, "0")
        self.entry_c1_ip = tk.Entry(frame_c1, bg="#002200", fg="#fff", insertbackground='white')
        self.entry_c1_ip.insert(0, "http://192.168.0.101:8080/video")
        self.lbl_c1_val = tk.Label(frame_c1, text="ID Kamery:", bg="#050a05", fg="#00ff00")
        self.lbl_c1_val.pack(anchor="w", padx=10)

        # --- KAMERA 2 (SIDE) ---
        frame_c2 = tk.LabelFrame(self.root, text=" KAMERA 2 (SIDE) ", bg="#050a05", fg="#00ff00", font=("Consolas", 12))
        frame_c2.pack(fill="x", padx=20, pady=5)
        self.use_c2 = tk.BooleanVar(value=True)
        cb_use_c2 = ttk.Checkbutton(frame_c2, text="AKTYWUJ DRUGĄ KAMERĘ", variable=self.use_c2, command=self.update_ui)
        cb_use_c2.pack(anchor="w", padx=10, pady=5)
        self.c2_type = tk.StringVar(value="WIFI")
        self.frame_c2_opts = tk.Frame(frame_c2, bg="#050a05")

        # ... (Reszta logiki C2 jak w oryginale) ...
        frame_c2_type = tk.Frame(self.frame_c2_opts, bg="#050a05")
        frame_c2_type.pack(fill="x", padx=10, pady=5)
        ttk.Radiobutton(frame_c2_type, text="USB", variable=self.c2_type, value="USB", command=self.update_ui).pack(
            side="left", padx=10)
        ttk.Radiobutton(frame_c2_type, text="Wi-Fi", variable=self.c2_type, value="WIFI", command=self.update_ui).pack(
            side="left", padx=10)
        self.entry_c2_usb = tk.Entry(self.frame_c2_opts, bg="#002200", fg="#fff", insertbackground='white')
        self.entry_c2_usb.insert(0, "1")
        self.entry_c2_ip = tk.Entry(self.frame_c2_opts, bg="#002200", fg="#fff", insertbackground='white')
        self.entry_c2_ip.insert(0, "http://192.168.0.102:8080/video")
        self.lbl_c2_val = tk.Label(self.frame_c2_opts, text="Adres IP:", bg="#050a05", fg="#00ff00")
        self.lbl_c2_val.pack(anchor="w", padx=10)

        # --- NOWA SEKCJA: WYDAJNOŚĆ AI ---
        frame_ai = tk.LabelFrame(self.root, text=" AI ENGINE CONFIGURATION ", bg="#050a05", fg="#00ff00",
                                 font=("Consolas", 12))
        frame_ai.pack(fill="x", padx=20, pady=10)

        # Wybór YOLO
        tk.Label(frame_ai, text="Model YOLO (Front):", bg="#050a05", fg="#aaa").grid(row=0, column=0, padx=10, pady=5,
                                                                                     sticky="w")
        self.combo_yolo = ttk.Combobox(frame_ai,
                                       values=["Nano (Najszybszy)", "Small (Zbalansowany)", "Medium (Dokładny)",
                                               "Large (Najdokładniejszy)"], state="readonly")
        self.combo_yolo.current(0)  # Domyślnie Nano
        self.combo_yolo.grid(row=0, column=1, padx=10, pady=5)

        # Wybór MediaPipe
        tk.Label(frame_ai, text="Model MediaPipe (Side):", bg="#050a05", fg="#aaa").grid(row=1, column=0, padx=10,
                                                                                         pady=5, sticky="w")
        self.combo_mp = ttk.Combobox(frame_ai, values=["Lite (Szybki)", "Full (Standard)", "Heavy (Dokładny)"],
                                     state="readonly")
        self.combo_mp.current(1)  # Domyślnie Full
        self.combo_mp.grid(row=1, column=1, padx=10, pady=5)

        # --- PRZYCISK START ---
        btn_start = tk.Button(self.root, text=">> INICJALIZACJA SYSTEMU <<", bg="#004400", fg="#00ff00",
                              font=("Consolas", 14, "bold"), command=self.start_app)
        btn_start.pack(pady=20, ipady=10, fill="x", padx=50)

        self.should_start = False
        self.update_ui()
        self.root.mainloop()

    def update_ui(self):
        # (Tutaj wklej metodę update_ui z oryginalnego pliku - bez zmian logicznych)
        self.entry_c1_usb.pack_forget()
        self.entry_c1_ip.pack_forget()
        if self.c1_type.get() == "USB":
            self.lbl_c1_val.config(text="ID Kamery (np. 0, 1):")
            self.entry_c1_usb.pack(fill="x", padx=10, pady=5)
        else:
            self.lbl_c1_val.config(text="Adres IP (np. http://...):")
            self.entry_c1_ip.pack(fill="x", padx=10, pady=5)

        if self.use_c2.get():
            self.frame_c2_opts.pack(fill="x")
            self.entry_c2_usb.pack_forget()
            self.entry_c2_ip.pack_forget()
            if self.c2_type.get() == "USB":
                self.lbl_c2_val.config(text="ID Kamery (np. 1, 2):")
                self.entry_c2_usb.pack(fill="x", padx=10, pady=5)
            else:
                self.lbl_c2_val.config(text="Adres IP (np. http://...):")
                self.entry_c2_ip.pack(fill="x", padx=10, pady=5)
        else:
            self.frame_c2_opts.pack_forget()

    def start_app(self):
        # 1. Zapis kamer (stara logika)
        if self.c1_type.get() == "USB":
            try:
                config.CAM_FRONT_ID = int(self.entry_c1_usb.get())
            except:
                config.CAM_FRONT_ID = 0
        else:
            config.CAM_FRONT_ID = self.entry_c1_ip.get()

        config.USE_DUAL_CAMERA = self.use_c2.get()
        if config.USE_DUAL_CAMERA:
            if self.c2_type.get() == "USB":
                try:
                    config.CAM_SIDE_ID = int(self.entry_c2_usb.get())
                except:
                    config.CAM_SIDE_ID = 1
            else:
                config.CAM_SIDE_ID = self.entry_c2_ip.get()
        else:
            config.CAM_SIDE_ID = None

        # 2. Zapis konfiguracji AI (NOWE)
        yolo_map = {
            "Nano (Najszybszy)": 'n',
            "Small (Zbalansowany)": 's',
            "Medium (Dokładny)": 'm',
            "Large (Najdokładniejszy)": 'l'
        }
        mp_map = {
            "Lite (Szybki)": 0,
            "Full (Standard)": 1,
            "Heavy (Dokładny)": 2
        }

        config.MODEL_YOLO_SIZE = yolo_map.get(self.combo_yolo.get(), 'n')
        config.MODEL_MP_COMPLEXITY = mp_map.get(self.combo_mp.get(), 1)

        self.should_start = True
        self.root.destroy()