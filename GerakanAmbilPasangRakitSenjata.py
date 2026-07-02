import time
# Pastikan Anda mengimpor GerakanDasar jika diperlukan di file ini
# from GerakanDasar import GerakanDasar

class RakitSenjata:
    def __init__(self):
        # HAPUS semua inisialisasi state di sini karena sudah pindah ke robot_data.py
        self.UjungTombak = "ada"
        self.ujung = 18

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
        cfg_geser = robot.config.data.get("rakit_senjata", {}).get("geser_samping",{})
        proxi = robot.sensor.proxi_belakang

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
            gerak.stop(robot)
            # self.transition_to("MULAI_JEPIT", now, robot, gerak)
            self.transition_to("PERSIAPAN", now, robot, gerak)
        

        elif robot.state.rakit_state == "PERSIAPAN":
            gerak.base_speed = 80
            gerak.max_pwm = 100
            gerak.maju_diagonal_kiri(robot)
            if (jarak_belakang >= 40):
                self.transition_to("PUTAR1", now, robot, gerak)
                gerak.target_angle = robot.config.data.get("rakit_senjata", {}).get("putar", {}).get("target_angle_1", 90)                

        elif robot.state.rakit_state == "PUTAR1":
            gerak.base_speed = 100
            gerak.max_pwm = 255
            if gerak.hadap_sudut(robot, now):
                self.transition_to("GESER_KESAMPING", now, robot, gerak)
        

        elif robot.state.rakit_state == "GESER_KESAMPING":
            
            cfg_geser = robot.config.data.get("rakit_senjata", {}).get("geser_samping", {})
            gerak.base_speed = 30
            gerak.max_pwm = 30
            robot.motor.CapitTombakNaikTurun = 0
            if gerak.geser_ke_titik_kanan(robot, cfg_geser, now):
                gerak.stop(robot)
                self.transition_to("MULAI_JEPIT", now, robot, gerak)
        
        elif robot.state.rakit_state == "GESER_KESAMPING2":
            # Pastikan cfg_geser mengembalikan nilai angka, misal 50 (bukan dictionary)
            
            
            gerak.base_speed = 30
            gerak.max_pwm = 30
            robot.motor.CapitTombakNaikTurun = 0
            
            if (cfg_geser - 1) <= jarak_kanan <= (cfg_geser + 1):
                gerak.stop(robot)
                self.transition_to("MULAI_JEPIT", now, robot, gerak)
            elif jarak_kanan < cfg_geser + 1:
                gerak.kiri(robot) 
            elif jarak_kanan > cfg_geser - 1:
                gerak.kanan(robot)
                

        elif robot.state.rakit_state == "MULAI_JEPIT":
            gerak.base_speed = 30
            gerak.max_pwm = 40
            robot.motor.CapitTombakNaikTurun = 1
            # gerak.mundur(robot)
            gerak.mundur_ke_titik(robot, 11, now)
            if jarak_belakang <= 12 or proxi == 0:
                gerak.stop(robot)                
                self.transition_to("JEPIT", now, robot, gerak)

        elif robot.state.rakit_state == "JEPIT":
            if (now - robot.state.rakit_transition_start > 0.01):
                robot.motor.CapitTombakJepit = 0
            if (now - robot.state.rakit_transition_start > 1.0):
                robot.motor.CapitTombakNaikTurun = 0
                self.transition_to("RELAY_MATI_2", now, robot, gerak)

        elif robot.state.rakit_state == "RELAY_MATI_2":
            if (now - robot.state.rakit_transition_start >= 0.5):
                self.transition_to("MAJU_30CM", now, robot, gerak)

        elif robot.state.rakit_state == "MAJU_30CM":
            gerak.base_speed = 100
            gerak.max_pwm = 250
            
            if jarak_belakang >= 30: # target 30 cm (52cm sensor belakang)
                gerak.stop(robot)
                if (now - robot.state.rakit_transition_start > 0.1):
                    print("[SENJATA] Tiba di posisi 30cm.")
                    gerak.target_angle = robot.config.data.get("rakit_senjata", {}).get("putar", {}).get("target_angle_2", -90)
                    self.transition_to("PUTAR_NEG_90", now, robot, gerak)
            else:
                if cfg_geser < 20:
                    gerak.maju_diagonal_kiri(robot)
                else:
                    gerak.mundur_ke_titik(robot, 100, now)
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