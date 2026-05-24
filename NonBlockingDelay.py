import time

class NonBlockingDelay:
    def __init__(self):
        # Inisialisasi dengan 0 agar saat dipanggil pertama kali langsung True
        self.last_time = 0

    def check_delay(self, seconds):
        """
        Mengecek apakah waktu sudah berlalu.
        Mengembalikan True jika sudah lewat, False jika belum.
        """
        current_time = time.time()
        if current_time - self.last_time >= seconds:
            self.last_time = current_time
            return True
        return False