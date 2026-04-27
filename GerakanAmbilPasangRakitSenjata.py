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
    def jalankan(self, robot, gerak, target_angle):
        now = time.time()

        match self.state:
            case "IDLE":
                print("[SENJATA] Memulai sequence RAKIT...")
                self.start_time = now
                self.state = "PUTAR"

                # 3. Target rotasi diset di memori robot yang aktif
                gerak.target_angle = target_angle

            case "PUTAR":
                gerak.hadap_sudut(robot)
                
                # 4. BACA kompas dari objek 'robot' yang datanya selalu FRESH
                if (robot.sensor.kompas >= (target_angle - 1) and robot.sensor.kompas <= (target_angle + 1)):
                    if (now - self.start_time > 0.1): # Delay kecil untuk memastikan stabil
                        print("[SENJATA] Menghadap 90 derajat. Mulai Mendekat...")
                        self.state = "MENDEKAT"
                        self.start_time = now
            
            case "MENDEKAT":
                gerak.mundur(robot)
                if (robot.sensor.proxi_belakang == 0):
                    print("[SENJATA] Sequence Selesai.")
                    self.state = "FINISHED"
                
            case "FINISHED":
                self.is_done = True
                gerak.stop(robot)
                return True

        return False