class MappingHutan:
    def __init__(self):
        # 1. Peta Ketinggian (Petak 0 adalah luar arena Start, Petak 13 adalah Zona 3)
        self.tinggi_petak = {
            0: 0,   
            1: 40,  2: 20,  3: 40,
            4: 20,  5: 40,  6: 60,  # Nilai 4 dan 6 bisa diupdate random nanti
            7: 40,  8: 60,  9: 40,
            10: 20, 11: 40, 12: 20,
            13: 0   
        }
        
        # 2. Peta Koneksi & Sudut Relatif (Dari mana, ke mana, arahnya berapa derajat)
        # 0 = Maju, 90 = Kanan, -90 = Kiri, 180/-180 = Mundur
        self.tetangga = {
            0: {2: 0}, # Dari luar menuju masuk petak 2 lurus
            2: {0: 180, 1: -90, 3: 90, 5: 0},
            5: {2: 180, 4: -90, 6: 90, 8: 0},
            8: {5: 180, 7: -90, 9: 90, 11: 0},
            11: {8: 180, 10: -90, 12: 90},
            12: {11: -90, 9: 180, 13: 0} # Ke zona 3 lurus (Asumsi lurus utara)
            # Anda bisa tambahkan koneksi petak lain nanti
        }
        
        # 3. ARRAY JALUR DINAMIS (Tinggal ubah array ini untuk mengganti rute!)
        self.rute = [0, 2, 5, 8, 11, 12, 13]
        self.index_rute = 0
        
    def get_next_move(self):
        """Menghitung jenis aksi (NAIK/TURUN) dan arah hadap robot"""
        if self.index_rute >= len(self.rute) - 1:
            return None # Rute sudah selesai
            
        petak_sekarang = self.rute[self.index_rute]
        petak_tujuan = self.rute[self.index_rute + 1]
        
        tinggi_awal = self.tinggi_petak[petak_sekarang]
        tinggi_tujuan = self.tinggi_petak[petak_tujuan]
        
        # Cari sudut absolut ke tujuan dari data dictionary tetangga
        sudut_tujuan = self.tetangga[petak_sekarang][petak_tujuan]
        
        # Hitung aksi dan hadap
        if tinggi_tujuan > tinggi_awal:
            aksi = "NAIK"
            sudut_hadap = sudut_tujuan # Naik menghadap target
            
        elif tinggi_tujuan < tinggi_awal:
            aksi = "TURUN"
            # Turun membelakangi target (Sudut target - 180)
            sudut_hadap = sudut_tujuan - 180 
            
            # Normalisasi PID Kompas (-180 sampai 180)
            if sudut_hadap <= -180: 
                sudut_hadap += 360
                
        else:
            aksi = "DATAR"
            sudut_hadap = sudut_tujuan # Asumsi datar sementara pakai hadap lurus
            
        return aksi, sudut_hadap, petak_tujuan
        
    def step_selesai(self):
        """Dipanggil ketika gerakan satu petak sudah tuntas"""
        self.index_rute += 1