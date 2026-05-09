import time
from GerakanCapitKFS import GerakanCapitKFS

class GerakanAmbilKFS:
    def __init__(self):
        self.capit = GerakanCapitKFS()
        self.state = "IDLE"
        self.start_time = 0
        self.is_done = False
        self.then = 0.0

        # --- DURASI SETIAP FASE (Atur Sesuai Realita Mekanik) ---
        # Waktu yang dibutuhkan untuk memastikan motor sampai di posisi tujuan
        self.waktu_steady = 1.0     # Mundur full & putar depan biasanya butuh 1 detik
        self.waktu_bersiap = 2.0   # Maju full ke depan biasanya butuh 1.5 detik
        self.waktu_ambil = 2.5      # Putar belakang + Mundur full bersamaan butuh 2 detik
        self.waktu_kembali = 1.0    # Kembali ke pose awal butuh 1 detik

    def reset(self):
        """Reset sequence agar bisa dipanggil ulang dari awal"""
        self.state = "IDLE"
        self.is_done = False

    def jalankan_kombinasi_1(self, robot):
        """
        Urutan Kombinasi 1 KFS.
        Harus dipanggil berulang-ulang di loop utama (Non-Blocking).
        Mengembalikan True jika seluruh urutan selesai.
        """
        now = time.time()

        # ==========================================
        # STATE 0: INISIALISASI
        # ==========================================
        match self.state:
            case "IDLE":
                selesai = self.capit.putar_capit_kebelakang(robot)
                self.then = time.time()
                if (selesai):
                    self.then = time.time()
                    self.state = "READY"
                    
                

            case "READY":
                self.capit.putar_capit_kedepan(robot)
                self.capit.buka(robot)
                if (time.time() - self.then > 1.64):
                    self.capit.capit_stop(robot)
                    self.then = time.time()
                    self.state = "CAPITMAJU"
            
            case "CAPITMAJU":
                self.capit.MajuMundur(robot, -800)
                if (time.time() - self.then > 1):
                    self.capit.capit_stop(robot)
                    self.capit.MajuMundur(robot, 0)
                    self.state = "JEPIT"
            
            case "JEPIT":
                selesai = self.capit.jepit(robot)
                if (selesai):
                    self.state = "MUNDUR"
                    self.then = now
            
            case "MUNDUR":
                self.capit.MajuMundur(robot, 800)
                if (now - self.then > 0.8):
                    self.state = "ANGKUT"
            
            case "ANGKUT":
                selesai = self.capit.putar_capit_kebelakang(robot)
                if (selesai):
                    self.state = "LEPAS"
                    self.then = now
            
            case "LEPAS":
                selesai = self.capit.buka(robot)
                if (selesai):
                    self.state = "BACK"
                    self.then = now
            
            case "BACK":
                self.capit.putar_capit_kedepan(robot)
                if (time.time() - self.then > 0.2):
                    self.then = time.time()
                    self.state = "FINISHED"
            

            

            case "FINISHED":
                return True

        return False # Urutan masih berjalan