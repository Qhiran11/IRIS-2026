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

    def AmbilKFS(self, robot, gerak, now):
        jarak_depan = robot.sensor.ultrasonic_depan
        if robot.state.kfs_state == "TRANSISI":
            gerak.stop(robot)
            jeda_transisi = robot.config.data.get("umum", {}).get("jeda_transisi_default", 0.01)
            if (now - robot.state.kfs_transition_start > jeda_transisi): # Jeda transisi 0.01 detik
                robot.state.kfs_state = robot.state.kfs_next_state
                robot.state.kfs_transition_start = now
                print(f"[KFS] Masuk ke state: {robot.state.kfs_state}")

        elif robot.state.kfs_state == "IDLE":
            robot.state.kfs_start_time = now # TAHAN TIMER DI SINI
            robot.state.kfs_transition_start = now
            self.transition_to("MAJU", now, robot, gerak)
        
        elif robot.state.kfs_state == "MAJU":
            maju_cfg = robot.config.data.get("gerakan_kfs", {}).get("maju", {})
            gerak.base_speed = maju_cfg.get("base_speed", 30)
            gerak.max_pwm = maju_cfg.get("max_pwm", 40)
            target_jarak = maju_cfg.get("target_jarak", 4)
            if gerak.maju_ke_titik(robot, target_jarak, now) or jarak_depan == 0:
                self.transition_to("AMBIL_KFS", now, robot, gerak)
                
        elif robot.state.kfs_state == "AMBIL_KFS":
            t = now - robot.state.kfs_transition_start
            timing = robot.config.data.get("gerakan_kfs", {}).get("timing", {})
            if t > timing.get("angkat", 4.3): #angkat
                robot.motor.relayCapitKFSAngkat = 0
                return True
            elif t > timing.get("jepit_stop", 3.8):  #jepit + stop
                robot.motor.relayCapitKFSJepit  = 1
                gerak.stop(robot)
            elif t > timing.get("maju", 3.4):  #maju
                gerak.maju(robot)
            elif t > timing.get("buka_stop", 3.1): #buka +stop
                robot.motor.relayCapitKFSJepit  = 0
                gerak.stop(robot)
            elif t > timing.get("mundur", 2.7):  #mundur
                gerak.mundur(robot)
            elif t > timing.get("jepit_lagi", 1.7): #jepit
                robot.motor.relayCapitKFSJepit  = 1
            elif t > timing.get("turun", 1.0): #turun
                robot.motor.relayCapitKFSAngkat = 1 
            elif t > timing.get("buka_awal", 0.1): #buka
                robot.motor.relayCapitKFSJepit  = 0      
        return False

    
    
    def detectKFS (self, robot):
        if robot.sensor.sensor_kfs_depan == 0:
            return "KFSDIDEPAN"

        return "TAKADAKFS" # Urutan masih berjalan