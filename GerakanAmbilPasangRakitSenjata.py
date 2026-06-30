import time
# Pastikan Anda mengimpor GerakanDasar jika diperlukan di file ini
# from GerakanDasar import GerakanDasar

class RakitSenjata:
    def __init__(self):
        # HAPUS semua inisialisasi state di sini karena sudah pindah ke robot_data.py
        self.UjungTombak = "ada"

    def transition_to(self, target_state, now, robot, gerak):
        gerak.stop(robot)
        robot.state.rakit_state = "TRANSISI"
        robot.state.rakit_next_state = target_state
        robot.state.rakit_transition_start = now

    
    def jalankan(self, robot, gerak, now):
        jarak_belakang  = robot.sensor.ultrasonic_belakang
        jarak_kanan     = robot.sensor.ultrasonic_kanan
        jarak_bawah_tengah = robot.sensor.ultrasonic_bawah_tengah
        target_jarak = 26

        # ---------------------------------------------------------
        # STATE MACHINE MENGGUNAKAN IF-ELIF
        # ---------------------------------------------------------
        if robot.state.rakit_state == "TRANSISI":
            gerak.stop(robot)
            jeda_transisi = robot.config.data.get("umum", {}).get("jeda_transisi_default", 0.01)
            if (now - robot.state.rakit_transition_start > jeda_transisi): # Jeda transisi 0.1 detik
                robot.state.rakit_state = robot.state.rakit_next_state
                robot.state.rakit_transition_start = now
                print(f"[SENJATA] Masuk ke state: {robot.state.rakit_state}")

        elif robot.state.rakit_state == "IDLE":
            robot.state.rakit_start_time = now # TAHAN TIMER DI SINI
            robot.state.rakit_transition_start = now
            if gerak.turun_ke_titk(robot, 5):
                gerak.stop(robot)
                self.transition_to("PERSIAPAN", now, robot, gerak)
        

        elif robot.state.rakit_state == "PERSIAPAN":
            gerak.turun_ke_titk(robot, robot.config.data.get("umum", {}).get("Tinggi"), tun="off")
            gerak.maju_diagonal_kiri(robot)
            if (jarak_belakang >= 35):
                self.transition_to("PUTAR1", now, robot, gerak)
                gerak.target_angle = robot.config.data.get("rakit_senjata", {}).get("putar", {}).get("target_angle_1", 90)                

        elif robot.state.rakit_state == "PUTAR1":
            gerak.turun_ke_titk(robot, robot.config.data.get("umum", {}).get("Tinggi"), tun="off")
            gerak.base_speed = 80
            gerak.max_pwm = 100
            if gerak.hadap_sudut(robot, now):
                self.transition_to("GESER_KESAMPING", now, robot, gerak)
        


        elif robot.state.rakit_state == "GESER_KESAMPING":
            gerak.turun_ke_titk(robot, robot.config.data.get("umum", {}).get("Tinggi"), tun="off")
            cfg_geser = robot.config.data.get("rakit_senjata", {}).get("geser_samping", {})
            gerak.base_speed = cfg_geser.get("base_speed") # Kecepatan pelan
            gerak.max_pwm = cfg_geser.get("max_pwm")
            robot.motor.CapitTombakNaikTurun = 0
            if gerak.geser_ke_titik_kanan(robot, 65, now):
                self.transition_to("NAIK_paskan", now, robot, gerak)
        
        elif robot.state.rakit_state == "NAIK_paskan":
            robot.motor.CapitTombakJepit = 1
            # gerak.naikTurunBiasa(robot,18)
            if gerak.turun_ke_titk_no_pitch(robot, 29):
            # if jarak_bawah_tengah > 18:
                # hitung delay 0.1 detik
                if (now - robot.state.rakit_transition_start > 0.1):
                    self.transition_to("MULAI_JEPIT", now, robot, gerak)
                

        elif robot.state.rakit_state == "MULAI_JEPIT":
            cfg_jepit = robot.config.data.get("rakit_senjata", {}).get("mulai_jepit", {})
            gerak.base_speed = cfg_jepit.get("base_speed", 20) # Jauh lebih pelan
            gerak.max_pwm = cfg_jepit.get("max_pwm", 30)
            robot.motor.CapitTombakNaikTurun = 1
            if gerak.mundur_ke_titik(robot, 4, now):
                gerak.stop(robot)                
                self.transition_to("JEPIT", now, robot, gerak)

        elif robot.state.rakit_state == "JEPIT":
            if (now - robot.state.rakit_transition_start > 0.01):
                robot.motor.CapitTombakJepit = 0
            if (now - robot.state.rakit_transition_start > 1.5):
                robot.motor.CapitTombakNaikTurun = 0
                self.transition_to("RELAY_MATI_2", now, robot, gerak)

        elif robot.state.rakit_state == "RELAY_MATI_2":
            if (now - robot.state.rakit_transition_start >= 2.0):
                self.transition_to("MAJU_30CM", now, robot, gerak)

        elif robot.state.rakit_state == "MAJU_30CM":
            gerak.base_speed = 80
            gerak.max_pwm = 100
            
            if jarak_belakang >= 20: # target 30 cm (52cm sensor belakang)
                gerak.stop(robot)
                if (now - robot.state.rakit_transition_start > 0.1):
                    print("[SENJATA] Tiba di posisi 30cm.")
                    gerak.target_angle = robot.config.data.get("rakit_senjata", {}).get("putar", {}).get("target_angle_2", -90)
                    self.transition_to("PUTAR_NEG_90", now, robot, gerak)
            else:
                if robot.targetJarakKanan <= 35:
                    gerak.maju_diagonal_kiri(robot)
                else:
                    gerak.mundur_ke_titik(robot, 20, now)
                robot.state.rakit_transition_start = now

        elif robot.state.rakit_state == "PUTAR_NEG_90":
            gerak.base_speed = 110
            gerak.max_pwm = 120
           
            if  gerak.hadap_sudut(robot, now):
                self.transition_to("DELAY_1", now, robot, gerak)

        elif robot.state.rakit_state == "DELAY_1":
            gerak.stop(robot)
            self.transition_to("BUKA_PEGANGAN", now, robot, gerak)
        
        elif robot.state.rakit_state == "BUKA_PEGANGAN":
            if (robot.sensor.data_qr ==  "Qr Ditemukan"):
                robot.motor.CapitTombakJepit = 1
                self.transition_to("DELAYBENTAR", now, robot, gerak)
                gerak.target_angle = 0
            else:
                pass
            
        
        elif robot.state.rakit_state == "DELAYBENTAR":
            gerak.stop(robot)
            if (now - robot.state.rakit_transition_start > 2.0 ):
                self.transition_to("BALIKKEPIT", now, robot, gerak)
        
        elif robot.state.rakit_state == "BALIKKEPIT":
            if gerak.baliKePosisiAwal(robot):
                self.transition_to("FINISHED", now, robot, gerak)
            
            

        elif robot.state.rakit_state == "FINISHED":
            robot.state.rakit_is_done = True
            gerak.stop(robot)
            return True

        return False