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
        """
        Membaca paket 17 data int16 (Total 39 byte).
        Struktur Paket: [AA 55] [34 byte data] [CRC] [0D 0A]
        
        Pemetaan data payload (17 int16):
        - index 0: cmpsHeading (Kompas)
        - index 1: S4 (Depan)
        - index 2: S7 (Kiri via UART)
        - index 3: S2 (Kanan)
        - index 4: S5 (Belakang)
        - index 5: tombol_start (Nano_A)
        - index 6: tombol_reset (Nano_B)
        - index 7: S3 (Bawah Depan)
        - index 8: S1 (Bawah Tengah)
        - index 9: S6 (Bawah Belakang)
        - index 10: cmpsPitch (Pitch Kompas)
        - index 11-16: Unused (Cadangan)
        """
        if not self.ser or not self.ser.is_open:
            return None 

        # Cek apakah terjadi Freeze (Tidak ada data valid selama lebih dari 1.5 detik)
        if time.time() - self.last_data_time > 1.5:
            self.trigger_koneksi_ulang()  # <--- Pemanggilan fungsi yang baru
            return None

        try:
            while self.ser.in_waiting >= 39:
                # 1. Sinkronisasi Header 1 (0xAA)
                if self.ser.read(1) == b'\xAA':
                    # 2. Sinkronisasi Header 2 (0x55)
                    if self.ser.read(1) == b'\x55':
                        # 3. Baca sisa paket (37 byte)
                        packet = self.ser.read(37)
                        
                        if len(packet) == 37:
                            data_payload = packet[:34]
                            received_crc = packet[34]
                            footer = packet[35:37]
                            
                            # 4. Validasi Footer
                            if footer == b'\x0D\x0A':
                                
                                # 5. Hitung ulang CRC
                                calc_crc = 0
                                for b in data_payload:
                                    calc_crc ^= b
                                    
                                # 6. Validasi CRC
                                if calc_crc == received_crc:
                                    
                                    # UPDATE WAKTU TRACKER: Data sukses terbaca, berarti Mega tidak freeze!
                                    self.last_data_time = time.time() 
                                    
                                    # 7. Ekstrak data
                                    decoded_data = struct.unpack('<17h', data_payload)
                                    return list(decoded_data)
        except Exception:
            pass
            
        return None

    def close(self):
        """Menutup port serial dengan aman."""
        if self.ser:
            try:
                self.ser.close()
                print("[INPUT] Port serial berhasil ditutup.")
            except Exception as e:
                print(f"[INPUT] Gagal menutup port serial: {e}")