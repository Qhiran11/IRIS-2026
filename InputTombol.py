import Jetson.GPIO as GPIO
import time

class MatrixKeypad:
    def __init__(self):
        # 1. Tentukan Pin (Gunakan penomoran BOARD/Fisik pada Jetson Nano)
        # Pastikan pin ini aman dan tidak dipakai oleh I2C/SPI tanpa sengaja
        self.ROW_PINS = [15, 16, 18, 19] # 4 Pin untuk Baris (R1, R2, R3, R4)
        self.COL_PINS = [21, 22, 23]     # 3 Pin untuk Kolom (C1, C2, C3)

        # 2. Pemetaan Layout Tombol 
        # Sesuaikan dengan bentuk fisik D-Pad / Keypad Anda
        self.KEY_MAP = [
            ['1', '2', '3'],
            ['4', '5', '6'],
            ['7', '8', '9'],
            ['*', '0', '#']
        ]

        # 3. Setup GPIO
        GPIO.setmode(GPIO.BOARD)
        
        # Setup Kolom sebagai Input dengan Pull-Up Internal (Default HIGH)
        for col in self.COL_PINS:
            GPIO.setup(col, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Setup Baris sebagai Output, default HIGH
        for row in self.ROW_PINS:
            GPIO.setup(row, GPIO.OUT, initial=GPIO.HIGH)
            
        self.last_key_pressed = None
        self.last_press_time = 0

    def baca_tombol(self):
        """Membaca tombol mana yang sedang ditekan"""
        pressed_key = None
        
        # Scan tiap baris
        for i, row in enumerate(self.ROW_PINS):
            # Tarik baris ini ke LOW
            GPIO.output(row, GPIO.LOW)
            
            # Cek apakah ada kolom yang ikut menjadi LOW (karena ditekan)
            for j, col in enumerate(self.COL_PINS):
                if GPIO.input(col) == GPIO.LOW:
                    pressed_key = self.KEY_MAP[i][j]
            
            # Kembalikan baris ke HIGH agar tidak mengganggu baris lain
            GPIO.output(row, GPIO.HIGH)
            
        # --- Fitur Anti-Bouncing (Debounce) ---
        now = time.time()
        if pressed_key is not None:
            # Cegah tombol terbaca ribuan kali dalam 1 detik
            if pressed_key != self.last_key_pressed or (now - self.last_press_time) > 0.5:
                self.last_key_pressed = pressed_key
                self.last_press_time = now
                return pressed_key
        else:
            # Jika tidak ada yang ditekan, reset state
            if (now - self.last_press_time) > 0.2:
                self.last_key_pressed = None

        return None

    def cleanup(self):
        """Wajib dipanggil saat program berhenti"""
        GPIO.cleanup()

# ==============================================================
# BLOK TESTING MANUAL (Hanya berjalan jika file ini di-run langsung)
# ==============================================================
if __name__ == "__main__":
    print("Memulai Testing Matrix Keypad...")
    print("Tekan tombol di D-Pad/Keypad Anda. Tekan 'Ctrl+C' untuk keluar.")
    
    keypad = MatrixKeypad()
    
    try:
        while True:
            tombol = keypad.baca_tombol()
            if tombol:
                print(f"[TEST] Tombol ditekan: {tombol}")
            
            time.sleep(0.05) # Delay kecil untuk stabilitas CPU
            
    except KeyboardInterrupt:
        print("\nTesting dihentikan oleh user.")
    finally:
        keypad.cleanup()
        print("GPIO Cleanup selesai.")