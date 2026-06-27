import serial
import struct
import time

class SensorReader:
    def __init__(self, port='', baudrate=115200):
        """Inisialisasi koneksi ke ARDUINO MEGA"""
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.last_data_time = time.time() # Tracker waktu anti-freeze
        self.connect()

    def connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.05)
            print(f"[INPUT] Berhasil terhubung ke ARDUINO MEGA di port {self.port}. Menunggu data (toleransi boot 4 detik)...")
            self.last_data_time = time.time() + 4.0 # Beri toleransi waktu booting Arduino Mega (4 detik)
            return True
        except Exception as e:
            print(f"[INPUT] Gagal terhubung ke ARDUINO MEGA: {e}")
            return False

    def trigger_koneksi_ulang(self):
        """Menutup port secara paksa dan mencoba menghubungkan ulang (Reconnect)"""
        print("[WARNING] Koneksi MEGA Freeze atau Terputus! Memulai protokol reconnect...")
        
        # 1. Kirim sinyal reset 'R' jika port masih terbuka untuk memicu watchdog reset di Arduino
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(b'R')
                time.sleep(0.05)
            except Exception as e:
                print(f"[RECOVERY] Gagal mengirim sinyal reset 'R': {e}")

        # 2. Tutup port jika masih dianggap terbuka oleh program
        if self.ser:
            try:
                self.ser.close()
                print("[RECOVERY] Port serial berhasil ditutup.")
            except Exception as e:
                print(f"[RECOVERY] Gagal menutup port (mungkin sudah drop dari OS): {e}")
                
        # 3. Beri jeda agar sistem operasi (Windows/Linux) melepas resource USB sepenuhnya
        time.sleep(1.0) 
        
        # 4. Panggil fungsi connect() untuk membuka jalur port baru
        print("[RECOVERY] Mencoba menghubungkan ulang...")
        if self.connect():
            print("[RECOVERY] Berhasil terhubung ulang ke Mega!")
        else:
            print("[RECOVERY] Gagal terhubung ulang. Cek fisik kabel USB Anda!")
    
    def baca_data(self):
        if not self.ser or not self.ser.is_open:
            return None 

        if time.time() - self.last_data_time > 1.5:
            self.trigger_koneksi_ulang()
            return None

        latest_payload = None # Menyimpan data terbaru

        try:
            # Kuras seluruh buffer serial dan hanya ambil data paling baru
            while self.ser.in_waiting >= 39:
                if self.ser.read(1) == b'\xAA':
                    if self.ser.read(1) == b'\x55':
                        packet = self.ser.read(37)
                        if len(packet) == 37:
                            data_payload = packet[:34]
                            received_crc = packet[34]
                            footer = packet[35:37]
                            
                            if footer == b'\x0D\x0A':
                                calc_crc = 0
                                for b in data_payload:
                                    calc_crc ^= b
                                    
                                if calc_crc == received_crc:
                                    latest_payload = data_payload # Simpan yang paling baru

            # Hanya return data jika berhasil mendapatkan paket tervalid paling akhir
            if latest_payload is not None:
                self.last_data_time = time.time() 
                decoded_data = struct.unpack('<17h', latest_payload)
                return list(decoded_data)
                
        except Exception as e:
            print(f"[INPUT] Error membaca serial: {e}")
            
        return None

    
    
    def close(self):
        """Menutup port serial dengan aman."""
        if self.ser:
            try:
                self.ser.close()
                print("[INPUT] Port serial berhasil ditutup.")
            except Exception as e:
                print(f"[INPUT] Gagal menutup port serial: {e}")