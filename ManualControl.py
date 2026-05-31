# serial_controller_v2.py (Versi IRIS 2026 KRAI)
import customtkinter as ctk
import serial
import serial.tools.list_ports
import struct
import threading
import time
import sys
import socket
import json

# Pengaturan CustomTkinter Theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MotorControllerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("IRIS 2026 - Master Kontrol 10 Motor (V3 PRO)")
        self.geometry("1100x680")
        
        # State Data
        self.motor_names = [
            "M0 (Driver Kanan)", "M1 (Driver Kiri)", 
            "M2 (DC Kanan Depan)", "M3 (DC Kiri Depan)", "M4 (DC Kanan Bkng)", "M5 (DC Kiri Bkng)",
            "M6 (Relay PW Kanan / mDorong1)", "M7 (Relay PW Kiri / mDorong2)",
            "M8 (pwLogic)",
            "M9 (Relay Tambahan 1)", "M10 (Relay Tambahan 2)"
        ]
        self.motor_limits = [255, 255, 255, 255, 255, 255, 255, 255, 1, 1, 1]
        self.motor_speeds = [0] * 11
        self.entry_vars = []
        
        # Perlindungan Variabel Antar-Thread (Protects motor_speeds array)
        self.data_lock = threading.Lock()
        
        # Kinematics Variables (Mecanum Vectored Control)
        # Tiga sumbu utama: Maju-Mundur, Kiri-Kanan, Rotasi.
        self.v_x = 0  
        self.v_y = 0  
        self.omega = 0 
        
        # Serial Management
        self.ser = None
        self.running = True

        self.build_ui()
        self.scan_ports() # Auto detect port saat mulai
        
        # Thread Penerima (RX Telemetry Baterai dari Arduino)
        self.rx_thread = threading.Thread(target=self.serial_rx_loop, daemon=True)
        self.rx_thread.start()
        
        # Loop Pengirim menggunakan Thread asli agar bebas hambatan GUI (Fix UI Jeda)
        self.temp_speeds = []
        self.last_sent_time = 0
        self.tx_thread = threading.Thread(target=self.serial_tx_loop, daemon=True)
        self.tx_thread.start()
        
        # Phone Link Server TCP
        self.server_thread = threading.Thread(target=self.start_server, daemon=True)
        self.server_thread.start()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def scan_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo.configure(values=ports)
        if ports:
            self.port_combo.set(ports[0])

    def toggle_connection(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.ser = None
            self.btn_connect.configure(text="CONNECT", fg_color="#27AE60")
            self.lbl_status.configure(text="Sistem: DISCONNECTED", text_color="red")
            self.lbl_batt.configure(text="Robot Batt: -- V", text_color="#7F8C8D")
        else:
            port = self.port_combo.get()
            try:
                self.ser = serial.Serial(port, 115200, timeout=0.01)
                self.btn_connect.configure(text="DISCONNECT", fg_color="#C0392B")
                self.lbl_status.configure(text="Sistem: CONNECTED", text_color="#2ECC71")
            except Exception as e:
                self.lbl_status.configure(text=f"Sistem: ERROR", text_color="red")

    def build_ui(self):
        # ==========================================
        # TOP MENU: Koneksi & Telemetri
        # ==========================================
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(side="top", fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(top_frame, text="COM Port:", font=("Arial", 12)).pack(side="left", padx=5)
        self.port_combo = ctk.CTkComboBox(top_frame, width=120)
        self.port_combo.pack(side="left", padx=5)
        
        ctk.CTkButton(top_frame, text="Refresh", width=60, command=self.scan_ports).pack(side="left", padx=5)
        self.btn_connect = ctk.CTkButton(top_frame, text="CONNECT", width=100, fg_color="#27AE60", command=self.toggle_connection)
        self.btn_connect.pack(side="left", padx=10)
        
        self.btn_link = ctk.CTkButton(top_frame, text="LINK: WAIT", width=140, fg_color="#C0392B", command=self.show_ip)
        self.btn_link.pack(side="left", padx=10)
        
        self.lbl_status = ctk.CTkLabel(top_frame, text="Sistem: DISCONNECTED", text_color="red", font=("Arial", 12, "bold"))
        self.lbl_status.pack(side="left", padx=20)
        
        self.lbl_batt = ctk.CTkLabel(top_frame, text="Robot Batt: -- V", text_color="#7F8C8D", font=("Arial", 14, "bold"))
        self.lbl_batt.pack(side="right", padx=20)

        # Pemisah Window (Kiri Kanan)
        self.left_frame = ctk.CTkFrame(self, width=500)
        self.left_frame.pack(side="left", fill="both", padx=10, pady=5)
        
        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.pack(side="right", fill="both", padx=10, pady=5, expand=True)
        
        # ==========================================
        # PANEL KIRI: DAFTAR 10 MOTOR (Individual)
        # ==========================================
        lbl_head = ctk.CTkLabel(self.left_frame, text="Kontrol Individual (Tekan SPASI = Stop)", font=("Arial", 14, "bold"), text_color="#F1C40F")
        lbl_head.pack(pady=10)
        
        self.bind("<space>", lambda e: self.reset_all_motors())
        
        for i in range(len(self.motor_names)):
            row = ctk.CTkFrame(self.left_frame, fg_color="transparent")
            row.pack(fill="x", pady=4, padx=5)
            
            lbl = ctk.CTkLabel(row, text=self.motor_names[i], width=160, anchor="w")
            lbl.pack(side="left")
            
            btn_dec = ctk.CTkButton(row, text="<", width=35, fg_color="#34495E", font=("Arial", 16,"bold"))
            if i in [6, 7]:
                btn_dec.bind("<ButtonPress-1>", lambda e, m=i: self.set_motor_val(m, -1))
                btn_dec.bind("<ButtonRelease-1>", lambda e, m=i: self.set_motor_val(m, 0))
            elif i in [8, 9, 10]:
                btn_dec.bind("<ButtonPress-1>", lambda e, m=i: self.set_motor_val(m, 1))
                btn_dec.bind("<ButtonRelease-1>", lambda e, m=i: self.set_motor_val(m, 0))
            else:
                btn_dec.configure(command=lambda m=i: self.step_motor(m, -1))
            btn_dec.pack(side="left", padx=5)
            
            var = ctk.StringVar(value="0")
            ent = ctk.CTkEntry(row, width=65, textvariable=var, justify="center", font=("Arial", 14, "bold"))
            ent.pack(side="left", padx=5)
            ent.bind("<Return>", lambda event, m=i, v=var: self.apply_manual(m, v))
            self.entry_vars.append(var)
            
            btn_inc = ctk.CTkButton(row, text=">", width=35, fg_color="#34495E", font=("Arial", 16,"bold"))
            if i in [6, 7]:
                btn_inc.bind("<ButtonPress-1>", lambda e, m=i: self.set_motor_val(m, 1))
                btn_inc.bind("<ButtonRelease-1>", lambda e, m=i: self.set_motor_val(m, 0))
            elif i in [8, 9, 10]:
                btn_inc.bind("<ButtonPress-1>", lambda e, m=i: self.set_motor_val(m, 1))
                btn_inc.bind("<ButtonRelease-1>", lambda e, m=i: self.set_motor_val(m, 0))
            else:
                btn_inc.configure(command=lambda m=i: self.step_motor(m, 1))
            btn_inc.pack(side="left", padx=5)
            
            btn_stop = ctk.CTkButton(row, text="STOP", width=55, fg_color="#C0392B", hover_color="#922B21", font=("Arial", 11, "bold"), command=lambda m=i: self.set_motor_val(m, 0))
            btn_stop.pack(side="left", padx=10)

        # ==========================================
        # PANEL KANAN: KONTROL KOMBINASI Vektor
        # ==========================================
        top_right = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        top_right.pack(pady=10)
        
        lbl_group = ctk.CTkLabel(top_right, text="Vector Kinematics", font=("Arial", 16, "bold"))
        lbl_group.pack(side="left", padx=10)
        
        ctk.CTkLabel(top_right, text="Global Speed:", text_color="#2ECC71", font=("Arial", 12)).pack(side="left", padx=5)
        self.var_global_speed = ctk.StringVar(value="255")
        ctk.CTkEntry(top_right, textvariable=self.var_global_speed, width=60, font=("Arial", 14, "bold"), justify="center").pack(side="left")

        RED_BTN = "#5B1612"
        RED_HOV = "#83241D"
        font_icn = ("Arial", 32, "bold") 

        # --- A. DPAD (Omni Mecanum Vector) ---
        dpad_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        dpad_frame.pack(pady=5)
        
        buttons_dpad = [
            ("↖", 0, 0, lambda i: self.set_vector(i, vx=1, vy=1, w=0)), 
            ("⬆", 0, 1, lambda i: self.set_vector(i, vx=1, vy=0, w=0)),
            ("↗", 0, 2, lambda i: self.set_vector(i, vx=1, vy=-1, w=0)),
            ("⬅", 1, 0, lambda i: self.set_vector(i, vx=0, vy=1, w=0)),  
            ("⏹", 1, 1, lambda i: self.set_vector(True, vx=0, vy=0, w=0)), 
            ("➡", 1, 2, lambda i: self.set_vector(i, vx=0, vy=-1, w=0)),
            ("↙", 2, 0, lambda i: self.set_vector(i, vx=-1, vy=1, w=0)), 
            ("⬇", 2, 1, lambda i: self.set_vector(i, vx=-1, vy=0, w=0)),
            ("↘", 2, 2, lambda i: self.set_vector(i, vx=-1, vy=-1, w=0))
        ]
        
        for (txt, r, c, cmdFn) in buttons_dpad:
            if txt == "⏹": 
                btn = ctk.CTkButton(dpad_frame, text="STOP", width=75, height=75, fg_color="#4F4F4F", hover_color="#3B3B3B", font=("Arial", 14,"bold"), command=lambda c=cmdFn: c(True))
            else:
                btn = ctk.CTkButton(dpad_frame, text=txt, width=75, height=75, fg_color=RED_BTN, hover_color=RED_HOV, font=font_icn)
                btn.bind("<ButtonPress-1>", lambda e, c=cmdFn: c(True))
                btn.bind("<ButtonRelease-1>", lambda e, c=cmdFn: c(False))
            btn.grid(row=r, column=c, padx=6, pady=6)

        mid_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        mid_frame.pack(pady=20)
        
        # B. DOUBLE ARROWS (Power Window M0 & M1)
        btn_pw_up = ctk.CTkButton(mid_frame, text="⏫", width=70, height=70, fg_color=RED_BTN, hover_color=RED_HOV, font=font_icn)
        btn_pw_up.grid(row=0, column=0, padx=15)
        btn_pw_up.bind("<ButtonPress-1>", lambda e: self.cmd_pw(True, 1))
        btn_pw_up.bind("<ButtonRelease-1>", lambda e: self.cmd_pw(False, 0))

        btn_pw_dn = ctk.CTkButton(mid_frame, text="⏬", width=70, height=70, fg_color=RED_BTN, hover_color=RED_HOV, font=font_icn)
        btn_pw_dn.grid(row=0, column=1, padx=15)
        btn_pw_dn.bind("<ButtonPress-1>", lambda e: self.cmd_pw(True, -1))
        btn_pw_dn.bind("<ButtonRelease-1>", lambda e: self.cmd_pw(False, 0))

        # C. CURVE ARROWS (Turn In Place - Omega Vector)
        btn_turn_l = ctk.CTkButton(mid_frame, text="↶", width=70, height=70, fg_color=RED_BTN, hover_color=RED_HOV, font=font_icn)
        btn_turn_l.grid(row=0, column=2, padx=15)
        btn_turn_l.bind("<ButtonPress-1>", lambda e: self.set_vector(True, vx=0, vy=0, w=-1))
        btn_turn_l.bind("<ButtonRelease-1>", lambda e: self.set_vector(False, vx=0, vy=0, w=0))

        btn_turn_r = ctk.CTkButton(mid_frame, text="↷", width=70, height=70, fg_color=RED_BTN, hover_color=RED_HOV, font=font_icn)
        btn_turn_r.grid(row=0, column=3, padx=15)
        btn_turn_r.bind("<ButtonPress-1>", lambda e: self.set_vector(True, vx=0, vy=0, w=1))
        btn_turn_r.bind("<ButtonRelease-1>", lambda e: self.set_vector(False, vx=0, vy=0, w=0))

        # PCA dan Stepper dinonaktifkan (Komponen telah dilepas)
        pass


    # ===============================================
    # FUNGSI INTERNAL UI & UPDATE KINEMATIKA
    # ===============================================
    def update_entry_text(self):
        for i in range(len(self.motor_names)):
            try:
                # Refresh hanya jika kursor user TIDAK sedang berada di kotak tersebut (agar ketikan manual tidak keriset)
                if self.focus_get() != self.entry_vars[i]._widget:
                    self.entry_vars[i].set(str(self.motor_speeds[i]))
            except:
                self.entry_vars[i].set(str(self.motor_speeds[i]))
    
    def set_motor_val(self, i, val):
        with self.data_lock: # Minta gembok memori 
            limit = self.motor_limits[i]
            self.motor_speeds[i] = max(-limit, min(limit, val))
        self.update_entry_text()
        
    def step_motor(self, i, direction):
        step = 10 if self.motor_limits[i] <= 1000 else 100
        with self.data_lock:
            new_val = self.motor_speeds[i] + (step * direction)
        self.set_motor_val(i, new_val)

    def apply_manual(self, i, string_var):
        try:
            val = int(string_var.get())
            self.set_motor_val(i, val)
        except ValueError:
            self.update_entry_text()

    def reset_all_motors(self):
        with self.data_lock:
            for i in range(len(self.motor_names)): self.motor_speeds[i] = 0
            self.v_x = 0
            self.v_y = 0
            self.omega = 0
        self.update_entry_text()

    def get_global_max(self):
        try:
            val = int(self.var_global_speed.get())
            return min(255, max(0, val))
        except:
            return 255

    # --- KINEMATICS MECANUM MIXER (Roda Omnidirectional) ---
    def set_vector(self, pressed, vx, vy, w):
        sp = self.get_global_max()
        if pressed:
            self.v_x = vx * sp
            self.v_y = vy * sp
            self.omega = w * sp
        else:
            # Jika user ngelepas D-PAD, kembalikan parameter ke Nol
            if vx == 0 and vy == 0 and w == 0:
                pass 
            else:
                self.v_x = 0; self.v_y = 0; self.omega = 0

        # Mecanum Inverse Kinematics Formula (Menghitung porsi tiap roda)
        fl = self.v_x + self.v_y + self.omega
        fr = self.v_x - self.v_y - self.omega
        bl = self.v_x - self.v_y + self.omega
        br = self.v_x + self.v_y - self.omega

        with self.data_lock:
            # Peta Asli M2:FR, M3:FL, M4:BR, M5:BL
            limit = 255
            self.motor_speeds[3] = max(-limit, min(limit, fl)) # Front L
            self.motor_speeds[2] = max(-limit, min(limit, fr)) # Front R
            self.motor_speeds[5] = max(-limit, min(limit, bl)) # Back L
            self.motor_speeds[4] = max(-limit, min(limit, br)) # Back R
            
        self.update_entry_text()

    def cmd_pw(self, pressed, dir_val):
        # PW sekarang menggunakan relay dikontrol oleh mDorong1 dan mDorong2 (indeks 6 dan 7)
        s = dir_val
        self.set_motor_val(6, s if pressed else 0)
        self.set_motor_val(7, s if pressed else 0)

    # ===============================================
    # SERIAL TX (TRANSMITTER) - THREAD
    # ===============================================
    def serial_tx_loop(self):
        while self.running:
            current_time = time.time()
            
            # Auto-Reconnect Mechanism
            if self.ser is None or not self.ser.is_open:
                if self.btn_connect.cget("text") == "DISCONNECT": 
                    # Paksa rubah status UI jadi DISCONNECTED otomatis lewat Tkinter (after memanggil fungsi)
                    self.after(0, self.toggle_connection)
            
            if self.ser and self.ser.is_open:
                try:
                    with self.data_lock:
                        self.motor_speeds[8] = 0 # pwLogic (indeks 8)
                        speeds_snapshot = self.motor_speeds.copy()
                        
                    # Kirim ke Robot JIKA nilai motor dirubah ATAU jika sudah lewat 0.05s (Keep Alive)
                    if self.temp_speeds != speeds_snapshot or (current_time - self.last_sent_time > 0.05):
                        self.temp_speeds = speeds_snapshot
                        
                        # UBAH: Konversi 11 angka (int16) menjadi 22 byte (Little Endian '<11h')
                        data_22b = struct.pack('<11h', *speeds_snapshot)
                        
                        calc_crc = 0
                        for b in data_22b:
                            calc_crc ^= b
                            
                        # Rakit payload: Header (2) + Data (22) + Checksum (1) + End (2)
                        payload = struct.pack('<BB', 0xAA, 0x55) + data_22b + struct.pack('<BBB', calc_crc, 0x0D, 0x0A)
                        self.ser.write(payload)
                        self.last_sent_time = current_time
                        
                except Exception as e:
                    # Delay dan auto-reconnect akan ambil alih
                    pass
                    
            time.sleep(0.04) # Bebaskan main UI thread, biarkan CPU bernafas murni    # ===============================================
    
    
    # SERIAL RX (RECEIVER / TELEMETRY) - THREAD
    # ===============================================
    def serial_rx_loop(self):
        while self.running:
            if self.ser and self.ser.is_open:
                try:
                    # Baca antrean serial
                    if self.ser.in_waiting >= 7:
                        b1 = self.ser.read()
                        if b1 == b'\xBB':  # Header 1 Telemetry (Dari Arduino)
                            b2 = self.ser.read()
                            if b2 == b'\x66': # Header 2
                                payload = self.ser.read(5) 
                                if len(payload) == 5 and payload[3] == 0x0D and payload[4] == 0x0A:
                                    bh, bl, crc = payload[0], payload[1], payload[2]
                                    # Hitung Checksum
                                    if (bh ^ bl) == crc:
                                        batt_mV = (bh << 8) | bl  # Restorasi tegangan utuh
                                        batt_V = batt_mV / 100.0
                                        # Hantam ke UI
                                        self.lbl_batt.configure(text=f"Robot Batt: {batt_V:.2f} V", text_color="#2ECC71")
                except Exception:
                    pass
            time.sleep(0.01)

    def show_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except:
            ip = "127.0.0.1"
        s.close()
        import tkinter.messagebox
        tkinter.messagebox.showinfo("Jaringan Lokal", f"Masukkan IP ini ke Aplikasi Android Anda:\n\n{ip}\n\nPort Server: 8888")

    def handle_phone_command(self, cmd_str):
        try:
            c = json.loads(cmd_str)
            t = c.get("t")
            if t == "gs":
                self.var_global_speed.set(str(c.get("v", 255)))
            elif t == "dp":
                pr = c.get("p", False)
                btn = c.get("btn")
                vmap = {
                    "↖": (1, 1, 0), "⬆": (1, 0, 0), "↗": (1, -1, 0),
                    "⬅": (0, 1, 0), "⏹": (0, 0, 0), "➡": (0, -1, 0),
                    "↙": (-1, 1, 0), "⬇": (-1, 0, 0), "↘": (-1, -1, 0),
                }
                if btn in vmap:
                    if btn == "⏹":
                        self.set_vector(True, 0, 0, 0)
                    else:
                        self.set_vector(pr, *vmap[btn])
            elif t == "pw":
                self.cmd_pw(c.get("p", False), c.get("d", 0))
            elif t == "pca1":
                self.cmd_pca(c.get("p", False), c.get("d", 0))
            elif t == "pca2":
                self.cmd_pca_2(c.get("p", False), c.get("d", 0))
            elif t == "pca3":
                self.cmd_pca_3(c.get("p", False), c.get("d", 0))
            elif t == "stp":
                self.cmd_stepper(c.get("p", False), c.get("d", 0))
            elif t == "trn":
                self.set_vector(c.get("p", False), 0, 0, c.get("d", 0))
            elif t == "ind":
                # Pengatur Nilai Individual Motor
                m = c.get("m", 0)
                val = c.get("v", 0)
                if c.get("p", False):
                    self.set_motor_val(m, val)
                else:
                    self.set_motor_val(m, 0)
            elif t == "stop":
                self.reset_all_motors()
        except Exception:
            pass

    def start_server(self):
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Dengarkan semua IP masuk pada port 8888
        self.server_sock.bind(("0.0.0.0", 8888))
        self.server_sock.listen(1)
        
        while self.running:
            try:
                self.server_sock.settimeout(1.0)
                conn, addr = self.server_sock.accept()
                
                # HP Terhubung
                try:
                    self.btn_link.configure(text=f"LINK: {addr[0]}", fg_color="#27AE60")
                except: pass
                
                conn.settimeout(2.0)
                buffer = ""
                while self.running:
                    try:
                        data = conn.recv(1024).decode('utf-8')
                        if not data: break
                        buffer += data
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            # Jalankan GUI update handler dari antrean tk.after agar aman dari thread crash
                            self.after(0, self.handle_phone_command, line)
                    except socket.timeout:
                        continue # socket timeout gapakai, kita muter terus 
                    except Exception as e:
                        break # Koneksi putus
                        
                conn.close()
                try:
                    if self.running: self.btn_link.configure(text="LINK: WAIT", fg_color="#C0392B")
                except: pass
            except socket.timeout:
                pass
            except Exception as e:
                pass
                
    def on_closing(self):
        self.running = False
        time.sleep(0.1)
        if self.ser and self.ser.is_open:
            # Kirim sinyal Ngerem Semua satu kali terakhir ke Arduino sebelum mati
            # UBAH: Kirim array berisi 11 angka nol, di-pack dengan format '<11h'
            data_22b = struct.pack('<11h', *([0]*11))
            crc = 0
            for b in data_22b: 
                crc ^= b
                
            payload = struct.pack('<BB', 0xAA, 0x55) + data_22b + struct.pack('<BBB', crc, 0x0D, 0x0A)
            try: 
                self.ser.write(payload)
            except: 
                pass
            self.ser.close()
        self.destroy()
        sys.exit()


if __name__ == "__main__":
    app = MotorControllerApp()
    app.mainloop()
