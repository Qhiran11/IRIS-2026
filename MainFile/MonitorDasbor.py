from cv2 import REDUCE_AVG
import random
from PIL import Image
import customtkinter as ctk
import socket
import json
import time
import threading
import sys

# Pengaturan Tema CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MonitorDasborApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Monitor Telemetri NANOPA 2026 (GUI Version - Auto Connect)")
        self.geometry("1000x600")
        
        # State Data & Jaringan
        self.running = True
        self.is_connected = False
        self.tcp_sock = None
        self.udp_sock = None
        
        self.build_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Mulai pencarian otomatis di latar belakang saat aplikasi dibuka
        threading.Thread(target=self.cari_jetson_thread, daemon=True).start()

    def build_ui(self):
        # ==========================================
        # TOP MENU: Kontrol Utama Sesuai Permintaan
        # ==========================================
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(side="top", fill="x", padx=10, pady=10)
        
        # 1. Tombol Switch Mode Gelap/Terang
        self.theme_switch = ctk.CTkSwitch(
            top_frame, text="Dark Mode", 
            command=self.toggle_theme,
            onvalue="Dark", offvalue="Light"
        )
        self.theme_switch.select() # Default Dark
        self.theme_switch.pack(side="left", padx=15)
        
        # 2. Panel Input Token (Terkunci dengan default "NANOPA")
        ctk.CTkLabel(top_frame, text="Token Jetson:", font=("Arial", 12, "bold")).pack(side="left", padx=(10, 5))
        self.token_entry = ctk.CTkEntry(top_frame, width=100, justify="center")
        self.token_entry.insert(0, "NANOPA")
        self.token_entry.configure(state="disabled") # Kunci agar tidak diubah saat auto-search
        self.token_entry.pack(side="left", padx=5)
        
        # 3. Status Label (Menggantikan posisi tombol Connect)
        self.lbl_status = ctk.CTkLabel(top_frame, text="Status: MEMULAI PENCARIAN...", text_color="#F1C40F", font=("Arial", 12, "bold"))
        self.lbl_status.pack(side="left", padx=20)

        # -----------------------------------------------------
        # [BARU] 4. Indikator Hardware (Diratakan ke Kanan)
        # -----------------------------------------------------
        self.lbl_hw_out = ctk.CTkLabel(top_frame, text="⚙️ MOTOR: ?", text_color="gray", font=("Arial", 12, "bold"))
        self.lbl_hw_out.pack(side="right", padx=10)

        self.lbl_hw_in = ctk.CTkLabel(top_frame, text="📡 SENSOR: ?", text_color="gray", font=("Arial", 12, "bold"))
        self.lbl_hw_in.pack(side="right", padx=10)
        
        # Penyekat visual (opsional)
        ctk.CTkLabel(top_frame, text="|", text_color="gray").pack(side="right", padx=5)

        # ==========================================
        # MAIN PANEL: Tampilan Data Json (Dasbor)
        # ==========================================
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Kolom Kiri: Sensor
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=5)
        ctk.CTkLabel(left_frame, text="📡 Data Memori Sensor", font=("Arial", 20, "bold"), text_color="#3498DB").pack(pady=5)
        self.box_sensor = ctk.CTkTextbox(left_frame, font=("Courier", 20), state="disabled")
        self.box_sensor.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Kolom Kanan: Dibagi Atas (Status) dan Bawah (Motor)
        right_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        right_frame.pack(side="right", fill="both", expand=True, padx=5)
        
        # Kanan Atas: Status Robot
        top_right = ctk.CTkFrame(right_frame)
        top_right.pack(side="top", fill="both", expand=True, pady=(0, 5))
        # Buat frame transparan khusus untuk menyusun Judul dan Badge secara horizontal
        header_status_frame = ctk.CTkFrame(top_right, fg_color="transparent")
        header_status_frame.pack(fill="x", pady=5)
        
        # Label Judul (di kiri)
        ctk.CTkLabel(header_status_frame, text="🤖 Status Utama Robot", font=("Arial", 20, "bold"), text_color="#F1C40F").pack(side="left", padx=(10, 5))
        
        # Label Badge Status (di sebelahnya)
        # fg_color digunakan untuk memberikan warna latar belakang (seperti tag/highlight)
        self.lbl_robot_state = ctk.CTkLabel(
            header_status_frame, 
            text="UNKNOWN", 
            font=("Arial", 14, "bold"), 
            text_color="white",
            corner_radius=8, # Membuat sudut latar belakang agak membulat
            padx=10, 
            pady=2
        )
        self.lbl_robot_state.pack(side="left", padx=5)
        self.box_status = ctk.CTkTextbox(top_right, font=("Courier", 20), state="disabled")
        self.box_status.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Kanan Bawah: Data Motor
        bot_right = ctk.CTkFrame(right_frame)
        bot_right.pack(side="bottom", fill="both", expand=True, pady=(5, 0))
        ctk.CTkLabel(bot_right, text="⚙️ Perintah Motor & Relay", font=("Arial", 14, "bold"), text_color="#E74C3C").pack(pady=5)
        self.box_motor = ctk.CTkTextbox(bot_right, font=("Courier", 14), state="disabled")
        self.box_motor.pack(fill="both", expand=True, padx=10, pady=10)

    
    def tampilkan_splash_screen(self):
        """Membuat overlay gambar full screen selama beberapa detik"""
        try:
            # Gunakan r"..." (raw string) agar backslash (\) Windows tidak terbaca sebagai error
            path_gambar = r"C:\Users\YOGA\Documents\IRIS 2026\NANOPA\Program_Utama_KRAI\python\NANOPA_ne9yzd.webp"
            
            # Load gambar menggunakan Pillow
            pil_img = Image.open(path_gambar)
            
            # Konversi ke CTkImage dan atur ukurannya (misal 600x400, sesuaikan dengan aspek rasio gambar Anda)
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(600, 400))
            
            # 1. Buat Frame hitam yang menutupi SELURUH jendela aplikasi
            # relwidth=1, relheight=1 artinya 100% lebar dan 100% tinggi jendela
            self.splash_frame = ctk.CTkFrame(self, fg_color="black")
            self.splash_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            
            # 2. Masukkan gambar ke tengah frame tersebut
            lbl_gambar = ctk.CTkLabel(self.splash_frame, text="", image=ctk_img)
            lbl_gambar.place(relx=0.5, rely=0.5, anchor="center")
            
            # 3. Hapus frame ini otomatis setelah 2000 milidetik (2 detik)
            self.after(1000, self.splash_frame.destroy)
            
        except Exception as e:
            print(f"[UI] Gambar transisi gagal dimuat: {e}")
            # Jika gambar tidak ditemukan, biarkan saja agar tidak membuat aplikasi crash
    
    
    def tampilkan_glitch(self):
        """Memunculkan gambar glitch sekilas lalu menghilang (Overlay transparan)"""
        try:
            path_gambar = r"C:\Users\YOGA\Documents\IRIS 2026\NANOPA\Program_Utama_KRAI\python\programmer.png"
            pil_img = Image.open(path_gambar)
            
            # CustomTkinter otomatis membaca alpha channel (transparansi) dari file PNG
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(800, 800))
            
            # Langsung buat Label dan tempel di main window (self), jangan pakai Frame tambahan
            self.lbl_glitch = ctk.CTkLabel(
                self, 
                text="", 
                image=ctk_img, 
                fg_color="transparent" # KUNCI: Membuat background kotak gambarnya hilang
            )
            
            # Letakkan tepat di tengah layar
            self.lbl_glitch.place(relx=0.5, rely=0.5, anchor="center")
            
            # Hancurkan label gambar ini setelah 150 milidetik
            self.after(150, self.lbl_glitch.destroy)
            
        except Exception as e:
            pass # Abaikan jika gambar gagal diload agar loop tidak error

    
    # ===============================================
    # FUNGSI INTERAKSI UI
    # ===============================================
    def toggle_theme(self):
        mode = self.theme_switch.get()
        ctk.set_appearance_mode(mode)

    def update_ui_text(self, text_box, data_dict):
        """Fungsi untuk merender isi JSON ke dalam Textbox"""
        text_box.configure(state="normal")
        text_box.delete("0.0", "end")
        
        if not data_dict:
            text_box.insert("end", "Menunggu data...\n")
        else:
            for key, value in data_dict.items():
                text_box.insert("end", f"{key: <25}: {value}\n")
                
        text_box.configure(state="disabled")

    # ===============================================
    # FUNGSI JARINGAN (SOCKET) & THREADING (AUTO RECONNECT)
    # ===============================================
    def cari_jetson_thread(self):
        token_target = "NANOPA" # Hardcode sesuai permintaan
        
        # Update UI ke mode pencarian
        self.after(0, lambda: self.lbl_status.configure(text=f"Mencari Robot ({token_target})...", text_color="#F1C40F"))
        
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.bind(('0.0.0.0', 5006))
        self.udp_sock.settimeout(2.0) # Waktu tunggu singkat agar loop bisa dicek

        while self.running and not self.is_connected:
            try:
                data, addr = self.udp_sock.recvfrom(1024)
                pesan = data.decode('utf-8')
                
                if pesan.startswith("NANOPA"):
                    _, token, port = pesan.split(":")
                    if token == token_target:
                        self.udp_sock.close()
                        # Lanjutkan koneksi TCP via Thread Utama (UI Safe)
                        self.after(0, self.connect_tcp, addr[0], int(port))
                        return # Keluar dari loop pencarian UDP
            except socket.timeout:
                # --- [BARU] LOGIKA GLITCH ACAK ---
                # Menggunakan random.random() untuk mendapatkan angka antara 0.0 - 1.0
                # Angka < 0.3 berarti ada kemungkinan 30% glitch muncul setiap kali timeout (tiap 2 detik)
                if random.random() < 0.8:
                    self.after(0, self.tampilkan_glitch)
                # ---------------------------------
                
                continue # Abaikan timeout, teruskan pencarian
            
            except Exception:
                time.sleep(1) # Mencegah CPU overload jika terjadi galat sistem
                
        if self.udp_sock:
            try: self.udp_sock.close()
            except: pass

    
    
    def connect_tcp(self, ip, port):
        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.tcp_sock.connect((ip, port))
            self.is_connected = True
            
            # Update UI
            self.lbl_status.configure(text=f"Status: TERHUBUNG ({ip})", text_color="#2ECC71")
            
            self.tampilkan_splash_screen()
            # Mulai Thread Penerima Data JSON
            threading.Thread(target=self.terima_data_thread, daemon=True).start()
            
        except Exception as e:
            self.lbl_status.configure(text=f"Gagal koneksi TCP, mencoba lagi...", text_color="#E74C3C")
            self.is_connected = False
            # Jika gagal sambung TCP, kembalikan ke loop pencarian UDP
            threading.Thread(target=self.cari_jetson_thread, daemon=True).start()

    def terima_data_thread(self):
        buffer = ""
        while self.is_connected and self.running:
            try:
                chunk = self.tcp_sock.recv(4096).decode('utf-8')
                if not chunk: break # Terputus dari sisi Jetson
                buffer += chunk
                
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    data_robot_terkini = json.loads(line)
                    
                    # Update GUI secara aman dari Thread
                    self.after(0, self.update_dashboard, data_robot_terkini)
                    
            except Exception:
                break # Galat jaringan, keluar dari loop
                
        # Jika keluar dari loop (koneksi terputus)
        if self.running:
            self.after(0, self.disconnect_and_reconnect)

    def update_dashboard(self, data):
        # 1. AMBIL SEMUA DATA DARI JSON TERLEBIH DAHULU (Taruh paling atas)
        status_data = data.get("Status Robot", {})
        hw_data = data.get("Koneksi Hardware", {})

        # =========================================================
        # 2. LOGIKA UPDATE BADGE STATUS UTAMA (DI SEBELAH JUDUL)
        # =========================================================
        robot_state = status_data.get("Main State", "UNKNOWN")
        val_upper = str(robot_state).upper()
        
        # Set tulisan hanya nilainya saja (contoh: "STANDBY")
        self.lbl_robot_state.configure(text=val_upper)
        
        # Warnai latar belakang kotak (fg_color) berdasarkan statusnya
        if val_upper == "STANDBY":
            self.lbl_robot_state.configure(fg_color="#3498DB", text_color="white") # Biru
        elif val_upper == "START":
            self.lbl_robot_state.configure(fg_color="#F1C40F", text_color="black") # Kuning 
        elif val_upper == "FINISHED":
            self.lbl_robot_state.configure(fg_color="#3498DB", text_color="white") # Biru
        else:
            self.lbl_robot_state.configure(fg_color="#7F8C8D", text_color="white") # Abu-abu 

        # =========================================================
        # 3. UPDATE INDIKATOR SENSOR & MOTOR (DI TOP BAR KANAN)
        # =========================================================
        if hw_data.get("Input Terhubung", False):
            self.lbl_hw_in.configure(text="📡 SENSOR: OK", text_color="#2ECC71") # Hijau
        else:
            self.lbl_hw_in.configure(text="📡 SENSOR: ERROR", text_color="#E74C3C") # Merah
            
        if hw_data.get("Output Terhubung", False):
            self.lbl_hw_out.configure(text="⚙️ MOTOR: OK", text_color="#2ECC71") # Hijau
        else:   
            self.lbl_hw_out.configure(text="⚙️ MOTOR: ERROR", text_color="#E74C3C") # Merah
        
        # =========================================================
        # 4. UPDATE TEXTBOX (KOTAK DATA) BAWAAN
        # =========================================================
        self.update_ui_text(self.box_sensor, data.get("Sensor", {}))
        self.update_ui_text(self.box_motor, data.get("Motor", {}))
        
        # Update kotak Status secara custom agar bisa mewarnai tulisan
        self.box_status.configure(state="normal")
        self.box_status.delete("0.0", "end")
        
        # Konfigurasi tag warna stabilo untuk textbox
        self.box_status.tag_config("merah", background="#E74C3C", foreground="white")
        self.box_status.tag_config("kuning", background="#F1C40F", foreground="black")
        
        if not status_data:
            self.box_status.insert("end", "Menunggu data...\n")
        else:
            for key, value in status_data.items():
                teks_kiri = f"{key: <25}: "
                self.box_status.insert("end", teks_kiri)
                
                idx_mulai = self.box_status.index("end-1c")
                
                val_str = str(value)
                self.box_status.insert("end", val_str)
                
                idx_selesai = self.box_status.index("end-1c")
                
                val_teks_upper = val_str.upper()
                if val_teks_upper in ["READY", "IDLE"]:
                    self.box_status.tag_add("merah", idx_mulai, idx_selesai)
                elif val_teks_upper == "FINISHED":
                    self.box_status.tag_add("kuning", idx_mulai, idx_selesai)
                    
                self.box_status.insert("end", "\n")
                
        self.box_status.configure(state="disabled")
    
    def disconnect_and_reconnect(self):
        """Membersihkan koneksi TCP yang putus dan otomatis memulai pencarian ulang"""
        self.is_connected = False
        if self.tcp_sock:
            try: self.tcp_sock.close()
            except: pass
            
        # Reset UI
        self.lbl_status.configure(text="TERPUTUS. Mencari ulang...", text_color="#E74C3C")
        
        # Kosongkan layar dasbor (opsional, bisa dinonaktifkan jika ingin melihat data terakhir)
        self.update_dashboard({})
        
        # Mulai ulang pencarian
        threading.Thread(target=self.cari_jetson_thread, daemon=True).start()

    def on_closing(self):
        self.running = False
        self.is_connected = False
        if self.tcp_sock:
            try: self.tcp_sock.close()
            except: pass
        if self.udp_sock:
            try: self.udp_sock.close()
            except: pass
        self.destroy()
        sys.exit()

if __name__ == "__main__":
    app = MonitorDasborApp()
    app.mainloop()