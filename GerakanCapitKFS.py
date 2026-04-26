# isi disini gerakan dasar untuk capit KFS
import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class GerakanCapitKFS:
    def __init__(self):
        # --- Parameter Kecepatan & Sudut ---
        self.pwm_naik_turun = 120    # Kecepatan maksimal motor PWM
        self.step_state_maju = 850     # Jumlah step maju
        self.step_state_tengah = 400   # Jumlah step tengah
        self.step_state_mundur = -850  # Jumlah step mundur
        self.posisiCapit = "belakang"
        
        # Sudut Servo (PCA) - Sesuaikan dengan kalibrasi mekanik Anda
        self.sudut_jepit_buka = 30
        self.sudut_jepit_tutup = 120
        self.sudut_putar_depan = 180
        self.sudut_putar_tengah = 90
        self.sudut_putar_belakang = 0


    
        self.posisiPutar = "depan" # Lacak posisi putaran saat ini
        
        # --- Parameter Waktu Putar (Kalibrasi dalam Detik) ---
        # Misal: Butuh 1.5 detik untuk putar 180 derajat (Belakang <-> Depan)
        self.waktu_putar_full = 0.6 
        # Misal: Butuh 0.75 detik untuk putar 90 derajat (Belakang/Depan <-> Tengah)
        self.waktu_putar_setengah = 0.75 
        self.pwm_arah = 0 
        
        self.putar_start_time = 0
        self.is_putar_active = False

    # ==========================================
    # 1. KONTROL JEPIT (1 PCA)
    # ==========================================
    def jepit(self, robot, writer, aktif):
        if aktif == "buka":
            print("buka")
        elif aktif == "jepit":
            print("jepit")
            
        robot.motor.gripper_status = 255
        
        data_keluar = robot.motor.get_array_output()
        writer.kirim_data(data_keluar)


    # ==========================================
    # 2. KONTROL NAIK TURUN (2 Motor PWM)
    # ==========================================
    def naik(self, robot):
        robot.motor.m5_pwm = self.pwm_naik_turun
        robot.motor.m6_pwm = self.pwm_naik_turun
        
    def turun(self, robot):
        robot.motor.m5_pwm = -self.pwm_naik_turun
        robot.motor.m6_pwm = -self.pwm_naik_turun

    def stop_naik_turun(self, robot):
        robot.motor.m5_pwm = 0
        robot.motor.m6_pwm = 0

    # ==========================================
    # 3. KONTROL MAJU MUNDUR (2 Motor Stepper)
    # ==========================================
    def MajuMundur(self, robot, writer, perintah):
        match perintah:
            case "maju":
                if self.posisiCapit == "belakang":
                    robot.motor.stepper1 = self.step_state_maju
                elif self.posisiCapit == "tengah":
                    robot.motor.stepper1 = self.step_state_maju - self.step_state_tengah

                self.posisiCapit = "depan"

            case "tengah":
                if self.posisiCapit == "belakang":
                    robot.motor.stepper1 = self.step_state_tengah
                elif self.posisiCapit == "depan":
                    robot.motor.stepper1 = -(self.step_state_tengah)

                self.posisiCapit = "tengah"
                
            case "mundur":
                if self.posisiCapit == "depan":
                    robot.motor.stepper1 = self.step_state_mundur
                elif self.posisiCapit == "tengah":
                    robot.motor.stepper1 = self.step_state_mundur + self.step_state_tengah
                self.posisiCapit = "belakang"

            case _:
                return  
        data_keluar = robot.motor.get_array_output()
        writer.kirim_data(data_keluar)

    # ==========================================
    # 4. KONTROL PUTAR (2 PCA)
    # ==========================================
    def putar_dinamis(self, robot, writer, target_posisi):
        """
        Target Posisi: "depan", "tengah", "belakang"
        Mengembalikan True jika rotasi selesai, False jika sedang berjalan.
        """
        # 1. Jika sudah di posisi yang sama, langsung kembalikan True
        if self.posisiPutar == target_posisi:
            return True

        # 2. Inisialisasi Gerakan Baru
        if not self.is_putar_active:
            self.putar_start_time = time.time()
            self.is_putar_active = True
            
            # Tentukan Arah dan Durasi berdasarkan posisi sekarang dan target
            self.durasi_target = 0
            self.pwm_arah = 0 
            
            if self.posisiPutar == "belakang":
                if target_posisi == "depan":
                    self.durasi_target = self.waktu_putar_full
                    self.pwm_arah = 255
                elif target_posisi == "tengah":
                    self.durasi_target = self.waktu_putar_setengah
                    self.pwm_arah = 255
                    
            elif self.posisiPutar == "tengah":
                if target_posisi == "depan":
                    self.durasi_target = self.waktu_putar_setengah
                    self.pwm_arah = 255
                elif target_posisi == "belakang":
                    self.durasi_target = self.waktu_putar_setengah
                    self.pwm_arah = -255
                    
            elif self.posisiPutar == "depan":
                if target_posisi == "belakang":
                    self.durasi_target = self.waktu_putar_full
                    self.pwm_arah = -255
                elif target_posisi == "tengah":
                    self.durasi_target = self.waktu_putar_setengah
                    self.pwm_arah = -255

            # Aktifkan Motor Putar


        # 3. Pengecekan Waktu (Non-Blocking)
        if self.is_putar_active:
            robot.motor.capit_putar1 = self.pwm_arah
            robot.motor.capit_putar2 = -self.pwm_arah
            writer.kirim_data(robot.motor.get_array_output())
            now = time.time()
            if (now - self.putar_start_time) >= self.durasi_target:
                # Waktu habis, hentikan motor
                robot.motor.capit_putar1 = 0
                robot.motor.capit_putar2 = 0
                writer.kirim_data(robot.motor.get_array_output())
                
                # Update status
                self.posisiPutar = target_posisi
                self.is_putar_active = False
                return True # Gerakan selesai
           
        return False # Masih dalam proses berputar