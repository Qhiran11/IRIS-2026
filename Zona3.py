import time


class Zona3:
    def __init__(self):
        self.state = "READY"
        self.jarak_naik_kanan = 40
        self.keceptan_naik_tanjakan = 180
        self.sudut_tanjakan = 3
        self.jarak_depan_naik = 500

        self.sudut_putar = -90
        self.jarak_depan_rak = 800
        self.paskan_ditengah = 88

        self.then = 0
        
    
    def logic_zona3(self,robot,gerak):
        now = time.time()
        match self.state:
            case "READY":
                gerak.base_speed  = 80
                gerak.max_pwm = gerak.base_speed
                self.then = now
                self.state = "KANAN"

            case "KANAN":
                if gerak.geser_ke_tengah2(robot, self.jarak_naik_kanan):
                    if (now - self.then > 1):
                        self.state = "MASUKTANJAKAN"
                        self.then = now
                else:
                    self.then = now

            
            case "MASUKTANJAKAN":
                # Panggil fungsi maju ke jarak 2cm
                if robot.sensor.kompas2 < self.sudut_tanjakan :
                    gerak.base_speed  = self.keceptan_naik_tanjakan
                    gerak.max_pwm = gerak.base_speed
                    gerak.maju(robot)

                else :
                    self.state = "TANJAKAN"
                    self.then = now
                    print (self.state)
                
            case "TANJAKAN":         
                gerak.maju(robot)   
                # Cek apakah sudah dekat tembok depan
                if robot.sensor.kompas2 < self.sudut_tanjakan: 
                    self.then = time.time()
                    gerak.base_speed  = 30
                    gerak.max_pwm = gerak.base_speed
                        
                    self.state = "STABILKAN"
                    print (self.state)

            
            case "STABILKAN":
                gerak.base_speed  = 80
                gerak.max_pwm = gerak.base_speed
                if (robot.sensor.kompas == gerak.target_angle or robot.sensor.kompas == -gerak.target_angle):
                    gerak.stop(robot)
                    
                    if time.time() - self.then > 0.1:
                        gerak.stop(robot)
                        gerak.target_angle = -90
                        STATE =  "MAJU"
                else:
                    gerak.hadap_sudut(robot)
                    self.then = time.time()
            
            case "PUTAR":
                if (robot.sensor.kompas == gerak.target_angle or robot.sensor.kompas == -gerak.target_angle):
                    gerak.stop(robot)
                    if time.time() - self.then > 0.1:
                        gerak.stop(robot)
                        self.state =  "MAJU"
                else:
                    gerak.hadap_sudut(robot)
                    self.then = time.time()
            
            case "MAJU":
                gerak.maju(robot)
                # if (robot.sensor.proxi_belakang == 0):
                #     gerak.stop(robot)
                #     self.state = "PASKAN"
                #     self.then = time.time()
                


    
            case "PASKAN":
                gerak.turun(robot, 160)
                if (now - self.then > 2):
                    gerak.stop(robot)
                    self.state = "SELESAI"
                    self.then = time.time()
 

            
            case "SELESAI":
                gerak.base_speed = gerak.max_pwm = 50
                gerak.maju(robot)
                if (robot.sensor.jarak_depan > 0 and robot.sensor.jarak_depan < 315 ):
                    gerak.stop(robot)
                    self.state = "PERISAPAN"
                    return True
                elif (robot.sensor.jarak_depan == -1 or robot.sensor.jarak_depan > 1200 ):
                    return True
                    self.state = "PERISAPAN"

        # print("jumlah Naik : ", self.jumlahNaik, " state : ", self.state)\
        return False
