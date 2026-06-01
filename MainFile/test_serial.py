# File: MainFile/test_serial.py
import serial
import time
import sys

def main():
    port = '/dev/ttyUSB0'
    baudrate = 115200
    print(f"Membuka port {port} dengan baudrate {baudrate}...")
    
    try:
        ser = serial.Serial(port, baudrate, timeout=1.0)
        print("Port berhasil dibuka! Memulai pembacaan data mentah...")
    except Exception as e:
        print(f"Gagal membuka port: {e}")
        sys.exit(1)
        
    start_time = time.time()
    packet_count = 0
    
    try:
        while True:
            in_waiting = ser.in_waiting
            if in_waiting > 0:
                data = ser.read(in_waiting)
                print(f"[{time.time() - start_time:.2f}s] Menerima {len(data)} byte: {data.hex().upper()}")
                # Cek jika ada header paket 0xAA 0x55
                if b'\xAA\x55' in data:
                    packet_count += 1
                    print(f"   -> Ditemukan header paket KRAI (0xAA 0x55) ke-{packet_count}!")
            else:
                time.sleep(0.1)
                
    except KeyboardInterrupt:
        print("\nPengujian dihentikan oleh user.")
    finally:
        ser.close()
        print("Port ditutup.")

if __name__ == "__main__":
    main()
