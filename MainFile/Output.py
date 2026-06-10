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
            # PERBAIKAN 1: Tambahkan write_timeout agar tidak freeze saat kabel terputus
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.05, write_timeout=0.05)
            print(f"[OUTPUT] Berhasil terhubung ke Arduino Due di port {self.port}")
            return True
        except Exception as e:
            print(f"[OUTPUT] Gagal terhubung ke Arduino Due: {e}")
            return False

    def kirim_data(self, array_output):
        if not self.ser or not self.ser.is_open:
            return False
        num_elements = len(array_output)

        current_time = time.time()

        try:
            if array_output != self.temp_speeds or (current_time - self.last_sent_time > 0.01):
                self.ser.reset_input_buffer() 
                self.temp_speeds = array_output.copy()
                fmt = f'<{num_elements}h'
                data_bytes = struct.pack(fmt, *array_output)
                calc_crc = 0
                for b in data_bytes:
                    calc_crc ^= b 
                    
                payload = struct.pack('<BB', 0xAA, 0x55) + data_bytes + struct.pack('<BBB', calc_crc, 0x0D, 0x0A)
                
                self.ser.write(payload)
                self.last_sent_time = current_time
                return True
                
        except Exception as e:
            self.ser.close() 
            print(f"[OUTPUT] Koneksi terputus mendadak: {e}") # Tambahkan log error
            return False
        