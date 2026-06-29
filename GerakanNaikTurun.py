import time
# Pastikan MappingHutan sudah di-import sesuai struktur kodemu
from MappingHutan import MappingHutan

class GerakanNaikTurun:
    def __init__(self):
        self.Hutan = MappingHutan()

    # ==============================================================
    # FUNGSI TRANSISI STATE
    # ==============================================================
    def transition_ke_tengah(self, target_state, now, robot, gerak, stop=True):
        if stop:
            gerak.stop(robot)
        robot.state.naikturun_sub_state = "TRANSISI"
        robot.state.naikturun_next_state = target_state
        robot.state.naikturun_transition_start = now

    def transition_naik(self, target_state, now, robot, gerak, stop=True):
        if stop:
            gerak.stop(robot)
        robot.state.naikturun_sub_state1 = "TRANSISI"
        robot.state.naikturun_next_state1 = target_state
        robot.state.naikturun_transition_start1 = now

    def transition_turun(self, target_state, now, robot, gerak, stop=True):
        if stop:
            gerak.stop(robot)
        robot.state.naikturun_sub_state2 = "TRANSISI"
        robot.state.naikturun_next_state2 = target_state
        robot.state.naikturun_transition_start2 = now

    def _proses_ke_tengah(self, robot, gerak, now):
        jarak_kanan = robot.sensor.ultrasonic_kanan
        jarak_depan = robot.sensor.ultrasonic_depan
        # Penanganan Transisi
        if robot.state.naikturun_sub_state == "TRANSISI":
            gerak.stop(robot)
            jeda_transisi = robot.config.data.get("umum", {}).get("jeda_transisi_default", 0.01)
            if (now - robot.state.naikturun_transition_start > jeda_transisi): # Jeda transisi 0.01 detik
                robot.state.naikturun_sub_state = robot.state.naikturun_next_state
                robot.state.naikturun_transition_start = now
                print(f"[NAIK-TURUN TENGAH] Masuk ke state: {robot.state.naikturun_sub_state}")
                
        elif robot.state.naikturun_sub_state == "SIAP":
            cfg_tengah = robot.config.data.get("gerakan_naikturun", {}).get("tengah", {})
            gerak.max_pwm = 200
            gerak.base_speed = 255
            gerak.maju_diagonal_kanan(robot)
            if (jarak_depan < 100 and jarak_depan >0):
                self.transition_ke_tengah("MAJU", now, robot, gerak, stop=False)

        elif robot.state.naikturun_sub_state == "MAJU":
            gerak.max_pwm = 50
            gerak.base_speed = 40
            if gerak.maju_ke_titik(robot, 30, now):
                gerak.stop(robot)
                self.transition_ke_tengah("SAMPING", now, robot, gerak, stop=False)
            
        elif robot.state.naikturun_sub_state == "SAMPING":
            gerak.base_speed = 30
            gerak.max_pwm = 45
            if gerak.geser_ke_titik_kanan(robot, 275, now):
                self.transition_ke_tengah("FINISH", now, robot, gerak, stop=False)
                return True 

        return False

    # ==============================================================
    # FUNGSI 2: GERAKAN NAIK
    # ==============================================================
    def _proses_naik(self, robot, gerak):
        now = time.time()
        jarak_depan = robot.sensor.ultrasonic_depan
        bawah_tengah = robot.sensor.ultrasonic_bawah_tengah
        bawah_depan = robot.sensor.ultrasonic_bawah_depan
        bawah_belakang = robot.sensor.ultrasonic_bawah_belakang
        pitch = robot.sensor.pitch_kompas

        # Penanganan Transisi
        if robot.state.naikturun_sub_state1 == "TRANSISI":
            # gerak.stop(robot)
            jeda_transisi = robot.config.data.get("umum", {}).get("jeda_transisi_default", 0.01)
            if (now - robot.state.naikturun_transition_start1 > jeda_transisi):
                robot.state.naikturun_sub_state1 = robot.state.naikturun_next_state1
                robot.state.naikturun_transition_start1 = now
                print(f"[NAIK-TURUN NAIK] Masuk ke state: {robot.state.naikturun_sub_state1}")
        
        elif robot.state.naikturun_sub_state1 == "PERISAPAN":
            robot.motor.mDorong1 = 0
            robot.motor.mDorong2 = 0
            gerak.base_speed  = 30
            gerak.max_pwm = 35
            gerak.maju(robot)
            self.transition_naik("N1", now, robot, gerak, stop=False)
            

        elif robot.state.naikturun_sub_state1 == "N1":
            
            if(jarak_depan < 25 or jarak_depan > 110):
                self.transition_naik("N2", now, robot, gerak, stop=False)
                
        elif robot.state.naikturun_sub_state1 == "N2":
            
            
            if bawah_tengah > 17:
                robot.motor.mDorong1 = 0
                robot.motor.mDorong2 = 0
                self.transition_naik("N3", now, robot, gerak, stop=False)
            else:
                gerak.turun_ke_titk(robot, 20)            
        elif robot.state.naikturun_sub_state1 == "N3":
            
            if(jarak_depan < 117 and jarak_depan >105):
                self.transition_naik("N4", now, robot, gerak, stop=False)
            
        elif robot.state.naikturun_sub_state1 == "N4":
            robot.motor.mDorong2 = 255 # DEPAN
            gerak.base_speed  = 140
            gerak.max_pwm = 155
            gerak.maju(robot)
            robot.motor.m2_pwm = 0 #depan kanan
            robot.motor.m0_pwm = 0 #depan kiri

            if(jarak_depan < 68 and jarak_depan > 60):
                self.transition_naik("N5", now, robot, gerak, stop=False)
            
        elif robot.state.naikturun_sub_state1 == "N5":
            gerak.maju(robot)
            robot.motor.mDorong1 = 255 # DEPAN
            robot.motor.m3_pwm = 0 #depan kanan
            robot.motor.m1_pwm = 0 #depan kiri
            if bawah_belakang > 20:
                self.transition_naik("N6", now, robot, gerak, stop=False)
        elif robot.state.naikturun_sub_state1 == "N6":
            robot.motor.mDorong2 = -155
            gerak.maju(robot)
            if pitch > 3:
                self.transition_naik("N7", now, robot, gerak, stop=False)
        elif robot.state.naikturun_sub_state1 == "N7":
            robot.motor.mDorong1 = 0
            robot.motor.mDorong2 = 0
            gerak.base_speed = 70
            gerak.max_pwm = 80
            gerak.maju(robot)
            if bawah_belakang <10 :
                self.transition_naik("N8", now, robot, gerak, stop=True)
                
                
        elif robot.state.naikturun_sub_state1 == "N8":
            if gerak.turun_ke_titk(robot, 13):
                self.transition_naik("PASKANHARIZONTAL", now, robot, gerak, stop=True)
        
        elif robot.state.naikturun_sub_state1 == "PASKANHARIZONTAL":
            if gerak.geser_ke_titik_kiri(robot, 34, now):
                self.transition_naik("PASKANVERTIKAL", now, robot, gerak, stop=True)
        elif robot.state.naikturun_sub_state1 == "PASKANVERTIKAL":
            if gerak.maju_ke_titik(robot, 29, now):
                self.transition_naik("PERISAPAN", now, robot, gerak, stop=True)
        elif robot.state.naikturun_sub_state1 == "FINISHED":
            gerak.stop(robot)
            
        
    
    # ==============================================================
    # FUNGSI 3: GERAKAN TURUN
    # ==============================================================

    def _proses_turun(self, robot, gerak):
        now = time.time()
        jarak_depan = robot.sensor.ultrasonic_depan
        bawah_tengah = robot.sensor.ultrasonic_bawah_tengah
        bawah_depan = robot.sensor.ultrasonic_bawah_depan
        bawah_belakang = robot.sensor.ultrasonic_bawah_belakang
        pitch = robot.sensor.pitch_kompas

        # Penanganan Transisi
        if robot.state.naikturun_sub_state1 == "TRANSISI":
            # gerak.stop(robot)
            jeda_transisi = robot.config.data.get("umum", {}).get("jeda_transisi_default", 0.01)
            if (now - robot.state.naikturun_transition_start1 > jeda_transisi):
                robot.state.naikturun_sub_state1 = robot.state.naikturun_next_state1
                robot.state.naikturun_transition_start1 = now
                print(f"[NAIK-TURUN NAIK] Masuk ke state: {robot.state.naikturun_sub_state1}")
        
        elif robot.state.naikturun_sub_state1 == "PERISAPAN":
            if gerak.turun_ke_titk(robot, 3):
                self.transition_naik("T0", now, robot, gerak, stop=False)
        elif robot.state.naikturun_sub_state1 == "T0":
            robot.motor.mDorong1 = 0
            robot.motor.mDorong2 = 0
            gerak.base_speed  = 25
            gerak.max_pwm = 25
            gerak.maju(robot)
            self.transition_naik("T1", now, robot, gerak, stop=False)
            

        elif robot.state.naikturun_sub_state1 == "T1":
            if bawah_depan > 10 :
                self.transition_naik("T2", now, robot, gerak, stop=True)
        elif robot.state.naikturun_sub_state1 == "T2":
            if gerak.turun_roda1( robot):
                gerak.base_speed  = 10
                gerak.max_pwm = 10
                self.transition_naik("T3", now, robot, gerak, stop=False)
        
        elif robot.state.naikturun_sub_state1 == "T3":
            gerak.base_speed  = 25
            gerak.max_pwm = 25
            gerak.maju(robot)
            if bawah_belakang > 10:
                self.transition_naik("T4", now, robot, gerak, stop=True)
        elif robot.state.naikturun_sub_state1 == "T4":
            gerak.turun_roda2( robot)
                
    
                
            
            
            
     
    
    