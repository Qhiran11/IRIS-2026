import socket
import json
import time
import threading
import sys
import random

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QTextEdit, QFrame, QCheckBox)
from PyQt6.QtCore import Qt, QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QFont, QColor

# =========================================================
# 1. KELAS SINYAL (Wajib di PyQt untuk menghubungkan Thread ke GUI)
# =========================================================
class NetworkSignals(QObject):
    update_status = pyqtSignal(str, str) # Mengirim (Teks, Hex Color)
    show_splash = pyqtSignal()
    show_glitch = pyqtSignal()
    update_dashboard = pyqtSignal(dict)  # Mengirim JSON Data
    reconnect = pyqtSignal()

# =========================================================
# 2. KELAS UTAMA APLIKASI
# =========================================================
class MonitorDasborApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Monitor Telemetri NANOPA 2026 (PyQt6 - Auto Connect)")
        self.resize(1000, 600)
        self.setStyleSheet("background-color: #1E1E1E; color: white;") # Tema Gelap
        
        # State Data & Jaringan
        self.running = True
        self.is_connected = False
        self.tcp_sock = None
        self.udp_sock = None
        
        # Inisialisasi Sinyal
        self.signals = NetworkSignals()
        self.signals.update_status.connect(self.ui_update_status)
        self.signals.show_splash.connect(self.ui_show_splash)
        self.signals.show_glitch.connect(self.ui_show_glitch)
        self.signals.update_dashboard.connect(self.ui_update_dashboard)
        self.signals.reconnect.connect(self.disconnect_and_reconnect)

        self.build_ui()
        self.setup_overlays()
        
        # Mulai pencarian otomatis di latar belakang
        threading.Thread(target=self.cari_jetson_thread, daemon=True).start()

    def build_ui(self):
        # Widget Utama & Layout Utama
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        font_normal = QFont("Arial", 12, QFont.Weight.Bold)
        font_mono = QFont("Courier", 14)
        font_mono_large = QFont("Courier", 16)
        
        # ==========================================
        # TOP MENU
        # ==========================================
        self.top_frame = QFrame()  # <--- Tambahkan self.
        self.top_frame.setStyleSheet("background-color: #2C3E50; border-radius: 5px;")
        top_layout = QHBoxLayout(self.top_frame) # <--- Tambahkan self.

        # --- [BARU] TOMBOL TEMA ---
        self.theme_switch = QCheckBox("Light Mode")
        self.theme_switch.setFont(font_normal)
        self.theme_switch.setStyleSheet("color: white;")
        self.theme_switch.stateChanged.connect(self.toggle_theme)

        # Masukkan ke dalam layout paling kiri
        top_layout.addWidget(self.theme_switch)
        top_layout.addSpacing(15)
        # --------------------------
        
        # Token Entry
        lbl_token = QLabel("Token Jetson:")
        lbl_token.setFont(font_normal)
        self.token_entry = QLineEdit("NANOPA")
        self.token_entry.setFont(font_normal)
        self.token_entry.setFixedWidth(100)
        self.token_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.token_entry.setEnabled(False)
        self.token_entry.setStyleSheet("background-color: #34495E; color: white; border: none;")
        
        # Status Label
        self.lbl_status = QLabel("Status: MEMULAI PENCARIAN...")
        self.lbl_status.setFont(font_normal)
        self.lbl_status.setStyleSheet("color: #F1C40F;") # Kuning
        
        # Indikator Hardware (Rata Kanan)
        self.lbl_hw_in = QLabel("📡 SENSOR: ?")
        self.lbl_hw_in.setFont(font_normal)
        self.lbl_hw_in.setStyleSheet("color: gray;")
        
        self.lbl_hw_out = QLabel("⚙️ MOTOR: ?")
        self.lbl_hw_out.setFont(font_normal)
        self.lbl_hw_out.setStyleSheet("color: gray;")
        
        top_layout.addWidget(lbl_token)
        top_layout.addWidget(self.token_entry)
        top_layout.addSpacing(20)
        top_layout.addWidget(self.lbl_status)
        top_layout.addStretch() # Mendorong elemen berikutnya ke kanan
        top_layout.addWidget(self.lbl_hw_in)
        top_layout.addSpacing(10)
        top_layout.addWidget(self.lbl_hw_out)
        
        main_layout.addWidget(self.top_frame)
        
        # ==========================================
        # MAIN PANEL (Membagi Kiri dan Kanan)
        # ==========================================
        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout)
        
        # --- KOLOM KIRI (Sensor) ---
        left_layout = QVBoxLayout()
        lbl_judul_sensor = QLabel("📡 Data Memori Sensor")
        lbl_judul_sensor.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        lbl_judul_sensor.setStyleSheet("color: #3498DB;")
        
        self.box_sensor = QTextEdit()
        self.box_sensor.setFont(font_mono_large)
        self.box_sensor.setReadOnly(True)
        self.box_sensor.setStyleSheet("background-color: #2C3E50; border: none; padding: 10px;")
        
        left_layout.addWidget(lbl_judul_sensor)
        left_layout.addWidget(self.box_sensor)
        content_layout.addLayout(left_layout, stretch=1)
        
        # --- KOLOM KANAN (Status & Motor) ---
        right_layout = QVBoxLayout()
        
        # Kanan Atas: Header Status
        header_status_layout = QHBoxLayout()
        lbl_judul_status = QLabel("🤖 Status Utama Robot")
        lbl_judul_status.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        lbl_judul_status.setStyleSheet("color: #F1C40F;")
        
        self.lbl_robot_state = QLabel("UNKNOWN")
        self.lbl_robot_state.setFont(font_normal)
        self.lbl_robot_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_robot_state.setStyleSheet("background-color: #7F8C8D; color: white; border-radius: 8px; padding: 5px 15px;")
        
        header_status_layout.addWidget(lbl_judul_status)
        header_status_layout.addWidget(self.lbl_robot_state)
        header_status_layout.addStretch()
        
        self.box_status = QTextEdit()
        self.box_status.setFont(font_mono_large)
        self.box_status.setReadOnly(True)
        self.box_status.setStyleSheet("background-color: #2C3E50; border: none; padding: 10px;")
        
        right_layout.addLayout(header_status_layout)
        right_layout.addWidget(self.box_status, stretch=1)
        
        # Kanan Bawah: Motor
        lbl_judul_motor = QLabel("⚙️ Perintah Motor & Relay")
        lbl_judul_motor.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        lbl_judul_motor.setStyleSheet("color: #E74C3C;")
        
        self.box_motor = QTextEdit()
        self.box_motor.setFont(font_mono)
        self.box_motor.setReadOnly(True)
        self.box_motor.setStyleSheet("background-color: #2C3E50; border: none; padding: 10px;")
        
        right_layout.addWidget(lbl_judul_motor)
        right_layout.addWidget(self.box_motor, stretch=1)
        
        content_layout.addLayout(right_layout, stretch=1)

    def setup_overlays(self):
        """Membuat label gambar mengambang (Overlay) tanpa Layout"""
        # 1. Overlay Splash Screen
        self.lbl_splash = QLabel(self)
        self.lbl_splash.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_splash.setStyleSheet("background-color: black;")
        self.lbl_splash.hide() # Sembunyikan default
        
        pixmap_splash = QPixmap(r"C:\Users\YOGA\Documents\IRIS 2026\NANOPA\Program_Utama_KRAI\python\NANOPA_ne9yzd.webp")
        self.lbl_splash.setPixmap(pixmap_splash.scaled(600, 400, Qt.AspectRatioMode.KeepAspectRatio))
        
        # 2. Overlay Glitch Hacker (Transparan & Bebas Bergerak)
        self.lbl_glitch = QLabel(self)
        self.lbl_glitch.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.lbl_glitch.setStyleSheet("background: transparent;")
        self.lbl_glitch.hide()
        
        # KUNCI: Simpan gambar orisinal ke dalam variabel agar kualitasnya 
        # tidak pecah saat kita melakukan resize acak berulang-ulang nanti
        self.pixmap_glitch_original = QPixmap(r"C:\Users\YOGA\Documents\IRIS 2026\NANOPA\Program_Utama_KRAI\python\programmer.png")

    def resizeEvent(self, event):
        """Otomatis mengubah ukuran Overlay agar menutupi window"""
        super().resizeEvent(event)
        # Hanya splash screen yang dikunci menutupi full layar
        self.lbl_splash.resize(self.width(), self.height())
        # lbl_glitch TIDAK LAGI DI-RESIZE DI SINI karena ukurannya akan random
    
    # ===============================================
    # FUNGSI UI UPDATES (Dipanggil oleh Sinyal secara aman)
    # ===============================================
    def toggle_theme(self, state):
        """Fungsi untuk mengubah tema (Dark/Light) menggunakan Qt Style Sheets"""
        if state == 2: # 2 artinya widget dalam keadaan Checked (Dicentang)
            # --- TEMA TERANG (LIGHT MODE) ---
            self.setStyleSheet("background-color: #ECF0F1; color: black;")
            self.theme_switch.setStyleSheet("color: black;")

            # [BARU] Ubah Top Frame jadi Biru Langit
            self.top_frame.setStyleSheet("background-color: #87CEEB; border-radius: 5px;")
            
            # Ubah warna kotak data menjadi putih dengan tulisan hitam
            style_kotak_terang = "background-color: #FFFFFF; color: black; border: 1px solid #BDC3C7; padding: 10px;"
            self.box_sensor.setStyleSheet(style_kotak_terang)
            self.box_status.setStyleSheet(style_kotak_terang)
            self.box_motor.setStyleSheet(style_kotak_terang)
            
        else: # 0 artinya widget dalam keadaan Unchecked
            # --- TEMA GELAP (DARK MODE - DEFAULT) ---
            self.setStyleSheet("background-color: #1E1E1E; color: white;")
            self.theme_switch.setStyleSheet("color: white;")

            # [BARU] Kembalikan Top Frame ke Biru Gelap
            self.top_frame.setStyleSheet("background-color: #2C3E50; border-radius: 5px;")
            
            # Kembalikan warna kotak data ke biru gelap
            style_kotak_gelap = "background-color: #2C3E50; color: white; border: none; padding: 10px;"
            self.box_sensor.setStyleSheet(style_kotak_gelap)
            self.box_status.setStyleSheet(style_kotak_gelap)
            self.box_motor.setStyleSheet(style_kotak_gelap)




    def ui_update_status(self, text, color):
        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(f"color: {color};")
        
    def ui_show_splash(self):
        self.lbl_splash.raise_() # Paksa ke depan
        self.lbl_splash.show()
        QTimer.singleShot(1000, self.lbl_splash.hide) # Hilang dlm 1 detik
        
    def ui_show_glitch(self, jumlah_kedipan=None):
        """Memunculkan efek glitch secara acak (1 atau 2 kali kedipan)"""
        # 1. Jika fungsi ini baru dipanggil pertama kali, tentukan mau kedip 1x atau 2x
        if jumlah_kedipan is None:
            jumlah_kedipan = random.choice([1, 2])
            
        if jumlah_kedipan > 0:
            # 2. Tentukan ukuran random (misal antara lebar 200px sampai 800px)
            ukuran_acak = random.randint(200, 800)
            
            # Buat ukuran pixmap baru dari gambar aslinya
            pixmap_baru = self.pixmap_glitch_original.scaled(
                ukuran_acak, ukuran_acak, Qt.AspectRatioMode.KeepAspectRatio
            )
            self.lbl_glitch.setPixmap(pixmap_baru)
            self.lbl_glitch.resize(pixmap_baru.width(), pixmap_baru.height())
            
            # 3. Tentukan posisi kordinat X dan Y secara acak di dalam window
            # Batas maksimal dikurangi ukuran gambar agar tidak keluar dari batas window
            batas_x = max(0, self.width() - pixmap_baru.width())
            batas_y = max(0, self.height() - pixmap_baru.height())
            
            posisi_x = random.randint(0, batas_x)
            posisi_y = random.randint(0, batas_y)
            
            # Pindahkan posisi labelnya
            self.lbl_glitch.move(posisi_x, posisi_y)
            
            # 4. Tampilkan gambar
            self.lbl_glitch.raise_()
            self.lbl_glitch.show()
            
            # 5. Durasi tampil juga dibuat acak (sangat cepat, 50 - 150 milidetik)
            durasi_tampil = random.randint(50, 150)
            
            # Panggil fungsi sembunyi dan teruskan sisa kedipan
            QTimer.singleShot(durasi_tampil, lambda: self._hide_and_loop_glitch(jumlah_kedipan - 1))

    def _hide_and_loop_glitch(self, sisa_kedipan):
        """Fungsi pembantu untuk menyembunyikan glitch dan mengatur jeda jika ada kedipan selanjutnya"""
        self.lbl_glitch.hide()
        
        if sisa_kedipan > 0:
            # Beri jeda waktu kosong (layar kembali normal sebentar) sebelum glitch kedua muncul
            # Jeda waktu dibuat acak antara 30 - 100 milidetik
            jeda_kosong = random.randint(30, 100)
            
            # Panggil kembali ui_show_glitch dengan sisa kedipan
            QTimer.singleShot(jeda_kosong, lambda: self.ui_show_glitch(sisa_kedipan))
        
    def ui_update_dashboard(self, data):
        status_data = data.get("Status Robot", {})
        hw_data = data.get("Koneksi Hardware", {})

        # 1. Update Badge
        robot_state = status_data.get("Robot Main State", "UNKNOWN")
        val_upper = str(robot_state).upper()
        self.lbl_robot_state.setText(val_upper)
        
        if val_upper == "STANDBY":
            self.lbl_robot_state.setStyleSheet("background-color: #3498DB; color: white; border-radius: 8px; padding: 5px 15px;")
        elif val_upper == "START":
            self.lbl_robot_state.setStyleSheet("background-color: #F1C40F; color: black; border-radius: 8px; padding: 5px 15px;")
        elif val_upper == "FINISHED":
            self.lbl_robot_state.setStyleSheet("background-color: #3498DB; color: white; border-radius: 8px; padding: 5px 15px;")
        else:
            self.lbl_robot_state.setStyleSheet("background-color: #7F8C8D; color: white; border-radius: 8px; padding: 5px 15px;")

        # 2. Update Hardware Indikator
        if hw_data.get("Input Terhubung", False):
            self.lbl_hw_in.setText("📡 SENSOR: OK")
            self.lbl_hw_in.setStyleSheet("color: #2ECC71;")
        else:
            self.lbl_hw_in.setText("📡 SENSOR: ERROR")
            self.lbl_hw_in.setStyleSheet("color: #E74C3C;")
            
        if hw_data.get("Output Terhubung", False):
            self.lbl_hw_out.setText("⚙️ MOTOR: OK")
            self.lbl_hw_out.setStyleSheet("color: #2ECC71;")
        else:   
            self.lbl_hw_out.setText("⚙️ MOTOR: ERROR")
            self.lbl_hw_out.setStyleSheet("color: #E74C3C;")

        # 3. Update Textbox Biasa (Sensor & Motor)
        self.box_sensor.clear()
        sensor_dict = data.get("Sensor", {})
        for k, v in sensor_dict.items():
            self.box_sensor.append(f"{k: <25}: {v}")
            
        self.box_motor.clear()
        motor_dict = data.get("Motor", {})
        for k, v in motor_dict.items():
            self.box_motor.append(f"{k: <25}: {v}")

        # 4. Update Kotak Status dengan Format HTML (Warna Stabilo)
        html_content = ""
        for key, value in status_data.items():
            val_str = str(value)
            val_upper = val_str.upper()
            
            # Format HTML untuk meniru "tag_add" Tkinter
            if val_upper in ["READY", "IDLE"]:
                val_formatted = f"<span style='background-color: #E74C3C; color: white;'>{val_str}</span>"
            elif val_upper == "FINISHED":
                val_formatted = f"<span style='background-color: #F1C40F; color: black;'>{val_str}</span>"
            else:
                val_formatted = val_str
                
            # Gunakan &nbsp; (spasi HTML) agar jarak kolom sejajar
            key_padded = f"{key}".ljust(25).replace(" ", "&nbsp;")
            html_content += f"{key_padded}: {val_formatted}<br>"
            
        self.box_status.setHtml(f"<pre style='font-family: Courier; font-size: 16px;'>{html_content}</pre>")

    # ===============================================
    # FUNGSI JARINGAN (SOCKET & THREADING)
    # ===============================================
    def cari_jetson_thread(self):
        token_target = "NANOPA"
        self.signals.update_status.emit(f"Mencari Robot ({token_target})...", "#F1C40F")
        
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.bind(('0.0.0.0', 5006))
        self.udp_sock.settimeout(2.0)

        while self.running and not self.is_connected:
            try:
                data, addr = self.udp_sock.recvfrom(1024)
                pesan = data.decode('utf-8')
                
                if pesan.startswith("NANOPA"):
                    _, token, port = pesan.split(":")
                    if token == token_target:
                        self.udp_sock.close()
                        self.connect_tcp(addr[0], int(port))
                        return
            except socket.timeout:
                if random.random() < 0.8:
                    self.signals.show_glitch.emit() # Picu animasi glitch di UI
                continue
            except Exception:
                time.sleep(1)

        if self.udp_sock:
            try: self.udp_sock.close()
            except: pass

    def connect_tcp(self, ip, port):
        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.tcp_sock.connect((ip, port))
            self.is_connected = True
            
            self.signals.update_status.emit(f"Status: TERHUBUNG ({ip})", "#2ECC71")
            self.signals.show_splash.emit() # Picu splash screen
            
            threading.Thread(target=self.terima_data_thread, daemon=True).start()
        except Exception as e:
            self.signals.update_status.emit("Gagal koneksi TCP, mencoba lagi...", "#E74C3C")
            self.is_connected = False
            threading.Thread(target=self.cari_jetson_thread, daemon=True).start()

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
                    # Kirim JSON ke GUI via sinyal
                    self.signals.update_dashboard.emit(data_robot_terkini)
                    
            except Exception:
                break 
                
        if self.running:
            self.signals.reconnect.emit()

    def disconnect_and_reconnect(self):
        self.is_connected = False
        if self.tcp_sock:
            try: self.tcp_sock.close()
            except: pass
            
        self.signals.update_status.emit("TERPUTUS. Mencari ulang...", "#E74C3C")
        self.signals.update_dashboard.emit({}) # Kosongkan UI
        threading.Thread(target=self.cari_jetson_thread, daemon=True).start()

    def closeEvent(self, event):
        """Fungsi bawaan PyQt untuk event penutupan window"""
        self.running = False
        self.is_connected = False
        if self.tcp_sock:
            try: self.tcp_sock.close()
            except: pass
        if self.udp_sock:
            try: self.udp_sock.close()
            except: pass
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MonitorDasborApp()
    window.show()
    sys.exit(app.exec())