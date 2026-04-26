import time
from GerakanCapitKFS import GerakanCapitKFS

class GerakanAmbilKFS:
    def __init__(self):
        self.capit = GerakanCapitKFS()
        self.state = "IDLE"
        self.start_time = 0
        self.is_done = False

    def reset(self):
        self.state = "IDLE"
        self.is_done = False

    def jalankan(self, robot):
        now = time.time()

        # --- STATE 0: INISIALISASI ---
        if self.state == "IDLE":
            print("[KFS] Memulai sequence AMBIL...")
            self.start_time = now
            self.state = "PREPARE"

        # --- STATE 1: BUKA & TURUN ---
        elif self.state == "PREPARE":
            if (now - self.start_time) < 1.0:
                self.capit.buka(robot)
                self.capit.turun(robot)
                self.capit.putar_setengah(robot)
            else:
                self.capit.stop_naik_turun(robot)
                self.start_time = now
                self.state = "APPROACH"

        # --- STATE 2: STEPPER MAJU ---
        elif self.state == "APPROACH":
            if (now - self.start_time) < 1.5:
                self.capit.maju(robot)
            else:
                self.start_time = now
                self.state = "GRAB"

        # --- STATE 3: TUTUP/JEPIT ---
        elif self.state == "GRAB":
            if (now - self.start_time) < 0.8:
                self.capit.tutup(robot)
            else:
                self.start_time = now
                self.state = "RETRACT"

        # --- STATE 4: NAIK & MUNDUR ---
        elif self.state == "RETRACT":
            if (now - self.start_time) < 1.5:
                self.capit.naik(robot)
                self.capit.mundur(robot)
            else:
                self.capit.stop_naik_turun(robot)
                self.state = "FINISHED"

        # --- STATE 5: SELESAI ---
        elif self.state == "FINISHED":
            self.is_done = True
            return True

        return False