import serial
import struct
import time

class SensorReader:
    def __init__(self, port='', baudrate=115200):
        """Inisialisasi koneksi ke ARDUINO MEGA"""
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.connect()

    def connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.05)
            print(f"[INPUT] Berhasil terhubung ke ARDUINO MEGA di port {self.port}")
            return True
        except Exception as e:
            print(f"[INPUT] Gagal terhubung ke ARDUINO MEGA: {e}")
            return False

    def baca_data(self):
        """
        Membaca paket 17 data int16 (Total 39 byte).
        Struktur Paket: [AA 55] [34 byte data] [CRC] [0D 0A]
        """
        if not self.ser or not self.ser.is_open:
            return None 

        try:
            # Perhitungan panjang paket baru:
            # [2 Header] + [34 Data (17 * 2)] + [1 CRC] + [2 Footer] = 39 byte
            while self.ser.in_waiting >= 39:
                
                # 1. Sinkronisasi Header 1 (0xAA)
                if self.ser.read(1) == b'\xAA':
                    
                    # 2. Sinkronisasi Header 2 (0x55)
                    if self.ser.read(1) == b'\x55':
                        
                        # 3. Baca sisa paket (37 byte)
                        # Terdiri dari: 34 byte data + 1 byte CRC + 2 byte Footer
                        packet = self.ser.read(37)
                        
                        if len(packet) == 37:
                            data_payload = packet[:34]   # 34 byte data murni (17 int16)
                            received_crc = packet[34]    # Byte ke-35 (indeks 34)
                            footer = packet[35:37]       # 2 byte terakhir
                            
                            # 4. Validasi Footer
                            if footer == b'\x0D\x0A':
                                
                                # 5. Hitung ulang CRC
                                calc_crc = 0
                                for b in data_payload:
                                    calc_crc ^= b
                                    
                                # 6. Validasi CRC
                                if calc_crc == received_crc:
                                    
                                    # 7. Ekstrak 34 byte data menjadi 17 integer
                                    # '<17h' = Little Endian, 17 buah short integer (16-bit)
                                    decoded_data = struct.unpack('<17h', data_payload)
                                    
                                    return list(decoded_data)
                                else:
                                    # print("CRC Error!")
                                    pass
        except Exception as e:
            # print(f"Error pembacaan: {e}")
            pass
            
        return None