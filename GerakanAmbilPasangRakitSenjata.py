import time
# Pastikan Anda mengimpor GerakanDasar jika diperlukan di file ini
# from GerakanDasar import GerakanDasar

class RakitSenjata:
    def __init__(self):
        # HAPUS semua inisialisasi state di sini karena sudah pindah ke robot_data.py
        self.targetJarakKanan = 50
        self.UjungTombak = "ada"

    def transition_to(self, target_state, now, robot, gerak):
        gerak.stop(robot)
        robot.state.rakit_state = "TRANSISI"
        robot.state.rakit_next_state = target_state
        robot.state.rakit_transition_start = now

    def target_tombak(self, robot, jarak_kanan, gerak, now):
        # 1. Cek status sensor tombak
        tombak_terdeteksi = (robot.sensor.cekTombak == 0)

        # 2. Inisialisasi state jika belum ada di memori robot
        if not hasattr(robot.state, 'sedang_menyesuaikan_tombak'):
            robot.state.sedang_menyesuaikan_tombak = False

        # 3. Kunci target saat PERTAMA KALI tombak terlihat di siklus ini
        if tombak_terdeteksi and not robot.state.sedang_menyesuaikan_tombak:
            robot.state.sedang_menyesuaikan_tombak = True
            
            # Daftar titik target valid: 11 + [0, 20, 40, 60, 80, 100]
            titik_referensi = [11, 31, 51, 71, 91, 111]
            
            # Cari nilai di dalam titik_referensi yang jarak selisihnya paling kecil dengan jarak_kanan saat ini
            titik_terdekat = min(titik_referensi, key=lambda x: abs(x - jarak_kanan))
            
            # Langsung timpa/stel target ke titik terdekat yang baru didapat
            robot.targetJarakKanan = titik_terdekat
            print(f"[SENJATA] Tombak terdeteksi di jarak {jarak_kanan}cm! Target disesuaikan otomatis ke {titik_terdekat}cm.")

        # 4. Kalkulasi jarak_pas diletakkan DI SINI (setelah penyesuaian target otomatis di atas)
        jarak_pas = (robot.targetJarakKanan - 1) <= jarak_kanan <= (robot.targetJarakKanan + 1)

        # ==========================================
        # KONDISI A: MODE SESUAIKAN (Tombak sudah ditemukan, sedang dipaskan)
        # ==========================================
        if robot.state.sedang_menyesuaikan_tombak:
            if jarak_pas:
                # Target sudah pas -> Berhenti, Aktifkan relay, matikan mode sesuaikan
                gerak.stop(robot)
                print(f"[SENJATA] Posisi lateral pas ({robot.targetJarakKanan}cm). Mengaktifkan relay tambahan...")
                
                # Reset state untuk persiapan tugas robot selanjutnya
                robot.state.sedang_menyesuaikan_tombak = False 
                return True
            else:
                # Target belum pas -> Terus geser ke titik_terdekat yang sudah disetel
                robot.state.rakit_transition_start = now
                if robot.targetJarakKanan > 40 and 21 <= jarak_kanan <= 28:
                    pass
                else:
                    gerak.geser_ke_titik_kanan(robot, robot.targetJarakKanan)
                return False

        # ==========================================
        # KONDISI B: MODE PENCARIAN (Tombak belum ketemu sama sekali)
        # ==========================================
        else:
            if jarak_pas:
                # Target sudah sampai TAPI tombak tidak ada -> Tambah target kanan +20cm
                gerak.stop(robot)
                
                if not hasattr(robot.state, 'last_search_time'):
                    robot.state.last_search_time = now
                    
                if (now - robot.state.last_search_time > 0.1): # Jeda pencarian 0.1 detik sebelum geser
                    print(f"[SENJATA] Tombak tidak ada di lokasi ({robot.targetJarakKanan}cm). Menggeser target +20cm")
                    if robot.targetJarakKanan > 120:
                        robot.targetJarakKanan -= 120      
                    robot.targetJarakKanan += 20
                    robot.state.last_search_time = now
                return False
            else:
                # Target belum sampai -> Terus geser untuk mencari
                robot.state.rakit_transition_start = now
                if robot.targetJarakKanan > 40 and 21 <= jarak_kanan <= 28:
                    pass
                else:
                    gerak.geser_ke_titik_kanan(robot, robot.targetJarakKanan)
                return False
    
    
    
    
    def jalankan(self, robot, gerak):
        now = time.time()
        jarak_belakang  = robot.sensor.ultrasonic_belakang
        jarak_kanan     = robot.sensor.ultrasonic_kanan
        target_jarak = robot.targetJarakBelakang

        # ---------------------------------------------------------
        # STATE MACHINE MENGGUNAKAN IF-ELIF
        # ---------------------------------------------------------
        if robot.state.rakit_state == "TRANSISI":
            gerak.stop(robot)
            if (now - robot.state.rakit_transition_start > 0.01): # Jeda transisi 0.1 detik
                robot.state.rakit_state = robot.state.rakit_next_state
                robot.state.rakit_transition_start = now
                print(f"[SENJATA] Masuk ke state: {robot.state.rakit_state}")

        elif robot.state.rakit_state == "IDLE":
            print("[SENJATA] Memulai sequence RAKIT...")
            robot.state.rakit_start_time = now # TAHAN TIMER DI SINI
            robot.state.rakit_transition_start = now
            self.transition_to("PERSIAPAN", now, robot, gerak)

        elif robot.state.rakit_state == "PERSIAPAN":
            gerak.maju(robot)
            if (jarak_belakang >= 35):
                self.transition_to("PUTAR1", now, robot, gerak)
                gerak.target_angle = 90                

        elif robot.state.rakit_state == "PUTAR1":
            gerak.hadap_sudut(robot)
            if (robot.sensor.kompas >= gerak.target_angle - 1 and robot.sensor.kompas <= gerak.target_angle + 1): # -90 derajat ± 1
                if (now - robot.state.rakit_transition_start > 0.1): # Delay stabilisasi
                    print("[SENJATA] Menghadap 90 derajat. Mulai Mendekat...")
                    self.transition_to("MENDEKAT", now, robot, gerak)
        
        elif robot.state.rakit_state == "MENDEKAT":
            gerak.base_speed = 100 # Kecepatan pelan
            gerak.max_pwm = 180
            if gerak.mundur_ke_titik(robot, target_jarak, now):
                robot.state.rakit_transition_start = now
                self.transition_to("GESER_KESAMPING", now, robot, gerak)

        elif robot.state.rakit_state == "GESER_KESAMPING":
            gerak.base_speed = 35 # Kecepatan pelan
            gerak.max_pwm = 45
            if gerak.geser_ke_titik_kanan(robot, robot.targetJarakKanan, now):
                self.transition_to("FINISHED", now, robot, gerak)

        elif robot.state.rakit_state == "MUNDUR_PELAN":
            gerak.base_speed = 40 # Jauh lebih pelan
            gerak.max_pwm = 55
            if robot.sensor.cekTombak == 0: # target 2 cm
                gerak.stop(robot)
                robot.motor.relay_tambahan2 = 1
                if (now - robot.state.rakit_transition_start > 0.8):
                    robot.motor.relay_tambahan1 = 1
                if (now - robot.state.rakit_transition_start > 1.0):
                    print("[SENJATA] Tiba di posisi sangat dekat (2cm).")
                    self.transition_to("RELAY_MATI_1", now, robot, gerak)
            else:
                gerak.mundur_ke_titik(robot, target_jarak + 8)
                robot.state.rakit_transition_start = now

        elif robot.state.rakit_state == "RELAY_MATI_1":
            
            # Jeda 1.5s sebelum pindah ke step matikan relay 2

            if jarak_belakang < target_jarak + 1: # target 2 cm
                robot.motor.relay_tambahan2 = 0
                gerak.stop(robot)
            else:
                gerak.mundur_ke_titik(robot, target_jarak)
                robot.state.rakit_transition_start = now
            if (now - robot.state.rakit_transition_start > 1):
                robot.motor.relay_tambahan1 = 0
            if (now - robot.state.rakit_transition_start > 1.5):
                self.transition_to("RELAY_MATI_2", now, robot, gerak)

        elif robot.state.rakit_state == "RELAY_MATI_2":
            # Jeda 3s sebelum lanjut ke MAJU_30CM
            if (now - robot.state.rakit_transition_start >= 1.0):
                self.transition_to("MAJU_30CM", now, robot, gerak)

        elif robot.state.rakit_state == "MAJU_30CM":
            gerak.base_speed = 120
            gerak.max_pwm = 255
            
            if jarak_belakang >= 51: # target 30 cm (52cm sensor belakang)
                gerak.stop(robot)
                if (now - robot.state.rakit_transition_start > 0.1):
                    print("[SENJATA] Tiba di posisi 30cm.")
                    gerak.target_angle = -90
                    self.transition_to("PUTAR_NEG_90", now, robot, gerak)
            else:
                if robot.targetJarakKanan <= 35:
                    gerak.maju_diagonal_kiri(robot)
                else:
                    gerak.mundur_ke_titik(robot, 52)
                robot.state.rakit_transition_start = now

        elif robot.state.rakit_state == "PUTAR_NEG_90":
            gerak.base_speed = 100
            gerak.max_pwm = 110
            gerak.hadap_sudut(robot)
            if (robot.sensor.kompas >= gerak.target_angle - 1 and robot.sensor.kompas <= gerak.target_angle + 1): # -90 derajat ± 1
                if (now - robot.state.rakit_transition_start > 0.2):
                    print("[SENJATA] Kembali menghadap -90 derajat.")
                    self.transition_to("DELAY_1", now, robot, gerak)

        elif robot.state.rakit_state == "DELAY_1":
            gerak.stop(robot)
            self.transition_to("BUKA_PEGANGAN", now, robot, gerak)
        
        elif robot.state.rakit_state == "BUKA_PEGANGAN":
            if (robot.sensor.data_qr ==  "Qr Ditemukan"):
                robot.motor.relay_tambahan2 = 1
                self.transition_to("FINISHED", now, robot, gerak)
                gerak.target_angle = 0
            else:
                pass
        
        elif robot.state.rakit_state == "PUTARKENOL":
            gerak.base_speed = 80
            gerak.max_pwm = 90
            gerak.hadap_sudut(robot)
            if (robot.sensor.kompas >= gerak.target_angle - 1 and robot.sensor.kompas <= gerak.target_angle + 1): # -90 derajat ± 1
                # self.transition_to("BALIK_KE_POSISI", now, robot, gerak)
                return True
                # if (now - robot.state.rakit_transition_start > 0.1):
                #     self.transition_to("BALIK_KE_POSISI", now, robot, gerak)
            else:
                robot.state.rakit_transition_start = now
                pass
        
        elif robot.state.rakit_state == "BALIK_KE_POSISI1":
            gerak.base_speed = 80
            gerak.max_pwm = 100
            gerak.mundur(robot)
            if (jarak_belakang <= 40):
                self.transition_to("FINISHED", now, robot, gerak)
            else:
                pass

        elif robot.state.rakit_state == "BALIK_KE_POSISI2":
            gerak.base_speed = 80
            gerak.max_pwm = 100
            gerak.mundur(robot)
            if (jarak_belakang <= 40):
                self.transition_to("FINISHED", now, robot, gerak)
            else:
                pass
            
            

        elif robot.state.rakit_state == "FINISHED":
            robot.state.rakit_is_done = True
            gerak.stop(robot)
            return True

        return False