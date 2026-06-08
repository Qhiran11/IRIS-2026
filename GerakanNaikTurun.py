import time
from MappingHutan import MappingHutan


class GerakanNaikTurun:
    def __init__(self):
        self.Hutan = MappingHutan()

    # ==============================================================
    # FUNGSI 1: GERAK KE TENGAH DAN MAJU
    # ==============================================================
    def _proses_ke_tengah(self, robot, gerak):

        now = time.time()
        
        if robot.state.naikturun_sub_state == "SIAP":
            gerak.base_speed = gerak.max_pwm = 140
            gerak.maju_diagonal_kanan(robot)
            robot.state.naikturun_start_time = now
            robot.state.naikturun_sub_state = "SERONG"
            
        elif robot.state.naikturun_sub_state == "SERONG":
            gerak.base_speed = gerak.max_pwm = 140
            gerak.maju_diagonal_kanan(robot)
            if (now - robot.state.naikturun_start_time > 1.5):                    
                if (robot.sensor.jarak_depan > 0 and robot.sensor.jarak_depan < 500):
                    gerak.stop(robot)
                    robot.state.naikturun_sub_state = "SAMPING"
                    robot.state.naikturun_start_time = now
            
        elif robot.state.naikturun_sub_state == "SAMPING":
            # Panggil fungsi maju ke jarak 2cm
            gerak.kanan(robot)
            
            # Cek apakah sudah dekat tembok depan
            if now - robot.state.naikturun_start_time > 0.6: 
                robot.state.naikturun_sub_state = "PASKAN"
                robot.state.naikturun_start_time = now
            
        elif robot.state.naikturun_sub_state == "PASKAN":
            gerak.base_speed = gerak.max_pwm = 50
            if gerak.geser_ke_tengah2(robot, 265): 
                print("[NAIK-TURUN] Posisi Pas. Siap Naik.")
                return True # Mengembalikan True jika tugas selesai

            # elif robot.sensor.ultrasonic_kanan < 220:
            #     gerak.kanan(robot)
        return False # Masih dalam proses, kembalikan False

    # ==============================================================
    # FUNGSI 2: GERAKAN NAIK
    # ==============================================================
    def _proses_naik(self, robot, gerak):
        now = time.time()
        
        if robot.state.naikturun_sub_state1 == "PERISAPAN":
            gerak.base_speed  = 30
            gerak.max_pwm = gerak.base_speed
            robot.state.naikturun_sub_state1 = "MAJU"

        elif robot.state.naikturun_sub_state1 == "MAJU":
            if (robot.sensor.jarak_depan <= 100):
                gerak.stop(robot)
                robot.state.naikturun_then = time.time()
                robot.state.naikturun_sub_state1 = "PASKAN"

            # elif (robot.sensor.jarak_depan > 50 and robot.sensor.jarak_depan < 200):
            #     gerak.base_speed = 30
            #     gerak.max_pwm = gerak.base_speed
            #     gerak.maju(robot)
            else:
                gerak.maju(robot)
            
        elif robot.state.naikturun_sub_state1 == "PASKAN":
            # Panggil fungsi maju ke jarak 2cm
            gerak.hadap_sudut(robot)
            
            # Cek apakah sudah dekat tembok depan
            if robot.sensor.kompas == gerak.target_angle : 
                gerak.stop(robot)
                robot.state.naikturun_then = time.time()
                time.sleep(0.3)
                robot.state.naikturun_sub_state1 = "NAIK"
            
        elif robot.state.naikturun_sub_state1 == "NAIK":
            gerak.naik(robot)
            if (now - robot.state.naikturun_then > 2.0):
                gerak.stop(robot)
                
                robot.state.naikturun_sub_state1 = "MAJU2"
                robot.state.naikturun_then = time.time()
            
        elif robot.state.naikturun_sub_state1 == "MAJU2":
            gerak.maju_roda_2(robot)
            if (robot.sensor.proxi_belakang == 0):
                gerak.stop(robot)
                robot.state.naikturun_sub_state1 = "BODY2NAIK"
                robot.state.naikturun_then = time.time()
                
        elif robot.state.naikturun_sub_state1 == "BODY2NAIK":
            gerak.turun(robot, 160)
            if (now - robot.state.naikturun_then > 2):
                gerak.stop(robot)
                robot.state.naikturun_sub_state1 = "TENGAHPASKAN"
                robot.state.naikturun_then = time.time()

        elif robot.state.naikturun_sub_state1 == "TENGAHPASKAN":
            gerak.base_speed = gerak.max_pwm = 30

            if (self.Hutan.index_rute + 1) in [1, 3, 5, 8]:
            # if (robot.sensor.ultrasonic_kiri == 0 or robot.sensor.ultrasonic_kiri > 30 or robot.sensor.ultrasonic_kanan > 30  or robot.sensor.ultrasonic_kanan == 0):
                gerak.stop(robot)          
                robot.state.naikturun_sub_state1 = "MAJUPASKAN"
                robot.state.naikturun_then = time.time()
            else:
                if gerak.geser_ke_tengah2(robot, 22):
                    gerak.stop(robot)          
                    robot.state.naikturun_sub_state1 = "MAJUPASKAN"
                    robot.state.naikturun_then = time.time()

        elif robot.state.naikturun_sub_state1 == "MAJUPASKAN":
            if robot.sensor.jarak_depan > 800 or robot.sensor.jarak_depan <= 0:
                gerak.maju(robot)
                if (now - robot.state.naikturun_then > 1):
                    gerak.stop(robot)
                    robot.state.naikturun_sub_state1 = "PERISAPAN"
                    return True
            else:
                if gerak.maju_ke_titik(robot, 350):
                    gerak.stop(robot)
                    robot.state.naikturun_sub_state1 = "PERISAPAN"
                    return True

        # print("jumlah Naik : ", self.jumlahNaik, " sub_state1 : ", robot.state.naikturun_sub_state1)\
        return False
                
    # ==============================================================
    # FUNGSI 3: GERAKAN TURUN
    # ==============================================================
    def _proses_turun(self, robot, gerak):
        now = time.time()
        
        if robot.state.naikturun_sub_state2 == "PERISAPAN":
            gerak.base_speed = gerak.max_pwm =  20
            robot.state.naikturun_sub_state2 = "MUNDUR"
            # robot.state.naikturun_sub_state2 = "BODY2TURUN"
            robot.state.naikturun_then = now

        elif robot.state.naikturun_sub_state2 == "MUNDUR":
            if (robot.sensor.proxi_belakang == 1):
                gerak.stop(robot)
                robot.state.naikturun_then = time.time()
                
                robot.state.naikturun_sub_state2 = "PASKAN"
            else:
                gerak.mundur(robot)
            
        elif robot.state.naikturun_sub_state2 == "PASKAN":
            # Panggil fungsi maju ke jarak 2cm
            
            gerak.hadap_sudut(robot)
            
            # Cek apakah sudah dekat tembok depan
            if robot.sensor.kompas == gerak.target_angle : 
                gerak.stop(robot)
                robot.state.naikturun_sub_state2 = "BODY2TURUN"
                robot.motor.pwLogic = 1
                robot.state.naikturun_then = time.time()
            
        elif robot.state.naikturun_sub_state2 == "BODY2TURUN":
            if (now - robot.state.naikturun_then > 1.8):
                gerak.stop(robot)
                robot.state.naikturun_sub_state2 = "MUNDUR2"
                robot.state.naikturun_then = time.time()
            elif (now - robot.state.naikturun_then > 0.3):
                robot.motor.pwLogic = 0
                gerak.naik(robot, -160)
            else:
                robot.motor.pwLogic = 1
                gerak.naik(robot, -160)
                    
            
        elif robot.state.naikturun_sub_state2 == "MUNDUR2":
            gerak.mundur_roda_2(robot)
            if (robot.sensor.proxi_depan == 1):
                gerak.stop(robot)
                robot.state.naikturun_sub_state2 = "TURUN"
                robot.state.naikturun_then = time.time()
                
        elif robot.state.naikturun_sub_state2 == "TURUN":
            gerak.turun(robot, 160)
            if (now - robot.state.naikturun_then > 2.0):
                gerak.stop(robot)
                robot.state.naikturun_sub_state2 = "MUNDURPASKAN"
                robot.state.naikturun_then = time.time()
 
        elif robot.state.naikturun_sub_state2 == "MUNDURPASKAN":
               
            gerak.base_speed = gerak.max_pwm = 50
            gerak.mundur(robot)
            if (robot.sensor.jarak_depan > 215 ):
                gerak.stop(robot)
                robot.state.naikturun_sub_state2 = "PERISAPAN"
                return True
            elif (robot.sensor.jarak_depan == -1 or robot.sensor.jarak_depan > 1200 ):
                gerak.stop(robot)
                return True
                # Catatan: Baris di bawah ini tidak akan pernah tereksekusi karena ada return True di atasnya.
                # Namun tetap saya biarkan seperti aslinanya.
                robot.state.naikturun_sub_state2 = "PERISAPAN"

        # print("jumlah Naik : ", self.jumlahNaik, " sub_state1 : ", robot.state.naikturun_sub_state1)\
        return False