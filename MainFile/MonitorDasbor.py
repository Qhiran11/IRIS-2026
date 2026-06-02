from cv2 import REDUCE_AVG
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
        
        # 2. Panel Input Token (Terkunci dengan default "IRIS")
        ctk.CTkLabel(top_frame, text="Token Jetson:", font=("Arial", 12, "bold")).pack(side="left", padx=(10, 5))
        self.token_entry = ctk.CTkEntry(top_frame, width=100, justify="center")
        self.token_entry.insert(0, "IRIS")
        self.token_entry.configure(state="disabled") # Kunci agar tidak diubah saat auto-search
        self.token_entry.pack(side="left", padx=5)
        
        # 3. Status Label (Menggantikan posisi tombol Connect)
        self.lbl_status = ctk.CTkLabel(top_frame, text="Status: MEMULAI PENCARIAN...", text_color="#F1C40F", font=("Arial", 12, "bold"))
        self.lbl_status.pack(side="left", padx=20)

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
        ctk.CTkLabel(top_right, text="🤖 Status Utama Robot", font=("Arial", 20, "bold"), text_color="#F1C40F").pack(pady=5)
        self.box_status = ctk.CTkTextbox(top_right, font=("Courier", 20), state="disabled")
        self.box_status.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Kanan Bawah: Data Motor
        bot_right = ctk.CTkFrame(right_frame)
        bot_right.pack(side="bottom", fill="both", expand=True, pady=(5, 0))
        ctk.CTkLabel(bot_right, text="⚙️ Perintah Motor & Relay", font=("Arial", 14, "bold"), text_color="#E74C3C").pack(pady=5)
        self.box_motor = ctk.CTkTextbox(bot_right, font=("Courier", 14), state="disabled")
        self.box_motor.pack(fill="both", expand=True, padx=10, pady=10)

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
        token_target = "IRIS" # Hardcode sesuai permintaan
        
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
        status_data = data.get("Status Robot", {})
        
        # 1. Update kotak Sensor dan Motor menggunakan fungsi default
        self.update_ui_text(self.box_sensor, data.get("Sensor", {}))
        self.update_ui_text(self.box_motor, data.get("Motor", {}))
        
        # 2. Update kotak Status secara custom agar bisa mewarnai KATA TERTENTU saja
        self.box_status.configure(state="normal")
        self.box_status.delete("0.0", "end")
        
        # Konfigurasi tag warna stabilo
        self.box_status.tag_config("merah", background="#E74C3C", foreground="white")
        self.box_status.tag_config("kuning", background="#F1C40F", foreground="black")
        
        if not status_data:
            self.box_status.insert("end", "Menunggu data...\n")
        else:
            for key, value in status_data.items():
                # Ketik label kiri terlebih dahulu
                teks_kiri = f"{key: <25}: "
                self.box_status.insert("end", teks_kiri)
                
                # Catat posisi (index) pointer tepat sebelum nilai status diketik
                idx_mulai = self.box_status.index("end-1c")
                
                # Ketik nilai statusnya (misal: "READY", "STOP")
                val_str = str(value)
                self.box_status.insert("end", val_str)
                
                # Catat posisi (index) pointer tepat setelah nilai status diketik
                idx_selesai = self.box_status.index("end-1c")
                
                # Terapkan highlight HANYA pada rentang kata tersebut
                val_upper = val_str.upper()
                if val_upper in ["READY", "IDLE"]:
                    self.box_status.tag_add("merah", idx_mulai, idx_selesai)
                elif val_upper == "FINISHED":
                    self.box_status.tag_add("kuning", idx_mulai, idx_selesai)
                    
                # Tambahkan baris baru (enter)
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