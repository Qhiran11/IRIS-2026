import time
from GerakanCapitKFS import GerakanCapitKFS


class GerakanAmbilKFS:
    def __init__(self):
        self.capit = GerakanCapitKFS()

    def transition_to(self, target_state, now, robot, gerak):
        gerak.stop(robot)
        robot.state.kfs_state = "TRANSISI"
        robot.state.kfs_next_state = target_state
        robot.state.kfs_transition_start = now

    def jalankan_kombinasi_1(self, robot, gerak):
        """
        Urutan Kombinasi 1 KFS.
        Harus dipanggil berulang-ulang di loop utama (Non-Blocking).
        Mengembalikan True jika seluruh urutan selesai.
        """
        now = time.time()

        # ==========================================
        # STATE MACHINE MENGGUNAKAN IF-ELIF DENGAN TRANSISI
        # ==========================================
        if robot.state.kfs_state == "TRANSISI":
            gerak.stop(robot)
            if (now - robot.state.kfs_transition_start > 0.01): # Jeda transisi 0.01 detik
                robot.state.kfs_state = robot.state.kfs_next_state
                robot.state.kfs_transition_start = now
                print(f"[KFS] Masuk ke state: {robot.state.kfs_state}")

        elif robot.state.kfs_state == "IDLE":
            robot.state.kfs_start_time = now # TAHAN TIMER DI SINI
            robot.state.kfs_transition_start = now
            self.transition_to("READY", now, robot, gerak)
                
        elif robot.state.kfs_state == "READY":
            robot.motor.relay_tambahan1 = 1 # Capit jepit kfs terbuka
            robot.motor.relay_tambahan2 = 0 # Capit kfs naik
            self.transition_to("BUANG", now, robot, gerak)
        
        elif robot.state.kfs_state == "AMBIL":
            elapsed_time = now - robot.state.kfs_transition_start
            if elapsed_time > 3.0: 
                robot.motor.relay_tambahan2 = 0
                # self.transition_to("FINISHED", now, robot, gerak)
                return True     
            elif elapsed_time > 0.2: 
                robot.motor.relay_tambahan1 = 0
            elif elapsed_time > 0.01: 
                robot.motor.relay_tambahan2 = 1         

        elif robot.state.kfs_state == "BUANG":
            elapsed_time = now - robot.state.kfs_transition_start
            if elapsed_time > 4.5: 
                robot.motor.relay_tambahan1 = 1
            elif elapsed_time > 3.0: 
                robot.motor.relay_tambahan2 = 0
            elif elapsed_time > 0.2: 
                robot.motor.relay_tambahan1 = 0
            elif elapsed_time > 0.01: 
                robot.motor.relay_tambahan2 = 1          
        return False # Urutan masih berjalan

    def detectKFS (self, robot):
        if robot.sensor.sensor_kfs_depan == 0:
            return "KFSDIDEPAN"

        return "TAKADAKFS" # Urutan masih berjalan