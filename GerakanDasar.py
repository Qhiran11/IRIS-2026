import time
from NonBlockingDelay import NonBlockingDelay

class PIDController:
    def __init__(self, Kp=8.0, Ki=0.001, Kd=15.0):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.prev_error = 0
        self.integral = 0

    def compute(self, target, current):
        error = current - target
        if error > 180: error -= 360
        if error < -180: error += 360

        self.integral += error
        derivative = error - self.prev_error
        output = (self.Kp * error) + (self.Ki * self.integral) + (self.Kd * derivative)
        self.prev_error = error
        return output

    def reset(self):
        self.prev_error = 0
        self.integral = 0


class GerakanDasar:
    def __init__(self):
        self.pid_kompas = PIDController(Kp=5.0, Ki=0.001, Kd=5.0)
        self.pid_kompas2 = PIDController(Kp=5.0, Ki=0.001, Kd=5.0)
        self.pid_jarak = PIDController(Kp=5.0, Ki=0.001, Kd=6.0) 

        self.pid_tinggi = PIDController(Kp=30.0, Ki=0.01, Kd=1.0)
        self.pid_pitch = PIDController(Kp=3.0, Ki=0.01, Kd=1.0)
        
        # Tentukan kecepatan maksimal motor (misalnya 255 atau 155 sesuai spesifikasi motor/driver)
        self.base_speed = 100  # Batas minimal PWM saat robot butuh koreksi
        self.max_pwm = 250 

        self.delay = NonBlockingDelay()
         
        self.target_angle = 0
        self.waktu_patokan = 0

        self.stateReturn = "HadapSudut"

    def _apply_motor(self, robot, FL, FR, BL, BR):
        """
        Helper untuk membatasi PWM dan mengirim ke objek motor.
        SINKRONISASI MANUAL CONTROL YANG BENAR:
        FL (Front Left)  = Array Index 3 = m4_pwm
        FR (Front Right) = Array Index 2 = m3_pwm
        BL (Back Left)   = Array Index 5 = m6_pwm
        BR (Back Right)  = Array Index 4 = m5_pwm
        """
        # Batasi nilai maksimum PWM agar aman
        FL_val = max(-self.max_pwm, min(self.max_pwm, int(FL)))
        FR_val = max(-self.max_pwm, min(self.max_pwm, int(FR)))
        BL_val = max(-self.max_pwm, min(self.max_pwm, int(BL)))
        BR_val = max(-self.max_pwm, min(self.max_pwm, int(BR)))

        # Masukkan ke variabel motor yang benar
        robot.motor.m1_pwm = FL_val
        robot.motor.m0_pwm = FR_val
        robot.motor.m3_pwm = BL_val
        robot.motor.m2_pwm = BR_val

    def penyeimbang(self, robot, now):
        pitch_sekarang = robot.sensor.pitch_kompas

        if pitch_sekarang > 1:
            robot.motor.mDorong1 = -155
            robot.motor.mDorong2 = 35
        elif pitch_sekarang < -1:
            robot.motor.mDorong1 = 35
            robot.motor.mDorong2 = -155
        elif pitch_sekarang == 1 or pitch_sekarang == -1 or pitch_sekarang == 0:
            robot.motor.mDorong1 = 0
            robot.motor.mDorong2 = 0
    
    
    
    def turun_ke_titk(self, robot, target_jarak):
        jarak_sekarang = robot.sensor.ultrasonic_bawah_tengah
        pitch_sekarang = robot.sensor.pitch_kompas
        
        # 1. Hitung error jarak (untuk mengetahui kapan harus stop)
        error_jarak = jarak_sekarang - target_jarak
        
        # 2. Toleransi: Berhenti jika jarak sudah pas (+- 1cm) DAN posisi sudah lurus (+- 1 derajat)
        if abs(error_jarak) <= 1 and abs(pitch_sekarang) <= 1:
            robot.motor.mDorong1 = 0
            robot.motor.mDorong2 = 0
            self.pid_tinggi.reset()
            self.pid_pitch.reset() # Reset juga integral pitch
            return True
            
        # 3. Hitung PID Ketinggian (Menghasilkan Base PWM)
        base_pwm = self.pid_tinggi.compute(target=target_jarak, current=jarak_sekarang)
        
        # 4. Hitung PID Penyeimbang (Menghasilkan Koreksi Pitch)
        # Target pitch selalu 0 (lurus sejajar tanah)
        koreksi_pitch = self.pid_pitch.compute(target=0, current=pitch_sekarang)
        
        # =========================================================
        # 5. PID MIXING (Perpaduan Tinggi dan Keseimbangan)
        # =========================================================
        # pwm_belakang dikurangi koreksi (jika pitch positif, belakang makin negatif / makin narik ke atas)
        # pwm_depan ditambah koreksi (jika pitch positif, depan makin positif / makin meluncur ke bawah)
        pwm_belakang = base_pwm - koreksi_pitch
        pwm_depan = base_pwm + koreksi_pitch
        
        # 6. ASYMMETRICAL CLAMPING (Membatasi kecepatan naik & turun)
        batas_maksimal_turun = 100    # Turun lambat dibantu gravitasi
        batas_maksimal_naik = -255   # Naik kuat melawan gravitasi
        batas_minimal_turun = 30     # Angka terkecil agar motor mau turun
        batas_minimal_naik = -130     # Angka terkecil agar motor kuat ngangkat naik
        
        def batasi_pwm(pwm_motor):
            # 1. Clamping Maksimal
            if pwm_motor > batas_maksimal_turun:
                pwm_motor = batas_maksimal_turun
            elif pwm_motor < batas_maksimal_naik:
                pwm_motor = batas_maksimal_naik
                
            # 2. Deadband Compensation (Mencegah macet saat error kecil)
            # Jika PID menyuruh TURUN (positif) tapi PWM terlalu kecil
            if 0 < pwm_motor < batas_minimal_turun:
                pwm_motor = batas_minimal_turun
                
            # Jika PID menyuruh NAIK (negatif) tapi PWM terlalu kecil (kurang kuat)
            elif 0 > pwm_motor > batas_minimal_naik:
                pwm_motor = batas_minimal_naik
                
            return int(pwm_motor)

        # 7. Aplikasikan ke motor
        robot.motor.mDorong1 = batasi_pwm(pwm_belakang)
        robot.motor.mDorong2 = batasi_pwm(pwm_depan)
        return False
               
        
            
    
    def stop(self, robot):
        robot.state.gerak_dasar_aktif = "STOP"
        self._apply_motor(robot, 0, 0, 0, 0)
        self.base_speed = 100  # Batas minimal PWM saat robot butuh koreksi
        self.max_pwm = 250 
        robot.motor.mDorong1 = 0
        robot.motor.mDorong2 = 0
        self.pid_kompas.reset()
        self.pid_kompas2.reset()
        self.pid_jarak.reset()
        

    # =====================================================================
    # 10 GERAKAN UTAMA (MECANUM KINEMATICS) - KOREKSI DISELARASKAN DENGAN HADAP SUDUT
    # =====================================================================

    def maju(self, robot):
        robot.state.gerak_dasar_aktif = "MAJU"
        kor = self.pid_kompas2.compute(self.target_angle, robot.sensor.kompas)
        self._apply_motor(robot, 
                          self.base_speed - kor, self.base_speed - kor, 
                          self.base_speed + kor, self.base_speed + kor)
        

    def mundur(self, robot):
        robot.state.gerak_dasar_aktif = "MUNDUR"
        kor = self.pid_kompas.compute(self.target_angle, robot.sensor.kompas)
        self._apply_motor(robot, 
                          -self.base_speed - kor, -self.base_speed - kor, 
                          -self.base_speed + kor, -self.base_speed + kor)
        

    def kiri(self, robot): # Strafe Kiri
        robot.state.gerak_dasar_aktif = "KIRI"
        kor = self.pid_kompas.compute(self.target_angle, robot.sensor.kompas)
        self._apply_motor(robot, 
                          -self.base_speed - kor,  self.base_speed - kor, 
                           self.base_speed + kor, -self.base_speed + kor)
        

    def kanan(self, robot): # Strafe Kanan
        robot.state.gerak_dasar_aktif = "KANAN"
        kor = self.pid_kompas.compute(self.target_angle, robot.sensor.kompas)
        self._apply_motor(robot,  
                           self.base_speed - kor, -self.base_speed - kor, 
                          -self.base_speed + kor,  self.base_speed + kor)
        

    # DIAGONAL MOVEMENT =======================================================
    def maju_diagonal_kanan(self, robot):
        robot.state.gerak_dasar_aktif = "maju diagonal kanan"
        kor = self.pid_kompas2.compute(self.target_angle, robot.sensor.kompas)
        self._apply_motor(robot, 
                          0 - kor, self.base_speed - kor, 
                          self.base_speed + kor, 0 + kor)

    def maju_diagonal_kiri(self, robot):
        robot.state.gerak_dasar_aktif = "maju diagonal kiri"
        kor = self.pid_kompas2.compute(self.target_angle, robot.sensor.kompas)
        self._apply_motor(robot, 
                          self.base_speed - kor, 0 - kor, 
                          0 + kor, self.base_speed + kor)

    def mundur_diagonal_kanan(self, robot):
        robot.state.gerak_dasar_aktif = "mundur diagonal kanan"
        kor = self.pid_kompas2.compute(self.target_angle, robot.sensor.kompas)
        self._apply_motor(robot, 
                          -self.base_speed + kor, 0 + kor, 
                          0 - kor, -self.base_speed - kor)

    def mundur_diagonal_kiri(self, robot):
        robot.state.gerak_dasar_aktif = "mundur diagonal kiri"
        kor = self.pid_kompas2.compute(self.target_angle, robot.sensor.kompas)
        self._apply_motor(robot, 
                          0 + kor, -self.base_speed + kor, 
                          -self.base_speed - kor, 0 - kor)
    # =========================================================================

    def geser_ke_tengah(self, robot, new_distance=0):
        robot.state.gerak_dasar_aktif = "geser ke tengah"
        target_kanan = 255
        if new_distance > 0:
            target_kanan = new_distance

        jarak = robot.sensor.ultrasonic_kanan
        speed_geser = 0

        if jarak == -1:
            speed_geser = 30 
        elif jarak > target_kanan - 3 and jarak < target_kanan + 3:
            speed_geser = 0
            self.pid_jarak.reset()
            return True
        else:
            speed_geser = self.pid_jarak.compute(target_kanan, jarak)
            speed_geser = max(-30, min(30, speed_geser))
        
        # Murni Strafe Jarak (Tanpa Campuran Kompas)
        self._apply_motor(robot, 
                          -speed_geser,  speed_geser, 
                           speed_geser, -speed_geser)
        return False
    
    def maju_ke_titik(self, robot, target_jarak, now):
        robot.state.gerak_dasar_aktif = "MAJU KE TITIK"
        kor_sudut = self.pid_kompas2.compute(self.target_angle, robot.sensor.kompas)
        jarak_sekarang = robot.sensor.ultrasonic_depan

        # Antisipasi jika sensor membaca error atau di luar jangkauan
        if jarak_sekarang <= 0 or jarak_sekarang == -1:
            return False
            
        speed_jarak = self.pid_jarak.compute(target_jarak, jarak_sekarang)

        # Batasi output PID sesuai base_speed
        speed_jarak = max(-self.base_speed, min(self.base_speed, speed_jarak))

        # PERBAIKAN: Mengubah tanda -speed_jarak menjadi positif (+) 
        # diselaraskan dengan master template fungsi maju()
        self._apply_motor(
            robot,
            speed_jarak + kor_sudut,
            speed_jarak + kor_sudut,
            speed_jarak - kor_sudut,
            speed_jarak - kor_sudut
        )

        # Logika pembacaan target & non-blocking delay disamakan persis dengan mundur_ke_titik
        if target_jarak - 1 <= jarak_sekarang <= target_jarak + 1:
            self.stop(robot)

            if getattr(self, 'waktu_patokan', None) is None:
                self.waktu_patokan = now
            if now - self.waktu_patokan > 0.1:
                self.waktu_patokan = None
                return True
        else:
            self.waktu_patokan = None

        return False

        
    
    def mundur_ke_titik(self, robot, target_jarak, now):
        robot.state.gerak_dasar_aktif = "MUNDUR KE TITIK"
        kor_sudut = self.pid_kompas2.compute(self.target_angle, robot.sensor.kompas)
        jarak_sekarang = robot.sensor.ultrasonic_belakang
        speed_jarak = self.pid_jarak.compute(target_jarak, jarak_sekarang)

        speed_jarak = max(-self.base_speed, min(self.base_speed, speed_jarak))
        self._apply_motor(robot, 
                          -speed_jarak - kor_sudut, -speed_jarak - kor_sudut, 
                          -speed_jarak + kor_sudut, -speed_jarak + kor_sudut)
        
        if target_jarak - 1 <= jarak_sekarang <= target_jarak + 1:
            self.stop(robot)
            if getattr(self, 'waktu_patokan', None) is None:
                self.waktu_patokan = now
            if now - self.waktu_patokan > 0.1:
                self.waktu_patokan = None  
                return True
        elif jarak_sekarang == 0 or jarak_sekarang == -1:
            self.mundur(robot)
            self.waktu_patokan = None
        else:
            self.waktu_patokan = None
        return False    


    def geser_ke_titik_kanan(self, robot, target_jarak, now):
        robot.state.gerak_dasar_aktif = "geser ke titik kanan"
        kor_sudut = self.pid_kompas2.compute(self.target_angle, robot.sensor.kompas)
        jarak_sekarang = robot.sensor.ultrasonic_kanan
        
        if jarak_sekarang <= 0 or jarak_sekarang == -1:
            speed_geser = 0
        else:
            speed_geser = self.pid_jarak.compute(target_jarak, jarak_sekarang)
            
        speed_geser = max(-self.base_speed, min(self.base_speed, speed_geser))
        
        self._apply_motor(robot, 
                          -speed_geser - kor_sudut,  speed_geser - kor_sudut, 
                           speed_geser + kor_sudut, -speed_geser + kor_sudut)
        if target_jarak - 1 <= jarak_sekarang <= target_jarak + 1:
            self.stop(robot)
            if getattr(self, 'waktu_patokan', None) is None:
                self.waktu_patokan = now
            if now - self.waktu_patokan > 0.05:
                self.waktu_patokan = None  
                return True
        else:
            self.waktu_patokan = None
        return False

    
    def geser_ke_titik_kiri(self, robot, target_jarak, now):
        robot.state.gerak_dasar_aktif = "geser ke titik kiri"
        kor_sudut = self.pid_kompas2.compute(self.target_angle, robot.sensor.kompas)
        jarak_sekarang = robot.sensor.ultrasonic_kiri
        
        # FILTER SENSOR & NOISE SEBELUM MASUK PID
        if jarak_sekarang <= 0 or jarak_sekarang == -1:
            self.kanan(robot)
            return False

        elif target_jarak > 100 and jarak_sekarang < 80:
            self.kanan(robot)
            return False
        speed_geser = self.pid_jarak.compute(target_jarak, jarak_sekarang)
            
        speed_geser = max(-self.base_speed, min(self.base_speed, speed_geser))
        
        # Eksekusi motor tetap berjalan untuk memastikan robot bisa berhenti (speed 0) saat ada noise
        self._apply_motor(robot, 
                          speed_geser - kor_sudut,  -speed_geser - kor_sudut, 
                         -speed_geser + kor_sudut,   speed_geser + kor_sudut)
                          
        if target_jarak - 2 <= jarak_sekarang <= target_jarak + 2:
            self.stop(robot)
            if getattr(self, 'waktu_patokan', None) is None:
                self.waktu_patokan = now
            if now - self.waktu_patokan > 0.1:
                self.waktu_patokan = None
                return True
        else:
            self.waktu_patokan = None
            
        return False
    
    

    
    def hadap_sudut(self, robot, now):
        """Berputar di tempat untuk mengunci sudut tertentu menggunakan PID"""
        robot.state.gerak_dasar_aktif = "hadap sudut"
        kor = self.pid_kompas.compute(self.target_angle, robot.sensor.kompas)
        
        # Master Template (Acuan Utama)
        self._apply_motor(robot, 
                          -kor, -kor,  
                          kor, kor) 
        if (robot.sensor.kompas >= self.target_angle - 1 and robot.sensor.kompas <= self.target_angle + 1): # -90 derajat ± 1 
            self.stop(robot)
            if getattr(self, 'waktu_patokan', None) is None:
                self.waktu_patokan = now
            if now - self.waktu_patokan > 0.1:
                self.waktu_patokan = None
                return True
 
    # =========================================================================
    # GERAKAN NON-MECANUM (LIFTER / PENGGERAK PW)
    # =========================================================================

    def turun(self, robot):
        robot.state.gerak_dasar_aktif = "naik"
        robot.motor.mDorong1 = -1
        robot.motor.mDorong2 = -1
        
    def naik(self, robot):
        robot.state.gerak_dasar_aktif = "turun"
        robot.motor.mDorong1 = 1
        robot.motor.mDorong2 = 1
        
    def maju_roda_2(self, robot):
        # self._apply_motor(robot, 0,0,0,0)
        robot.state.gerak_dasar_aktif = "maju roda 2"
    
    def mundur_roda_2(self, robot):
        self._apply_motor(robot, 0,0,0,0)
        robot.state.gerak_dasar_aktif = "mundur roda 2"
    
    def stop_roda_2(self, robot):
        robot.state.gerak_dasar_aktif = "mundur roda 2"

    
    
    
    def geser_ke_tengah2(self, robot, target_kanan):
        robot.state.gerak_dasar_aktif = "geser ke tengah2"
        jarak = robot.sensor.ultrasonic_kiri

        if jarak > target_kanan+2:
            self.kanan(robot)
            self.delay.last_time = time.time()
        elif jarak < target_kanan-2:
            self.kiri(robot)
            self.delay.last_time = time.time()
        else: 
            self.stop(robot)
            if self.delay.check_delay(0.1):
                return True
        return False

    def baliKePosisiAwal(self, robot):
        now = time.time()
        if self.stateReturn == "HadapSudut":
            self.target_angle = 0
            self.hadap_sudut(robot, now)
            if self.target_angle - 1 <= robot.sensor.kompas <= self.target_angle + 1:
                self.stop(robot)
                self.stateReturn = "turunBody"
        
        elif self.stateReturn == "turunBody":
            if self.turun_ke_titk(robot, 4):
                self.stop(robot)
                self.stateReturn = "MundurKetitik"

        elif self.stateReturn == "MundurKetitik":
            if self.mundur_ke_titik(robot, 10, now):
                self.stop(robot)
                self.stateReturn = "geser ke titik kiri"
        elif self.stateReturn == "geser ke titik kiri":
            if self.geser_ke_titik_kiri(robot, 87, now):
                self.stop(robot)
                self.stateReturn = "HadapSudut"
                return True
        return False
        