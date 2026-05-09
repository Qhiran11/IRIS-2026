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
            # Timeout kecil agar program tidak freeze jika ARDUINO MEGA mati
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.05)
            print(f"[INPUT] Berhasil terhubung ke ARDUINO MEGA di port {self.port}")
            return True
        except Exception as e:
            print(f"[INPUT] Gagal terhubung ke ARDUINO MEGA: {e}")
            return False

    def baca_data(self):
        """
        Membaca buffer, memvalidasi paket 13 data int16, dan mereturn array.
        """
        if not self.ser or not self.ser.is_open:
            return None 

        try:
            # Buffer minimal 31 byte:
            # [2 Header] + [26 Data (13 * 2)] + [1 CRC] + [2 Footer] = 31 byte
            while self.ser.in_waiting >= 31:
                
                # 1. Sinkronisasi Header 1 (0xAA)
                if self.ser.read(1) == b'\xAA':
                    
                    # 2. Sinkronisasi Header 2 (0x55)
                    if self.ser.read(1) == b'\x55':
                        
                        # 3. Baca sisa paket (29 byte)
                        # Terdiri dari: 26 byte data + 1 byte CRC + 2 byte Footer
                        packet = self.ser.read(29)
                        
                        if len(packet) == 29:
                            data_payload = packet[:26]   # 26 byte data murni
                            received_crc = packet[26]    # Byte ke-27 (indeks 26)
                            footer = packet[27:29]       # 2 byte terakhir
                            
                            # 4. Validasi Footer
                            if footer == b'\x0D\x0A':
                                
                                # 5. Hitung ulang CRC
                                calc_crc = 0
                                for b in data_payload:
                                    calc_crc ^= b
                                    
                                # 6. Validasi CRC
                                if calc_crc == received_crc:
                                    
                                    # 7. Ekstrak 26 byte data kembali menjadi array 13 integer
                                    # '<13h' = Little Endian, 13 buah short integer (16-bit)
                                    # Indeks: 0:Heading, 1:VL, 2-4:US, 5:Prox B, 6-9:Limit, 10:Prox D, 11:Pitch, 12:Roll
                                    decoded_data = struct.unpack('<13h', data_payload)
                                    
                                    return list(decoded_data)
                                else:
                                    # print("CRC Error!")
                                    pass
        except Exception as e:
            # Menangkap error jika kabel tercabut atau gangguan serial
            # print(f"Error pembacaan: {e}")
            pass
            
        return None