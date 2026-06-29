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
            gerak.max_pwm = 100
            gerak.base_speed = 80
            gerak.maju(robot)
            if (jarak_depan < 100 and jarak_depan >0):
                self.transition_ke_tengah("MAJU", now, robot, gerak, stop=False)

        elif robot.state.naikturun_sub_state == "MAJU":
            gerak.max_pwm = 70
            gerak.base_speed = 50
            if gerak.maju_ke_titik(robot, 30, now):
                gerak.stop(robot)
                self.transition_ke_tengah("SAMPING", now, robot, gerak, stop=False)
            
        elif robot.state.naikturun_sub_state == "SAMPING":
            if gerak.geser_ke_titik_kanan(robot, 268, now):
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
            
            if(jarak_depan < 25):
                self.transition_naik("N2", now, robot, gerak, stop=False)
                
        elif robot.state.naikturun_sub_state1 == "N2":
            
            gerak.naikTurunBiasa(robot, 14)
            if bawah_tengah > 20:
                robot.motor.mDorong1 = robot.motor.mDorong2 = 0
                self.transition_naik("N3", now, robot, gerak, stop=False)
            
        elif robot.state.naikturun_sub_state1 == "N3":
            
            if(jarak_depan < 116 and jarak_depan >105):
                self.transition_naik("N4", now, robot, gerak, stop=False)
            
        elif robot.state.naikturun_sub_state1 == "N4":
            robot.motor.mDorong2 = 255 # DEPAN
            gerak.base_speed  = 140
            gerak.max_pwm = 155
            gerak.maju(robot)
            if(jarak_depan < 68 and jarak_depan > 60):
                self.transition_naik("N5", now, robot, gerak, stop=False)
            
        elif robot.state.naikturun_sub_state1 == "N5":
            robot.motor.mDorong1 = 255 # DEPAN
            if bawah_belakang > 20:
                self.transition_naik("N6", now, robot, gerak, stop=False)
        elif robot.state.naikturun_sub_state1 == "N6":
            robot.motor.mDorong2 = -155
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
            gerak.turun_ke_titk(robot, 10)
            gerak.stop

            

            



            
                
            

        
                
        elif robot.state.naikturun_sub_state1 == "PASKANHARIZONTAL":
            gerak.base_speed = gerak.max_pwm = 30
            if gerak.geser_ke_titik_kanan(robot, 250, now):
                self.transition_naik("PERISAPAN", now, robot, gerak)
                return True

        return False
                
    
    
    
    
    # ==============================================================
    # FUNGSI 3: GERAKAN TURUN
    # ==============================================================
    
    