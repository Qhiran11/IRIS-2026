import time
from GerakanCapitKFS import GerakanCapitKFS


class GerakanAmbilKFS:
    def __init__(self):
        self.capit = GerakanCapitKFS()

    def jalankan_kombinasi_1(self, robot, gerak):
        """
        Urutan Kombinasi 1 KFS.
        Harus dipanggil berulang-ulang di loop utama (Non-Blocking).
        Mengembalikan True jika seluruh urutan selesai.
        """
        now = time.time()

        # ==========================================
        # STATE 0: INISIALISASI
        # ==========================================
        if robot.state.kfs_state == "IDLE":
            selesai = self.capit.putar_capit_kebelakang(robot)
            robot.state.kfs_start_time = time.time()
            if (selesai):
                robot.state.kfs_state = "READY"
                
        elif robot.state.kfs_state == "READY":
            self.capit.putar_capit_kedepan(robot)
            self.capit.buka(robot)
            gerak.base_speed  = 30
            gerak.max_pwm = gerak.base_speed
            if (time.time() - robot.state.kfs_then > 1.5):
                self.capit.capit_stop(robot)
                robot.state.kfs_then = time.time()
                robot.state.kfs_state = "ROBOTMAJU"
        
        elif robot.state.kfs_state == "ROBOTMAJU":
            if (robot.sensor.jarak_depan <= 100):
                gerak.stop(robot)
                robot.state.kfs_then = time.time()
                robot.state.kfs_state = "CAPITMAJU"
            else:
                gerak.maju(robot)
        
        elif robot.state.kfs_state == "CAPITMAJU":
            self.capit.MajuMundur(robot, -800)
            if (time.time() - robot.state.kfs_then > 1):
                self.capit.capit_stop(robot)
                self.capit.MajuMundur(robot, 0)
                robot.state.kfs_state = "JEPIT"
        
        elif robot.state.kfs_state == "JEPIT":
            selesai = self.capit.jepit(robot)
            if (selesai):
                robot.state.kfs_state = "MUNDUR"
                robot.state.kfs_then = now
        
        elif robot.state.kfs_state == "MUNDUR":
            self.capit.MajuMundur(robot, 800)
            if (now - robot.state.kfs_then > 0.8):
                robot.state.kfs_state = "ANGKUT"
        
        elif robot.state.kfs_state == "ANGKUT":
            selesai = self.capit.putar_capit_kebelakang(robot)
            if (selesai):
                robot.state.kfs_state = "LEPAS"
                robot.state.kfs_then = now
        
        elif robot.state.kfs_state == "LEPAS":
            selesai = self.capit.buka(robot)
            if (selesai):
                robot.state.kfs_state = "BACK"
                robot.state.kfs_then = now
        
        elif robot.state.kfs_state == "BACK":
            self.capit.putar_capit_kedepan(robot)
            if (time.time() - robot.state.kfs_then > 0.5):
                self.capit.capit_stop(robot)
                robot.state.kfs_then = time.time()
                robot.state.kfs_state = "FINISHED"
        
        elif robot.state.kfs_state == "FINISHED":
            self.capit.capit_stop(robot)
            robot.motor.stepper1 = 0

            return True     
        
        
        return False # Urutan masih berjalan




    def detectKFS (self, robot):
        if robot.sensor.sensor_kfs_depan == 0:
            return "KFSDIDEPAN"

        return "TAKADAKFS" # Urutan masih berjalan
    