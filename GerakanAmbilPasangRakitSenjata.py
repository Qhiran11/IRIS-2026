import time
from GerakanDasar import GerakanDasar

class RakitSenjata:
    def __init__(self):
        self.state = "IDLE"
        self.start_time = 0
        self.is_done = False
        self.transition_start = 0
        self.next_state = ""
        self.targetJarakKanan = 50

    def transition_to(self, target_state, now, robot, gerak):
        """
        Melakukan transisi state dengan jeda stop selama 0.1 detik.
        """
        gerak.stop(robot)
        self.state = "TRANSISI"
        self.next_state = target_state
        self.transition_start = now

    def jalankan(self, robot, gerak, target_angle, target_jarak):
        now = time.time()

        if self.state == "TRANSISI":
            gerak.stop(robot)
            if (now - self.transition_start >= 0.1): # Jeda transisi 0.1 detik
                self.state = self.next_state
                self.start_time = now
                print(f"[SENJATA] Masuk ke state: {self.state}")

        elif self.state == "IDLE":
            print("[SENJATA] Memulai sequence RAKIT...")
            self.transition_to("PERSIAPAN", now, robot, gerak)

        elif self.state == "PERSIAPAN":
            gerak.maju(robot)
            if (now - self.start_time > 0.8):
                self.transition_to("PUTAR1", now, robot, gerak)
                gerak.target_angle = target_angle                

        elif self.state == "PUTAR1":
            gerak.hadap_sudut(robot)
            if (robot.sensor.kompas >= (target_angle - 2) and robot.sensor.kompas <= (target_angle + 2)):
                if (now - self.start_time > 0.5): # Delay stabilisasi
                    print("[SENJATA] Menghadap 90 derajat. Mulai Mendekat...")
                    self.transition_to("MENDEKAT", now, robot, gerak)
        
        elif self.state == "MENDEKAT":
            gerak.base_speed = 35 # Kecepatan pelan
            gerak.max_pwm = 45
            jarak = robot.sensor.ultrasonic_belakang
            if jarak >= (target_jarak - 1) and jarak <= (target_jarak + 1): 
                gerak.stop(robot)
                if (now - self.start_time > 0.5): 
                    print(f"[SENJATA] Tiba di posisi dekat ({target_jarak}cm).")
                    self.transition_to("GESER_KESAMPING", now, robot, gerak)
            elif (jarak == -1): 
                gerak.mundur(robot)
                self.start_time = now
            else:
                gerak.mundur_ke_titik(robot, target_jarak)
                self.start_time = now
        
        
        
        
        return False