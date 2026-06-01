# File: MonitorDasborGUI.py
import customtkinter as ctk
import socket
import json
import time
import threading
import sys

# Pengaturan Tema CustomTkinter (Mirip ManualControl.py)
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MonitorDasborApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Monitor Telemetri NANOPA 2026 (GUI Version)")
        self.geometry("1000x600")
        
        # State Data & Jaringan
        self.running = True
        self.is_connected = False
        self.tcp_sock = None
        self.udp_sock = None
        
        self.build_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

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
        
        # 2. Panel Input Token
        ctk.CTkLabel(top_frame, text="Token Jetson:", font=("Arial", 12, "bold")).pack(side="left", padx=(10, 5))
        self.token_entry = ctk.CTkEntry(top_frame, width=100, justify="center", placeholder_text="Misal: ABCD")
        self.token_entry.pack(side="left", padx=5)
        
        # 3. Tombol Connect / Disconnect
        self.btn_connect = ctk.CTkButton(
            top_frame, text="CONNECT", width=120, 
            fg_color="#27AE60", hover_color="#2ECC71",
            command=self.toggle_connection
        )
        self.btn_connect.pack(side="left", padx=15)
        
        # Status Label
        self.lbl_status = ctk.CTkLabel(top_frame, text="Status: DISCONNECTED", text_color="#E74C3C", font=("Arial", 12, "bold"))
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

    def toggle_connection(self):
        if self.is_connected:
            self.disconnect_system()
        else:
            token = self.token_entry.get().strip().upper()
            if not token:
                self.lbl_status.configure(text="Status: TOKEN KOSONG!", text_color="#E74C3C")
                return
            
            # Ubah UI ke mode pencarian
            self.btn_connect.configure(state="disabled")
            self.token_entry.configure(state="disabled")
            self.lbl_status.configure(text=f"Mencari Jetson ({token})...", text_color="#F1C40F")
            
            # Jalankan pencarian di Thread terpisah agar UI tidak Freeze
            threading.Thread(target=self.cari_jetson_thread, args=(token,), daemon=True).start()

    def update_ui_text(self, text_box, data_dict):
        """Fungsi untuk merender isi JSON ke dalam Textbox"""
        text_box.configure(state="normal")
        text_box.delete("0.0", "end")
        
        if not data_dict:
            text_box.insert("end", "Menunggu data...\n")
        else:
            for key, value in data_dict.items():
                # Format string agar rapi seperti tabel
                text_box.insert("end", f"{key: <25}: {value}\n")
                
        text_box.configure(state="disabled")

    # ===============================================
    # FUNGSI JARINGAN (SOCKET) & THREADING
    # ===============================================
    def cari_jetson_thread(self, token_target):
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.bind(('0.0.0.0', 5006))
        self.udp_sock.settimeout(10.0) # Waktu tunggu 10 detik

        try:
            while self.running:
                data, addr = self.udp_sock.recvfrom(1024)
                pesan = data.decode('utf-8')
                
                if pesan.startswith("NANOPA"):
                    _, token, port = pesan.split(":")
                    if token == token_target:
                        self.udp_sock.close()
                        # Lanjutkan koneksi TCP via Thread Utama (UI Safe)
                        self.after(0, self.connect_tcp, addr[0], int(port))
                        return
        except socket.timeout:
            self.after(0, self.handle_timeout)
        except Exception:
            pass
        finally:
            if self.udp_sock:
                self.udp_sock.close()

    def handle_timeout(self):
        self.lbl_status.configure(text="Status: TIMEOUT / TIDAK DITEMUKAN", text_color="#E74C3C")
        self.btn_connect.configure(state="normal", text="CONNECT", fg_color="#27AE60")
        self.token_entry.configure(state="normal")

    def connect_tcp(self, ip, port):
        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.tcp_sock.connect((ip, port))
            self.is_connected = True
            
            # Update UI
            self.lbl_status.configure(text=f"Status: CONNECTED ({ip})", text_color="#2ECC71")
            self.btn_connect.configure(state="normal", text="DISCONNECT", fg_color="#C0392B", hover_color="#922B21")
            
            # Mulai Thread Penerima Data JSON
            threading.Thread(target=self.terima_data_thread, daemon=True).start()
            
        except Exception as e:
            self.lbl_status.configure(text=f"Status: GAGAL KONEK TCP", text_color="#E74C3C")
            self.btn_connect.configure(state="normal", text="CONNECT", fg_color="#27AE60")
            self.token_entry.configure(state="normal")

    def terima_data_thread(self):
        buffer = ""
        while self.is_connected and self.running:
            try:
                chunk = self.tcp_sock.recv(4096).decode('utf-8')
                if not chunk: break
                buffer += chunk
                
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    data_robot_terkini = json.loads(line)
                    
                    # Update GUI secara aman dari Thread menggunakan self.after
                    self.after(0, self.update_dashboard, data_robot_terkini)
                    
            except Exception:
                break
                
        # Jika keluar dari loop (koneksi terputus dari sisi jetson)
        if self.is_connected:
            self.after(0, self.disconnect_system)

    def update_dashboard(self, data):
        self.update_ui_text(self.box_sensor, data.get("Sensor", {}))
        self.update_ui_text(self.box_motor, data.get("Motor", {}))
        self.update_ui_text(self.box_status, data.get("Status Robot", {}))

    def disconnect_system(self):
        self.is_connected = False
        if self.tcp_sock:
            try: self.tcp_sock.close()
            except: pass
            
        # Reset UI
        self.lbl_status.configure(text="Status: DISCONNECTED", text_color="#E74C3C")
        self.btn_connect.configure(text="CONNECT", fg_color="#27AE60", hover_color="#2ECC71")
        self.token_entry.configure(state="normal")
        
        # Kosongkan layar dasbor
        self.update_dashboard({})

    def on_closing(self):
        self.running = False
        self.disconnect_system()
        self.destroy()
        sys.exit()


if __name__ == "__main__":
    app = MonitorDasborApp()
    app.mainloop()