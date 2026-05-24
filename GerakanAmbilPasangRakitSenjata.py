import time
from GerakanDasar import GerakanDasar

class RakitSenjata:
    # 1. HAPUS pembuatan Robot() dan GerakanDasar() di dalam __init__
    def __init__(self):
        self.state = "IDLE"
        self.start_time = 0
        self.is_done = False

    # 2. Paksa fungsi ini untuk menerima objek 'robot' dan 'gerak' 
    # yang sedang dipakai oleh ProsesUtama.py
    def jalankan(self, robot, gerak, target_angle, target_jarak):
        now = time.time()

        match self.state:
            case "IDLE":
                print("[SENJATA] Memulai sequence RAKIT...")
                self.start_time = now
                self.state = "PERISAPAN"

            case "PERISAPAN":
                gerak.maju(robot)
                if (now - self.start_time > 0.8):
                    gerak.stop(robot)
                    self.start_time = now
                    self.state = "PUTAR1"
                    gerak.target_angle = target_angle                

            case "PUTAR1":
                gerak.hadap_sudut(robot)
                
                # 4. BACA kompas dari objek 'robot' yang datanya selalu FRESH
                if (robot.sensor.kompas >= (target_angle - 2) and robot.sensor.kompas <= (target_angle + 2)):
                    if (now - self.start_time > 0.1): # Delay kecil untuk memastikan stabil
                        print("[SENJATA] Menghadap 90 derajat. Mulai Mendekat...")
                        self.state = "MENDEKAT"
                        self.start_time = now
            
# ...
            case "MENDEKAT":
                jarak = robot.sensor.ultrasonic_belakang
                if jarak >= (target_jarak - 2) and jarak <= (target_jarak + 2): 
                    # Jika perlu, pastikan juga posisinya sudah stabil selama beberapa detik
                    gerak.stop(robot)
                    if (now - self.start_time > 0.1): 
                        print("[SENJATA] Tiba di posisi rakit (10cm).")
                        self.state = "STOP"
                        self.start_time = now
                elif(jarak == -1) : 
                    gerak.mundur(robot)
                else:
                    gerak.mundur_ke_titik(robot, target_jarak)

            case "STOP":
                gerak.stop(robot)
                if (now - self.start_time > 3): # Delay kecil untuk memastikan stabil
                    self.state = "MAJU"
                    self.start_time = now

        
            case "MAJU":
                gerak.maju(robot) 
                jarak = robot.sensor.ultrasonic_belakang
                if (jarak >= 31 ): 
                    # Jika perlu, pastikan juga posisinya sudah stabil selama beberapa detik
                    if (now - self.start_time > 0.2): 
                        print("[SENJATA] Tiba di posisi rakit (10cm).")
                        self.state = "PUTAR2"
                        gerak.target_angle = 0
                        self.start_time = now
                        gerak.base_speed = gerak.max_pwm = 70


            case "PUTAR2":
                gerak.hadap_sudut(robot) 
                if (robot.sensor.kompas >= (gerak.target_angle - 1) and robot.sensor.kompas <= (gerak.target_angle + 1)): 
                    if (now - self.start_time > 1):
                        self.start_time = now
                        print("[SENJATA] Kembali menghadap 0 derajat.")
                        self.state = "FINISHED"
            
# ...
                
            case "FINISHED":
                self.is_done = True
                gerak.stop(robot)
                return True

        return False