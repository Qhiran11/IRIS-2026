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
        jarak_kiri = robot.sensor.ultrasonic_kiri
        jarak_depan = robot.sensor.ultrasonic_depan
        # Penanganan Transisi
        if robot.state.naikturun_sub_state == "TRANSISI":
            gerak.stop(robot)
            if (now - robot.state.naikturun_transition_start > 0.01): # Jeda transisi 0.01 detik
                robot.state.naikturun_sub_state = robot.state.naikturun_next_state
                robot.state.naikturun_transition_start = now
                print(f"[NAIK-TURUN TENGAH] Masuk ke state: {robot.state.naikturun_sub_state}")
                
        elif robot.state.naikturun_sub_state == "SIAP":
            gerak.max_pwm = 140
            gerak.base_speed = 120
            gerak.maju(robot)
            if (jarak_depan < 100):
                self.transition_ke_tengah("MAJU", now, robot, gerak, stop=False)

        elif robot.state.naikturun_sub_state == "MAJU":
            if gerak.maju_ke_titik(robot, 30, now):
                gerak.stop(robot)
                self.transition_ke_tengah("SAMPING", now, robot, gerak, stop=False)
            
        elif robot.state.naikturun_sub_state == "SAMPING":
            gerak.max_pwm = 120
            gerak.base_speed = 100
            if gerak.geser_ke_titik_kiri(robot, 250, now):
                self.transition_ke_tengah("PASKAN", now, robot, gerak, stop=False)

        elif robot.state.naikturun_sub_state == "PASKAN":
            gerak.max_pwm = 30
            gerak.base_speed = 30
            if gerak.maju_ke_titik(robot, 3, now) or jarak_depan <= 0:
                gerak.max_pwm = 60
                gerak.base_speed = 60
                self.transition_ke_tengah("FINISH", now, robot, gerak, stop=False)
                return True 

        return False

    # ==============================================================
    # FUNGSI 2: GERAKAN NAIK
    # ==============================================================
    def _proses_naik(self, robot, gerak):
        now = time.time()
        jarak_depan = robot.sensor.ultrasonic_depan
        proxi_belakang = robot.sensor.proxi_belakang

        # Penanganan Transisi
        if robot.state.naikturun_sub_state1 == "TRANSISI":
            gerak.stop(robot)
            if (now - robot.state.naikturun_transition_start1 > 0.01):
                robot.state.naikturun_sub_state1 = robot.state.naikturun_next_state1
                robot.state.naikturun_transition_start1 = now
                print(f"[NAIK-TURUN NAIK] Masuk ke state: {robot.state.naikturun_sub_state1}")
        
        elif robot.state.naikturun_sub_state1 == "PERISAPAN":
            gerak.base_speed  = 20
            gerak.max_pwm = 30
            self.transition_naik("MAJU", now, robot, gerak, stop=False)

        elif robot.state.naikturun_sub_state1 == "MAJU":
            if gerak.maju_ke_titik(robot, 4, now) or jarak_depan == 0:
                self.transition_naik("NAIK", now, robot, gerak, stop=False)

        elif robot.state.naikturun_sub_state1 == "NAIK":
            gerak.naik(robot)
            if (now - robot.state.naikturun_transition_start1 > 3.0):
                self.transition_naik("MAJU2", now, robot, gerak)
        
        elif robot.state.naikturun_sub_state1 == "MAJU2":
            gerak.maju_roda_2(robot)
            if (proxi_belakang == 0):
                gerak.stop_roda_2(robot)
                self.transition_naik("BODY2NAIK", now, robot, gerak)


        elif robot.state.naikturun_sub_state1 == "BODY2NAIK":
            gerak.turun(robot)
            if (now - robot.state.naikturun_transition_start1 > 3.0):
                self.transition_naik("PASKANTENGAH", now, robot, gerak)
        
        elif robot.state.naikturun_sub_state1 == "PASKANTENGAH":
            if gerak.maju_ke_titik(robot, 27, now):
                self.transition_naik("PASKANHARIZONTAL", now, robot, gerak)
                
        elif robot.state.naikturun_sub_state1 == "PASKANHARIZONTAL":
            if gerak.geser_ke_titik_kiri(robot, 24, now):
                self.transition_naik("PERISAPAN", now, robot, gerak)
                return True

        return False
                
    
    
    
    
    # ==============================================================
    # FUNGSI 3: GERAKAN TURUN
    # ==============================================================
    def _proses_turun(self, robot, gerak):
        now = time.time()
        jarak_depan = robot.sensor.ultrasonic_depan

        # Penanganan Transisi
        if robot.state.naikturun_sub_state2 == "TRANSISI":
            gerak.stop(robot)
            if (now - robot.state.naikturun_transition_start2 > 0.01):
                robot.state.naikturun_sub_state2 = robot.state.naikturun_next_state2
                robot.state.naikturun_transition_start2 = now
                print(f"[NAIK-TURUN TURUN] Masuk ke state: {robot.state.naikturun_sub_state2}")
        
        elif robot.state.naikturun_sub_state2 == "PERISAPAN":
            gerak.base_speed = gerak.max_pwm = 20
            self.transition_turun("MUNDUR", now, robot, gerak, stop=False)

        elif robot.state.naikturun_sub_state2 == "MUNDUR":
            if (robot.sensor.proxi_belakang == 1):
                self.transition_turun("BODY2TURUN", now, robot, gerak)
            else:
                gerak.mundur(robot)
            
        elif robot.state.naikturun_sub_state2 == "BODY2TURUN":
            gerak.naik(robot)
            if (now - robot.state.naikturun_transition_start2 > 3.0):
                self.transition_turun("MUNDUR2", now, robot, gerak)
                    
        elif robot.state.naikturun_sub_state2 == "MUNDUR2":
            gerak.mundur_roda_2(robot)
            if (robot.sensor.proxi_depan == 1):
                gerak.stop_roda_2(robot)
                self.transition_turun("TURUN", now, robot, gerak)
                
        elif robot.state.naikturun_sub_state2 == "TURUN":
            gerak.turun(robot)
            if (now - robot.state.naikturun_transition_start2 > 2.0):
                self.transition_turun("MUNDURPASKAN", now, robot, gerak)

        elif robot.state.naikturun_sub_state2 == "MUNDURPASKAN":
            gerak.base_speed = gerak.max_pwm = 50
            gerak.mundur(robot)
            if (jarak_depan > 15 ):
                self.transition_turun("PERISAPAN", now, robot, gerak)
                return True

        return False


    def _proses_naik2(self, robot, gerak):
        now = time.time()
        jarak_depan = robot.sensor.ultrasonic_depan
        jarak_belakang = robot.sensor.ultrasonic_belakang
        proximity_belakang = robot.sensor.proxi_belakang

        # Penanganan Transisi
        if robot.state.naikturun_sub_state1 == "TRANSISI":
            gerak.stop(robot)
            if (now - robot.state.naikturun_transition_start1 > 0.01):
                robot.state.naikturun_sub_state1 = robot.state.naikturun_next_state1
                robot.state.naikturun_transition_start1 = now
                print(f"[NAIK-TURUN NAIK] Masuk ke state: {robot.state.naikturun_sub_state1}")
        
        elif robot.state.naikturun_sub_state1 == "PERISAPAN":
            gerak.base_speed  = 20
            gerak.max_pwm = 30
            self.transition_naik("MAJU", now, robot, gerak, stop=False)

        elif robot.state.naikturun_sub_state1 == "MAJU":
            if gerak.maju_ke_titik(robot, 4, now) or jarak_depan == 0:
                self.transition_naik("NAIK", now, robot, gerak, stop=False)

        elif robot.state.naikturun_sub_state1 == "NAIK":
            gerak.naik(robot)
            if (now - robot.state.naikturun_transition_start1 > 4.0):
                self.transition_naik("MAJU2", now, robot, gerak)
        
        elif robot.state.naikturun_sub_state1 == "MAJU2":
            gerak.maju_roda_2(robot)
            if (proximity_belakang == 0):
                gerak.stop_roda_2(robot)
                self.transition_naik("BODY2NAIK", now, robot, gerak)


        elif robot.state.naikturun_sub_state1 == "BODY2NAIK":
            gerak.turun(robot)
            if (now - robot.state.naikturun_transition_start1 > 3.0):
                self.transition_naik("DELAYMAJU", now, robot, gerak)
        
        elif robot.state.naikturun_sub_state1 == "DELAYMAJU":
            gerak.maju(robot)
            if (now - robot.state.naikturun_transition_start1 > 0.1):
                self.transition_naik("PASKANHARIZONTAL", now, robot, gerak)
                
        elif robot.state.naikturun_sub_state1 == "PASKANHARIZONTAL":
            gerak.stop(robot)
            self.transition_naik("PERISAPAN", now, robot, gerak)
            return True

        return False
                
    