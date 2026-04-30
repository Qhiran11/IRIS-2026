import time

class GerakanNaikTurun:
    def __init__(self):
        self.state = "IDLE"
        self.sub_state = "SERONG" # Untuk mengatur langkah di dalam fungsi tertentu
        self.sub_state1 = "MAJU" # Untuk mengatur langkah di dalam fungsi tertentu
        self.start_time = 0
        self.is_done = False

    def reset(self):
        self.state = "IDLE"
        self.sub_state = "SERONG"

        self.is_done = False

    # ==============================================================
    # FUNGSI 1: GERAK KE TENGAH DAN MAJU
    # ==============================================================
    def _proses_ke_tengah(self, robot, gerak):

        now = time.time()
        
        match self.sub_state:
            case "SERONG":
                gerak.base_speed = gerak.max_pwm = 140
                gerak.maju_diagonal_kanan(robot)
                print (self.sub_state)
                
                if (robot.sensor.jarak_depan != -1 and robot.sensor.jarak_depan < 600):
                    gerak.stop(robot)
                    # return True # Mengembalikan True jika tugas selesai
                    self.sub_state = "PASKAN"
                    self.start_time = now
            
            case "PASKAN":
                # Panggil fungsi maju ke jarak 2cm
                gerak.geser_ke_tengah(robot)
                
                # Cek apakah sudah dekat tembok depan
                if gerak.geser_ke_tengah(robot) == True: 
                    gerak.stop(robot)
                    print("[NAIK-TURUN] Posisi Pas. Siap Naik.")
                    return True # Mengembalikan True jika tugas selesai
        return False # Masih dalam proses, kembalikan False

    # ==============================================================
    # FUNGSI 2: GERAKAN NAIK
    # ==============================================================
    def _proses_naik(self, robot, gerak):
        now = time.time()
        
        match self.sub_state1:
            case "MAJU":
                gerak.base_speed = gerak.max_pwm = 80
                gerak.maju(robot)
                print (self.sub_state1)
                
                if (robot.sensor.jarak_depan != -1 and robot.sensor.jarak_depan < 30):
                    gerak.stop(robot)
                    # return True # Mengembalikan True jika tugas selesai
                    self.sub_state1 = "PASKAN"
                    gerak.target_angle = 0
            
            case "PASKAN":
                # Panggil fungsi maju ke jarak 2cm
                gerak.hadap_sudut(robot)
                
                # Cek apakah sudah dekat tembok depan
                if robot.sensor.kompas == 0 : 
                    gerak.stop(robot)
                    print("[NAIK-TURUN] Posisi Pas. Siap Naik.")
                    self.sub_state1 = "NAIK"
            
            case "NAIK":
                gerak.naik(robot)
        return False # Masih dalam proses, kembalikan False
    # ==============================================================
    # FUNGSI 3: GERAKAN TURUN
    # ==============================================================
    def _proses_turun(self, robot, gerak, now):
        # TODO: Masukkan perintah motor capit/lifter untuk turun di sini
        # Contoh: robot.motor.m5_pwm = -100
        
        # Simulasi selesai dalam 2 detik
        if (now - self.start_time > 2.0):
            gerak.stop(robot)
            print("[NAIK-TURUN] Proses Turun Selesai.")
            return True
            
        return False

    # ==============================================================
    # FUNGSI UTAMA ("MANDOR") YANG DIPANGGIL DI PROSES UTAMA
    # ==============================================================
    def jalankan(self, robot, gerak, target_angle):
        now = time.time()

        match self.state:
            case "IDLE":
                print("[NAIK-TURUN] Memulai Sequence...")
                self.start_time = now
                self.state = "KE_TENGAH"
                gerak.target_angle = target_angle

            case "KE_TENGAH":
                # Tunggu fungsi ini mengembalikan True baru pindah state
                if self._proses_ke_tengah(robot, gerak, now):
                    self.state = "NAIK"
                    self.start_time = now

            case "NAIK":
                if self._proses_naik(robot, gerak, now):
                    self.state = "TURUN"
                    self.start_time = now

            case "TURUN":
                if self._proses_turun(robot, gerak, now):
                    self.state = "FINISHED"

            case "FINISHED":
                self.is_done = True
                return True

        return False