import Jetson.GPIO as GPIO
import time

class TombolKontrol:
    def __init__(self, pin_start=31, pin_reset=33):
        """
        Menggunakan penomoran pin BOARD (Fisik).
        Default: 
        - Tombol Start di Pin 31
        - Tombol Reset di Pin 33
        """
        self.PIN_START = pin_start
        self.PIN_RESET = pin_reset

        # Setup GPIO
        GPIO.setmode(GPIO.BOARD)
        
        # Setup sebagai Input dengan Pull-Up Internal (Default bernilai HIGH)
        # Jika tombol ditekan, arus mengalir ke Ground (GND), sehingga terbaca LOW.
        GPIO.setup(self.PIN_START, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.PIN_RESET, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
        # Variabel untuk Debounce (Mencegah tombol terbaca berkali-kali dalam 1 ketukan)
        self.last_press_time_start = 0
        self.last_press_time_reset = 0
        self.debounce_delay = 0.5 # Jeda 0.5 detik antar ketukan

    def baca_start(self):
        """Mengembalikan True jika tombol Start ditekan"""
        now = time.time()
        # Jika pin LOW, artinya tombol sedang ditekan (terhubung ke GND)
        if GPIO.input(self.PIN_START) == GPIO.LOW:
            if (now - self.last_press_time_start) > self.debounce_delay:
                self.last_press_time_start = now
                return True
        return False

    def baca_reset(self):
        """Mengembalikan True jika tombol Reset ditekan"""
        now = time.time()
        if GPIO.input(self.PIN_RESET) == GPIO.LOW:
            if (now - self.last_press_time_reset) > self.debounce_delay:
                self.last_press_time_reset = now
                return True
        return False

    def cleanup(self):
        """Wajib dipanggil saat program berhenti untuk melepaskan pin GPIO"""
        GPIO.cleanup()

# ==============================================================
# BLOK TESTING MANUAL (Hanya berjalan jika file ini di-run langsung)
# ==============================================================
if __name__ == "__main__":
    print("Memulai Testing Tombol Start & Reset...")
    print("Tekan tombol. Tekan 'Ctrl+C' untuk keluar.")
    
    tombol = TombolKontrol()
    
    try:
        while True:
            if tombol.baca_start():
                print(f"[TEST] Tombol START ditekan!")
                
            if tombol.baca_reset():
                print(f"[TEST] Tombol RESET ditekan!")
            
            time.sleep(0.05) # Delay kecil untuk stabilitas CPU
            
    except KeyboardInterrupt:
        print("\nTesting dihentikan oleh user.")
    finally:
        tombol.cleanup()
        print("GPIO Cleanup selesai.")