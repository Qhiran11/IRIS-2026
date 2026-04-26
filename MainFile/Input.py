import serial
import struct
import time

class SensorReader:
    def __init__(self, port='', baudrate=115200):
        """Inisialisasi koneksi ke STM32"""
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.connect()

    def connect(self):
        try:
            # Timeout kecil agar program tidak freeze jika STM32 mati
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.05)
            print(f"[INPUT] Berhasil terhubung ke STM32 di port {self.port}")
        except Exception as e:
            print(f"[INPUT] Gagal terhubung ke STM32: {e}")

    def baca_data(self):
        """
        Fungsi ini dipanggil terus-menerus oleh ProsesUtama.py.
        Tugasnya membaca buffer, memvalidasi paket, dan mereturn array.
        """
        if not self.ser or not self.ser.is_open:
            return None # Kembalikan None jika tidak ada koneksi

        try:
            # Buffer harus memiliki minimal 29 byte (2 Header + 24 Data + 1 CRC + 2 Footer)
            while self.ser.in_waiting >= 29:
                
                # 1. Sinkronisasi Header 1 (0xAA)
                if self.ser.read(1) == b'\xAA':
                    
                    # 2. Sinkronisasi Header 2 (0x55)
                    if self.ser.read(1) == b'\x55':
                        
                        # 3. Baca sisa paket (27 byte)
                        packet = self.ser.read(27)
                        
                        if len(packet) == 27:
                            data_24b = packet[:24]
                            received_crc = packet[24]
                            footer = packet[25:27]
                            
                            # 4. Validasi Footer
                            if footer == b'\x0D\x0A':
                                
                                # 5. Hitung ulang CRC
                                calc_crc = 0
                                for b in data_24b:
                                    calc_crc ^= b
                                    
                                # 6. Validasi CRC
                                if calc_crc == received_crc:
                                    
                                    # 7. Ekstrak 24 byte data kembali menjadi array 12 integer
                                    # '<12h' = Little Endian, 12 buah short integer (16-bit)
                                    received_speeds = struct.unpack('<12h', data_24b)
                                    
                                    # KEMBALIKAN ARRAY KE PROSES UTAMA
                                    return list(received_speeds)
                                else:
                                    # print("CRC Error!")
                                    pass
        except Exception as e:
            # Menangkap error jika kabel tercabut di tengah jalan
            pass
            
        return None # Jika paket belum lengkap atau rusak, kembalikan None