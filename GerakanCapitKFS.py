# isi disini gerakan dasar untuk capit KFS
import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class GerakanCapitKFS:
    def __init__(self):
        # --- Parameter Kecepatan & Sudut ---
        self.pwm_naik_turun = 120    # Kecepatan maksimal motor PWM
        
        # Sudut Servo (PCA) - Sesuaikan dengan kalibrasi mekanik Anda
        self.sudut_jepit_buka = 30
        self.sudut_jepit_tutup = 120
        self.sudut_putar_depan = 180
        self.sudut_putar_tengah = 90
        self.sudut_putar_belakang = 0


    
        self.posisiPutar = "putar1" # Lacak posisi putaran saat ini
        self.waktu_putar = time.time()
        
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
    # # positif jepit
    # robot.motor.capit_jepit = 40

    # # negatif  buka
    # robot.motor.capit_jepit = -40            
    def jepit(self, robot):
        if robot.sensor.limit_capitJepit == 0:
            robot.motor.capit_jepit = 0
            return True
        else:
            robot.motor.capit_jepit = 255
        return False

    def buka(self, robot):
        if robot.sensor.limit_capitBuka == 0:
            robot.motor.capit_jepit = 0
            return True
        else:
            robot.motor.capit_jepit = -230
        return False

    # ==========================================
    # 2. KONTROL MAJU MUNDUR (2 Motor Stepper)
    # ==========================================
    def MajuMundur(self, robot, perintah):

        # postif mundur
        # Capit.MajuMundur(robot, 800)

        # negatif maju
        # Capit.MajuMundur(robot, -800)        
        robot.motor.stepper1 = perintah
                
    # ==========================================
    # 4. KONTROL PUTAR (2 PCA)
    # ==========================================
    def putar_capit_kebelakang(self, robot):
        """
        Target Posisi: "depan", "tengah", "belakang"
        Mengembalikan True jika rotasi selesai, False jika sedang berjalan.
        """
        if (robot.sensor.limit_kiri_capit == 0):robot.motor.capit_putar_kiri = 0
        else:robot.motor.capit_putar_kiri = 180

        if (robot.sensor.limit_kanan_capit == 0):robot.motor.capit_putar_kanan = 0
        else:robot.motor.capit_putar_kanan = -180

        if ((robot.sensor.limit_kiri_capit == 0) and (robot.sensor.limit_kanan_capit == 0)): return True

        
        return False # Masih dalam proses berputar

    def putar_capit_kedepan(self, robot):
        """
        Target Posisi: "depan", "tengah", "belakang"
        Mengembalikan True jika rotasi selesai, False jika sedang berjalan.
        """
        # putar belakang
        robot.motor.capit_putar_kiri = -180
        robot.motor.capit_putar_kanan = 180

        
        return False # Masih dalam proses berputar

    def capit_stop(self, robot):
        """
        Target Posisi: "depan", "tengah", "belakang"
        Mengembalikan True jika rotasi selesai, False jika sedang berjalan.
        """
        # putar belakang
        robot.motor.capit_putar_kiri = 0
        robot.motor.capit_putar_kanan = 0

        
        return False # Masih dalam proses berputar

    