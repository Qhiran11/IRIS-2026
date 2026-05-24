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

        match self.state:
            case "TRANSISI":
                gerak.stop(robot)
                if (now - self.transition_start >= 0.1): # Jeda transisi 0.1 detik
                    self.state = self.next_state
                    self.start_time = now
                    print(f"[SENJATA] Masuk ke state: {self.state}")

            case "IDLE":
                print("[SENJATA] Memulai sequence RAKIT...")
                self.transition_to("PERSIAPAN", now, robot, gerak)

            case "PERSIAPAN":
                gerak.maju(robot)
                if (now - self.start_time > 0.8):
                    self.transition_to("PUTAR1", now, robot, gerak)
                    gerak.target_angle = target_angle                

            case "PUTAR1":
                gerak.hadap_sudut(robot)
                if (robot.sensor.kompas >= (target_angle - 2) and robot.sensor.kompas <= (target_angle + 2)):
                    if (now - self.start_time > 0.5): # Delay stabilisasi
                        print("[SENJATA] Menghadap 90 derajat. Mulai Mendekat...")
                        self.transition_to("MENDEKAT", now, robot, gerak)
            
            case "MENDEKAT":
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

            case "GESER_KESAMPING":
                gerak.base_speed = 35 # Kecepatan pelan
                gerak.max_pwm = 45
                jarak_kanan = robot.sensor.ultrasonic_kanan
                if jarak_kanan >= (self.targetJarakKanan - 1) and jarak_kanan <= (self.targetJarakKanan + 1):
                    gerak.stop(robot)
                    if (now - self.start_time > 0.5):
                        print(f"[SENJATA] Posisi lateral pas ({self.targetJarakKanan}cm). Mengaktifkan relay tambahan...")
                        robot.motor.relay_tambahan1 = 1
                        robot.motor.relay_tambahan2 = 1
                        self.transition_to("MUNDUR_PELAN", now, robot, gerak)
                else:
                    gerak.geser_ke_titik_kanan(robot, self.targetJarakKanan)
                    self.start_time = now

            case "MUNDUR_PELAN":
                # Pertahankan relay tambahan tetap bernilai 1 (HIGH)
                robot.motor.relay_tambahan1 = 1
                robot.motor.relay_tambahan2 = 1

                gerak.base_speed = 20 # Jauh lebih pelan
                gerak.max_pwm = 25
                jarak = robot.sensor.ultrasonic_belakang
                if jarak == 2: # target 2 cm (toleransi 1cm)
                    gerak.stop(robot)
                    if (now - self.start_time > 0.5):
                        print("[SENJATA] Tiba di posisi sangat dekat (2cm).")
                        self.transition_to("RELAY_MATI_1", now, robot, gerak)
                elif (jarak == -1):
                    gerak.mundur(robot)
                    self.start_time = now
                else:
                    gerak.mundur_ke_titik(robot, 2)
                    self.start_time = now

            case "RELAY_MATI_1":
                robot.motor.relay_tambahan1 = 0
                # Jeda 0.1s sebelum relay_tambahan2 LOW dan lanjut ke MAJU_30CM
                if (now - self.start_time >= 1.5):
                    robot.motor.relay_tambahan2 = 0
                    self.transition_to("RELAY_MATI_2", now, robot, gerak)
            
            case "RELAY_MATI_2":
                # robot.motor.relay_tambahan1 = 0
                # Jeda 0.1s sebelum relay_tambahan2 LOW dan lanjut ke MAJU_30CM
                if (now - self.start_time >= 3):
                    # robot.motor.relay_tambahan2 = 0
                    self.transition_to("MAJU_30CM", now, robot, gerak)

            case "MAJU_30CM":
                robot.motor.relay_tambahan1 = 0
                robot.motor.relay_tambahan2 = 0

                gerak.base_speed = 60
                gerak.max_pwm = 70
                jarak = robot.sensor.ultrasonic_belakang
                if jarak >= 51 and jarak <= 53: # target 30 cm
                    gerak.stop(robot)
                    if (now - self.start_time > 0.5):
                        print("[SENJATA] Tiba di posisi 30cm.")
                        gerak.target_angle = -90
                        self.transition_to("PUTAR_NEG_90", now, robot, gerak)
                elif (jarak == -1):
                    gerak.maju(robot)
                    self.start_time = now
                else:
                    gerak.mundur_ke_titik(robot, 52)
                    self.start_time = now

            case "PUTAR_NEG_90":
                gerak.base_speed = 80
                gerak.max_pwm = 90
                gerak.hadap_sudut(robot)
                if (robot.sensor.kompas >= -92 and robot.sensor.kompas <= -88): # -90 derajat ± 2
                    if (now - self.start_time > 0.5):
                        print("[SENJATA] Kembali menghadap -90 derajat.")
                        self.transition_to("DELAY_1", now, robot, gerak)
            case "DELAY_1":
                gerak.stop(robot)
                if (now - self.start_time > 20):
                    robot.motor.relay_tambahan1 = 1
                    robot.motor.relay_tambahan2 = 1
                    self.transition_to("FINISHED", now, robot, gerak)
            
            case "FINISHED":
                self.is_done = True
                gerak.stop(robot)
                return True

        return False