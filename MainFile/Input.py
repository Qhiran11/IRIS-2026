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
            print(f"[INPUT] Berhasil terhubung ke ARDUINO MEGA di port {self.port}")
            self.last_data_time = time.time() # Reset tracker saat koneksi awal
            return True
        except Exception as e:
            print(f"[INPUT] Gagal terhubung ke ARDUINO MEGA: {e}")
            return False

    def trigger_reset_mega(self):
        """Mengirim byte trigger ke Mega untuk melakukan self-reset dan Auto-Reconnect"""
        print("[WARNING] Koneksi MEGA Freeze atau Terputus! Memulai protokol pemulihan...")
        
        if self.ser and self.ser.is_open:
            try:
                # 1. Coba kirim sinyal reset terlebih dahulu
                self.ser.write(b'R') 
                self.ser.flush()
                print("[INPUT] Sinyal reset terkirim. Menunggu Mega booting...")
                
                # Beri waktu 2 detik untuk Arduino Mega melakukan booting ulang
                time.sleep(2.0) 
                
                self.ser.reset_input_buffer()
                self.last_data_time = time.time()
                
            except Exception as e:
                # 2. Jika gagal (Errno 5 I/O Error), berarti port fisik sudah terputus dari OS
                print(f"[ERROR] Gagal mengirim sinyal reset (Hardware Drop): {e}")
                print("[RECOVERY] Memaksa tutup port dan mencoba menghubungkan ulang...")
                
                # Tutup port yang sudah jadi "hantu"
                try:
                    self.ser.close()
                except:
                    pass 
                
                time.sleep(1.0) # Jeda agar sistem operasi Linux mendeteksi ulang USB
                
                # Panggil ulang fungsi connect untuk membuka jalur port baru
                if self.connect():
                    self.last_data_time = time.time()
                    print("[RECOVERY] Berhasil terhubung ulang ke Mega!")
                else:
                    print("[RECOVERY] Gagal terhubung ulang. Cek fisik kabel USB Anda!")
    
    def baca_data(self):
        """
        Membaca paket 17 data int16 (Total 39 byte).
        Struktur Paket: [AA 55] [34 byte data] [CRC] [0D 0A]
        """
        if not self.ser or not self.ser.is_open:
            return None 

        # Cek apakah terjadi Freeze (Tidak ada data valid selama lebih dari 1.5 detik)
        if time.time() - self.last_data_time > 1.5:
            self.trigger_reset_mega()
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