import time
# Pastikan Anda mengimpor GerakanDasar jika diperlukan di file ini
# from GerakanDasar import GerakanDasar

class RakitSenjata:
    def __init__(self):
        # HAPUS semua inisialisasi state di sini karena sudah pindah ke robot_data.py
        self.targetJarakKanan = 50
        self.Dummy = "Dum"

    def transition_to(self, target_state, now, robot, gerak):
        gerak.stop(robot)
        robot.state.rakit_state = "TRANSISI"
        robot.state.rakit_next_state = target_state
        robot.state.rakit_transition_start = now
   
    def jalankan(self, robot, gerak, target_angle, target_jarak):
        now = time.time()
        jarak_belakang       = robot.sensor.ultrasonic_belakang
        jarak_kanan = robot.sensor.ultrasonic_kanan

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
                gerak.target_angle = target_angle                

        elif robot.state.rakit_state == "PUTAR1":
            gerak.hadap_sudut(robot)
            if (robot.sensor.kompas >= (target_angle - 2) and robot.sensor.kompas <= (target_angle + 2)):
                if (now - robot.state.rakit_transition_start > 0.1): # Delay stabilisasi
                    print("[SENJATA] Menghadap 90 derajat. Mulai Mendekat...")
                    self.transition_to("MENDEKAT", now, robot, gerak)
        
        elif robot.state.rakit_state == "MENDEKAT":
            gerak.base_speed = 45 # Kecepatan pelan
            gerak.max_pwm = 55
            
            if (jarak_belakang == -1): 
                gerak.mundur(robot)
                robot.state.rakit_transition_start = now            
            elif jarak_belakang < target_jarak + 16: 
                gerak.stop(robot)
                if (now - robot.state.rakit_transition_start > 0.2): 
                    print(f"[SENJATA] Tiba di posisi dekat ({target_jarak}cm).")
                    self.transition_to("GESER_KESAMPING", now, robot, gerak)

            else:
                gerak.mundur_ke_titik(robot, target_jarak)
                robot.state.rakit_transition_start = now

        elif robot.state.rakit_state == "GESER_KESAMPING":
            gerak.base_speed = 35 # Kecepatan pelan
            gerak.max_pwm = 45
            
            if jarak_kanan >= (robot.targetJarakKanan - 1) and jarak_kanan <= (robot.targetJarakKanan + 1):
                gerak.stop(robot)
                robot.motor.relay_tambahan2 = 1
                if (now - robot.state.rakit_transition_start > 0.2):
                    robot.motor.relay_tambahan1 = 1
                if (now - robot.state.rakit_transition_start > 0.8):
                    print(f"[SENJATA] Posisi lateral pas ({robot.targetJarakKanan}cm). Mengaktifkan relay tambahan...")
                    self.transition_to("MUNDUR_PELAN", now, robot, gerak)
        
            else:
                # --- LOGIKA FILTER JARAK HANTU ---
                # Jika target di atas 40 cm, dan sensor membaca angka 21 hingga 28, abaikan!
                if robot.targetJarakKanan > 40 and 21 <= jarak_kanan <= 28:
                    pass # 'pass' berarti sistem tidak melakukan apa-apa dan langsung lanjut ke looping berikutnya
                
                # Jika angka sensor aman (bukan 21-28), jalankan gerakan normal
                else:
                    gerak.geser_ke_titik_kanan(robot, robot.targetJarakKanan)
                    robot.state.rakit_transition_start = now
            # if jarak_kanan <= 30:
            #     gerak.stop(robot)

        elif robot.state.rakit_state == "MUNDUR_PELAN":
            gerak.base_speed = 20 # Jauh lebih pelan
            gerak.max_pwm = 25
            if jarak_belakang <= target_jarak + 1: # target 2 cm
                gerak.stop(robot)
                
                if (now - robot.state.rakit_transition_start > 0.1):
                    print("[SENJATA] Tiba di posisi sangat dekat (2cm).")
                    self.transition_to("RELAY_MATI_1", now, robot, gerak)
            else:
                gerak.mundur_ke_titik(robot, target_jarak)
                robot.state.rakit_transition_start = now

        elif robot.state.rakit_state == "RELAY_MATI_1":
            robot.motor.relay_tambahan2 = 0
            # Jeda 1.5s sebelum pindah ke step matikan relay 2
            if (now - robot.state.rakit_transition_start > 0.5):
                robot.motor.relay_tambahan1 = 0
            if (now - robot.state.rakit_transition_start > 1):
                self.transition_to("RELAY_MATI_2", now, robot, gerak)

        elif robot.state.rakit_state == "RELAY_MATI_2":
            # Jeda 3s sebelum lanjut ke MAJU_30CM
            if (now - robot.state.rakit_transition_start >= 1.0):
                self.transition_to("MAJU_30CM", now, robot, gerak)

        elif robot.state.rakit_state == "MAJU_30CM":
            gerak.base_speed = 120
            gerak.max_pwm = 255
            
            
            if jarak_belakang >= 51 and jarak_belakang <= 53: # target 30 cm (52cm sensor belakang)
                gerak.stop(robot)
                if (now - robot.state.rakit_transition_start > 0.1):
                    print("[SENJATA] Tiba di posisi 30cm.")
                    gerak.target_angle = -90
                    self.transition_to("PUTAR_NEG_90", now, robot, gerak)
            elif (jarak_belakang == -1):
                gerak.maju(robot)
                robot.state.rakit_transition_start = now
            else:
                gerak.mundur_ke_titik(robot, 52)
                robot.state.rakit_transition_start = now

        elif robot.state.rakit_state == "PUTAR_NEG_90":
            gerak.base_speed = 150
            gerak.max_pwm = 180
            gerak.hadap_sudut(robot)
            if (robot.sensor.kompas >= -92 and robot.sensor.kompas <= -88): # -90 derajat ± 2
                if (now - robot.state.rakit_transition_start > 0.1):
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
            if (robot.sensor.kompas >= -2 and robot.sensor.kompas <= 2):
                # self.transition_to("BALIK_KE_POSISI", now, robot, gerak)
                if (now - robot.state.rakit_transition_start > 0.5):
                    self.transition_to("BALIK_KE_POSISI", now, robot, gerak)
            else:
                robot.state.rakit_transition_start = now
                pass
        
        elif robot.state.rakit_state == "BALIK_KE_POSISI":
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