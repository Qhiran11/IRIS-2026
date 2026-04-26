import time
from GerakanCapitKFS import GerakanCapitKFS

class GerakanAmbilKFS:
    def __init__(self):
        self.capit = GerakanCapitKFS()
        self.state = "IDLE"
        self.start_time = 0
        self.is_done = False

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

    def jalankan_kombinasi_1(self, robot, writer):
        """
        Urutan Kombinasi 1 KFS.
        Harus dipanggil berulang-ulang di loop utama (Non-Blocking).
        Mengembalikan True jika seluruh urutan selesai.
        """
        now = time.time()

        # ==========================================
        # STATE 0: INISIALISASI
        # ==========================================
        if self.state == "IDLE":
            print("[KFS] Memulai Kombinasi 1...")
            self.start_time = now
            self.state = "STEADY"

        # ==========================================
        # STATE 1: STEADY
        # Capit di posisi belakang, arah putar lurus ke depan (BERSAMAAN)
        # ==========================================
        elif self.state == "STEADY":
            durasi_berjalan = now - self.start_time
            if durasi_berjalan < self.waktu_steady:
                # Perintahkan kedua motor sekaligus (Akan jalan bersamaan)
                self.capit.MajuMundur(robot, writer, "mundur")
                # self.capit.putar_dinamis(robot, writer, "depan")
            else:
                print("[KFS] Menuju Bersiap...")
                self.start_time = now
                self.state = "BERSIAP"

        # ==========================================
        # STATE 2: BERSIAP
        # Capit maju maks kedepan
        # ==========================================
        elif self.state == "BERSIAP":
            durasi_berjalan = now - self.start_time
            if durasi_berjalan < self.waktu_bersiap:
                self.capit.MajuMundur(robot, writer, "maju")
            else:
                print("[KFS] Menuju Ambil...")
                self.start_time = now
                self.state = "AMBIL"

        # ==========================================
        # STATE 3: AMBIL DAN LETAKKAN
        # Putar capit kebelakang, capit bergerak maks kebelakang (BERSAMAAN)
        # ==========================================
        elif self.state == "AMBIL":
            durasi_berjalan = now - self.start_time
            if durasi_berjalan < self.waktu_ambil:
                self.capit.MajuMundur(robot, writer, "mundur")
                self.capit.putar_dinamis(robot, writer, "belakang")
                
            else:
                print("[KFS] Menuju Kembali...")
                self.start_time = now
                self.state = "KEMBALI"

        # ==========================================
        # STATE 4: KEMBALI KE POSISI STEADY
        # ==========================================
        elif self.state == "KEMBALI":
            durasi_berjalan = now - self.start_time
            if durasi_berjalan < self.waktu_kembali:
                #  self.capit.MajuMundur(robot, writer, "mundur")
                 self.capit.putar_dinamis(robot, writer, "depan")
            else:
                print("[KFS] Kombinasi 1 SELESAI!")
                self.state = "FINISHED"

        # ==========================================
        # STATE 5: FINISHED
        # ==========================================
        elif self.state == "FINISHED":
            self.is_done = True
            return True

        return False # Urutan masih berjalan