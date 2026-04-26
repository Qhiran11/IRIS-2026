import serial
import struct
import time

class ArduinoDueWriter:
    def __init__(self, port='COM4', baudrate=115200):
        """Inisialisasi koneksi ke Arduino Due / Mega"""
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.last_sent_time = 0
        self.temp_speeds = []
        self.connect()

    def connect(self):
        try:
            # Timeout kecil agar program tidak freeze
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.05)
            print(f"[OUTPUT] Berhasil terhubung ke Arduino Due di port {self.port}")
        except Exception as e:
            print(f"[OUTPUT] Gagal terhubung ke Arduino Due: {e}")

    def kirim_data(self, array_output):
        """
        Fungsi ini dipanggil oleh ProsesUtama.py.
        Tugasnya menerima array[12], mengemasnya menjadi paket byte,
        lalu mengirimnya ke Arduino Due.
        """
        if not self.ser or not self.ser.is_open:
            return False

        current_time = time.time()

        try:
            # OPTIMASI: Kirim data JIKA ada perubahan perintah 
            # ATAU untuk "Keep Alive" (misal robot diam, tetap kirim tiap 0.05 detik)
            if array_output != self.temp_speeds or (current_time - self.last_sent_time > 0.01):
                self.temp_speeds = array_output.copy()
                
                # 1. Konversi 13 angka (int16) menjadi 26 byte (Little Endian '<13h')
                data_26b = struct.pack('<13h', *array_output)
                
                # 2. Hitung Checksum (CRC) menggunakan XOR
                calc_crc = 0
                for b in data_26b:
                    calc_crc ^= b
                    
                # 3. Rakit Paket Lengkap
                # - Header: 0xAA, 0x55
                # - Data: 26 byte
                # - CRC: 1 byte hasil hitung
                # - Footer: 0x0D, 0x0A (\r\n)
                payload = struct.pack('<BB', 0xAA, 0x55) + data_26b + struct.pack('<BBB', calc_crc, 0x0D, 0x0A)
                
                # 4. Tembakkan ke Serial
                self.ser.write(payload)
                self.last_sent_time = current_time
                
                return True
                
        except Exception as e:
            # Menangkap error jika kabel Arduino tercabut di tengah jalan
            # Tutup port agar aman dan tidak memicu error beruntun
            self.ser.close() 
            
        return False