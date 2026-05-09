import time


class GerakanNaikTurun:
    def __init__(self):
        self.state = "IDLE"
        self.sub_state = "SERONG" # Untuk mengatur langkah di dalam fungsi tertentu
        self.sub_state1 = "PERISAPAN"
        self.sub_state2 = "PERISAPAN"
        self.start_time = 0
        self.is_done = False
        self.then = time.time()
        self.jumlahNaik = 0

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
                
                if (robot.sensor.jarak_depan != -1 and robot.sensor.jarak_depan < 550):
                    gerak.stop(robot)
                    self.sub_state = "SAMPING"
                    self.start_time = now
            
            case "SAMPING":
                # Panggil fungsi maju ke jarak 2cm
                gerak.kanan(robot)
                
                # Cek apakah sudah dekat tembok depan
                if now - self.start_time > 0.6: 
                    self.sub_state = "PASKAN"
                    self.start_time = now
            
            case "PASKAN":
                gerak.base_speed = gerak.max_pwm = 50
                if gerak.geser_ke_tengah2(robot, 255): 
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
        
        match self.sub_state1:
            case "PERISAPAN":
                gerak.base_speed  = 30
                gerak.max_pwm = gerak.base_speed
                self.sub_state1 = "MAJU"

            case "MAJU":
                if (robot.sensor.jarak_depan <= 100):
                    gerak.stop(robot)
                    self.then = time.time()
                    self.sub_state1 = "PASKAN"

                # elif (robot.sensor.jarak_depan > 50 and robot.sensor.jarak_depan < 200):
                #     gerak.base_speed = 30
                #     gerak.max_pwm = gerak.base_speed
                #     gerak.maju(robot)
                else:
                    gerak.maju(robot)
            
            case "PASKAN":
                # Panggil fungsi maju ke jarak 2cm
                gerak.hadap_sudut(robot)
                
                # Cek apakah sudah dekat tembok depan
                if robot.sensor.kompas == gerak.target_angle : 
                    gerak.stop(robot)
                    self.then = time.time()
                    time.sleep(0.3)
                    self.sub_state1 = "NAIK"
            
            case "NAIK":
                gerak.naik(robot)
                if (now - self.then > 2.0):
                    gerak.stop(robot)
                    
                    self.sub_state1 = "MAJU2"
                    self.then = time.time()
            
            case "MAJU2":
                gerak.maju_roda_2(robot)
                if (robot.sensor.proxi_belakang == 0):
                    gerak.stop(robot)
                    self.sub_state1 = "BODY2NAIK"
                    self.then = time.time()
                


    
            case "BODY2NAIK":
                gerak.turun(robot, 160)
                if (now - self.then > 2):
                    gerak.stop(robot)
                    self.sub_state1 = "MAJUPASKAN"
                    self.then = time.time()
 

            
            case "MAJUPASKAN":
               
                gerak.base_speed = gerak.max_pwm = 50
                gerak.maju(robot)
                if (robot.sensor.jarak_depan > 0 and robot.sensor.jarak_depan < 315 ):
                    gerak.stop(robot)
                    self.sub_state1 = "PERISAPAN"
                    return True
                elif (robot.sensor.jarak_depan == -1 or robot.sensor.jarak_depan > 1200 ):
                    return True
                    self.sub_state1 = "PERISAPAN"

        
                
                        

            case "TENGAHPASKAN":
                gerak.base_speed = gerak.max_pwm = 50
                if gerak.geser_ke_tengah2(robot, 22):
                    gerak.stop(robot)
                    self.jumlahNaik = self.jumlahNaik + 1 


        # print("jumlah Naik : ", self.jumlahNaik, " sub_state1 : ", self.sub_state1)\
        return False
        
        
                
    # ==============================================================
    # FUNGSI 3: GERAKAN TURUN
    # ==============================================================
    def _proses_turun(self, robot, gerak):
        now = time.time()
        
        match self.sub_state2:
            case "PERISAPAN":
                gerak.base_speed = gerak.max_pwm = 20
                self.sub_state2 = "MUNDUR"
                # self.sub_state2 = "BODY2TURUN"
                self.then = now

            case "MUNDUR":
                if (robot.sensor.proxi_belakang == 1):
                    gerak.stop(robot)
                    self.then = time.time()
                    
                    self.sub_state2 = "PASKAN"
                else:
                    gerak.mundur(robot)
            
            case "PASKAN":
                # Panggil fungsi maju ke jarak 2cm
                gerak.hadap_sudut(robot)
                
                # Cek apakah sudah dekat tembok depan
                if robot.sensor.kompas == gerak.target_angle : 
                    gerak.stop(robot)
                    self.sub_state2 = "BODY2TURUN"
                    robot.motor.pwLogic = 1
                    self.then = time.time()
            
            case "BODY2TURUN":
                if (now - self.then > 1.8):
                    gerak.stop(robot)
                    self.sub_state2 = "MUNDUR2"
                    self.then = time.time()
                elif (now - self.then > 0.3):
                    robot.motor.pwLogic = 0
                    gerak.naik(robot, -160)
                else:
                    robot.motor.pwLogic = 1
                    gerak.naik(robot, -160)
                    
            
            case "MUNDUR2":
                gerak.mundur_roda_2(robot)
                if (robot.sensor.proxi_depan == 1):
                    gerak.stop(robot)
                    self.sub_state2 = "TURUN"
                    self.then = time.time()
                


    
            case "TURUN":
                gerak.turun(robot, 160)
                if (now - self.then > 2.0):
                    gerak.stop(robot)
                    self.sub_state2 = "MUNDURPASKAN"
                    self.then = time.time()
 

            
            case "MUNDURPASKAN":
               
                gerak.base_speed = gerak.max_pwm = 50
                gerak.mundur(robot)
                if (robot.sensor.jarak_depan > 215 ):
                    gerak.stop(robot)
                    self.sub_state2 = "PERISAPAN"
                    return True
                elif (robot.sensor.jarak_depan == -1 or robot.sensor.jarak_depan > 1200 ):
                    gerak.stop(robot)
                    return True
                    self.sub_state2 = "PERISAPAN"

        # print("jumlah Naik : ", self.jumlahNaik, " sub_state1 : ", self.sub_state1)\
        return False
      

    # ==============================================================
    # FUNGSI UTAMA ("MANDOR") YANG DIPANGGIL DI PROSES UTAMA
    # =============================================================