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
    def set_tunings(self, Kp, Ki, Kd):
        """
        Berfungsi untuk memperbarui parameter PID secara real-time
        seiring berjalannya program (Continuous Adaptive Tuning).
        """
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd


class GerakanDasar:
    def __init__(self):
        self.pid_kompas = PIDController(Kp=5.0, Ki=0.001, Kd=5.0)
        self.pid_kompas2 = PIDController(Kp=5.0, Ki=0.001, Kd=5.0)
        self.pid_jarak = PIDController(Kp=10.0, Ki=0.05, Kd=1.0) 

        self.pid_tinggi = PIDController(Kp=10.0, Ki=0.0, Kd=0.0)
        self.pid_pitch = PIDController(Kp=4.0, Ki=0.0, Kd=0.0)
        
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
            robot.motor.mDorong1 = -135
            robot.motor.mDorong2 = 45
        elif pitch_sekarang < -1:
            robot.motor.mDorong1 = 35
            robot.motor.mDorong2 = -155
        elif pitch_sekarang == 1 or pitch_sekarang == -1 or pitch_sekarang == 0:
            robot.motor.mDorong1 = 0
            robot.motor.mDorong2 = 0
    
    
    
    def naikTurunBiasa (self, robot, target):
        jarak = robot.sensor.ultrasonic_bawah_tengah
        if jarak < target:
            robot.motor.mDorong1 = -255
            robot.motor.mDorong2 = -240
        else:
            robot.motor.mDorong1 = 0
            robot.motor.mDorong2 = 0
    
    def turun_ke_titk(self, robot, target_jarak, temp_pitch=3):
        jarak_sekarang = robot.sensor.ultrasonic_bawah_tengah
        pitch_sekarang = robot.sensor.pitch_kompas
        
        # 1. Hitung error jarak dan pitch
        error_jarak = jarak_sekarang - target_jarak
        abs_error = abs(error_jarak)
        
        error_pitch = pitch_sekarang - temp_pitch # Menghitung selisih dari patokan 3 derajat
        
        # =========================================================
        # CONTINUOUS ADAPTIVE TUNING (JARAK & WAKTU)
        # =========================================================
        def map_value(x, in_min, in_max, out_min, out_max):
            x = max(in_min, min(in_max, x))
            return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

        # A. Tuning Kp Berdasarkan Jarak
        # NAIKKAN batas bawahnya! Jangan 0.5, coba 2.0 agar motor tetap punya tenaga di 5cm terakhir.
        # Batas atas dinaikkan ke 10.0 agar turunnya lebih gesit.
        dinamis_Kp = map_value(abs_error, 3, 30, 2.0, 10.0)
        
        # B. Tuning Ki Berdasarkan Jarak & Waktu (Mencegah macet 1 menit)
        # NAIKKAN Ki maksimal ke 0.2. Ini akan membuat akumulasi tenaga 4x lebih cepat dari sebelumnya.
        dinamis_Ki = map_value(abs_error, 1, 10, 0.09, 0.0)
        
        # Terapkan nilai dinamis ke objek PID tinggi
        self.pid_tinggi.set_tunings(dinamis_Kp, dinamis_Ki, 1.0) 
        # =========================================================

        # 2. Toleransi: Berhenti jika masuk range aman (+- 1cm) dan pitch sesuai patokan (+- 1 derajat)
        if abs_error <= 1 and abs(error_pitch) <= 1:
            robot.motor.mDorong1 = 0
            robot.motor.mDorong2 = 0
            self.pid_tinggi.reset()
            self.pid_pitch.reset()
            return True
            
        # ... (lanjutkan dengan base_pwm dan PID Mixing seperti sebelumnya)
            
        # 3. Hitung PID Ketinggian (Menghasilkan Base PWM)
        base_pwm = self.pid_tinggi.compute(target=target_jarak, current=jarak_sekarang)
        
        # 4. Hitung PID Penyeimbang (Menghasilkan Koreksi Pitch)
        koreksi_pitch = self.pid_pitch.compute(target=3, current=pitch_sekarang)
        
        # 5. PID MIXING
        pwm_belakang = base_pwm - koreksi_pitch
        pwm_depan = base_pwm + koreksi_pitch
        
        # 6. ASYMMETRICAL CLAMPING
        batas_maksimal_turun = 80    # Turun lambat dibantu gravitasi
        batas_maksimal_naik = -255   # Naik kuat melawan gravitasi
        batas_minimal_turun = 30     # Angka terkecil turun
        batas_minimal_naik = -200    # Angka terkecil kuat ngangkat
        
        def batasi_pwm(pwm_motor):
            # Clamping Maksimal
            if pwm_motor > batas_maksimal_turun:
                pwm_motor = batas_maksimal_turun
            elif pwm_motor < batas_maksimal_naik:
                pwm_motor = batas_maksimal_naik
                
            # Deadband Compensation
            if 0 < pwm_motor < batas_minimal_turun:
                pwm_motor = batas_minimal_turun
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
    
    # Helper fungsi map diletakkan di luar (atau di dalam class) agar rapi jika memungkinkan,
    # namun di sini saya sematkan langsung agar Anda bisa sekadar Copy-Paste dengan aman.
    # Helper fungsi map diletakkan di luar (atau di dalam class) agar rapi jika memungkinkan,
    # namun di sini saya sematkan langsung agar Anda bisa sekadar Copy-Paste dengan aman.
    def _map_value(self, x, in_min, in_max, out_min, out_max):
        x = max(in_min, min(in_max, x))
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    def maju_ke_titik(self, robot, target_jarak, now):
        robot.state.gerak_dasar_aktif = "MAJU KE TITIK"
        jarak_sekarang = robot.sensor.ultrasonic_depan

        # Antisipasi jika sensor membaca error atau di luar jangkauan
        if jarak_sekarang <= 0 or jarak_sekarang == -1:
            return False
            
        abs_error = abs(jarak_sekarang - target_jarak)
        
        # --- ADAPTIVE TUNING PID JARAK ---
        # Kp: Saat sisa 30cm, Kp agresif (misal 8.0). Saat sisa 5cm, Kp mengecil (misal 3.0)
        dinamis_Kp = self._map_value(abs_error, 5, 30, 1.1, 8.0)
        # Ki: Aktif menendang gesekan hanya saat jarak < 10cm
        dinamis_Ki = self._map_value(abs_error, 1, 10, 0.1, 0.0)
        self.pid_jarak.set_tunings(dinamis_Kp, dinamis_Ki, self.pid_jarak.Kd)
        # ---------------------------------

        kor_sudut = self.pid_kompas2.compute(self.target_angle, robot.sensor.kompas)
        speed_jarak = self.pid_jarak.compute(target_jarak, jarak_sekarang)

        # Batasi output PID sesuai base_speed
        speed_jarak = max(-self.base_speed, min(self.base_speed, speed_jarak))

        self._apply_motor(
            robot,
            speed_jarak - kor_sudut,
            speed_jarak - kor_sudut,
            speed_jarak + kor_sudut,
            speed_jarak + kor_sudut
        )

        if target_jarak - 1 <= jarak_sekarang <= target_jarak + 1:
            self.stop(robot)
            if getattr(self, 'waktu_patokan', None) is None:
                self.waktu_patokan = now
            if now - self.waktu_patokan > 0.1:
                self.waktu_patokan = None
                self.pid_jarak.reset()    # Reset error integral
                self.pid_kompas2.reset()  # Reset error integral kompas
                return True
        else:
            self.waktu_patokan = None

        return False

        
    def mundur_ke_titik(self, robot, target_jarak, now):
        robot.state.gerak_dasar_aktif = "MUNDUR KE TITIK"
        jarak_sekarang = robot.sensor.ultrasonic_belakang
        
        if jarak_sekarang <= 0 or jarak_sekarang == -1:
            # Sesuai logika Anda sebelumnya
            self.mundur(robot) 
            self.waktu_patokan = None
            return False

        abs_error = abs(jarak_sekarang - target_jarak)
        
        # --- ADAPTIVE TUNING PID JARAK ---
        dinamis_Kp = self._map_value(abs_error, 5, 30, 2.0, 8.0)
        dinamis_Ki = self._map_value(abs_error, 1, 10, 0.1, 0.0)
        self.pid_jarak.set_tunings(dinamis_Kp, dinamis_Ki, self.pid_jarak.Kd)
        # ---------------------------------

        kor_sudut = self.pid_kompas2.compute(self.target_angle, robot.sensor.kompas)
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
                self.pid_jarak.reset()
                self.pid_kompas2.reset()
                return True
        else:
            self.waktu_patokan = None
            
        return False    


    def geser_ke_titik_kanan(self, robot, target_jarak, now):
        robot.state.gerak_dasar_aktif = "geser ke titik kanan"
        jarak_sekarang = robot.sensor.ultrasonic_kanan
        
        if jarak_sekarang <= 0 or jarak_sekarang == -1:
            speed_geser = 0
        else:
            abs_error = abs(jarak_sekarang - target_jarak)
            
            # --- ADAPTIVE TUNING PID JARAK ---
            # Bergerak geser (strafing) biasanya butuh torsi lebih besar karena gesekan roda omni/mecanum
            dinamis_Kp = self._map_value(abs_error, 5, 30, 3.0, 10.0) 
            dinamis_Ki = self._map_value(abs_error, 1, 10, 0.2, 0.0)
            self.pid_jarak.set_tunings(dinamis_Kp, dinamis_Ki, self.pid_jarak.Kd)
            # ---------------------------------
            
            speed_geser = self.pid_jarak.compute(target_jarak, jarak_sekarang)
            
        kor_sudut = self.pid_kompas2.compute(self.target_angle, robot.sensor.kompas)
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
                self.pid_jarak.reset()
                self.pid_kompas2.reset()
                return True
        else:
            self.waktu_patokan = None
            
        return False

    
    def geser_ke_titik_kiri(self, robot, target_jarak, now):
        robot.state.gerak_dasar_aktif = "geser ke titik kiri"
        jarak_sekarang = robot.sensor.ultrasonic_kiri
        
        # FILTER SENSOR & NOISE SEBELUM MASUK PID
        if jarak_sekarang <= 0 or jarak_sekarang == -1:
            self.kanan(robot)
            return False

        elif target_jarak > 100 and jarak_sekarang < 80:
            self.kanan(robot)
            return False
            
        abs_error = abs(jarak_sekarang - target_jarak)
        
        # --- ADAPTIVE TUNING PID JARAK ---
        dinamis_Kp = self._map_value(abs_error, 5, 30, 4.0, 10.0)
        dinamis_Ki = self._map_value(abs_error, 1, 10, 0.2, 0.0)
        self.pid_jarak.set_tunings(dinamis_Kp, dinamis_Ki, self.pid_jarak.Kd)
        # ---------------------------------

        kor_sudut = self.pid_kompas2.compute(self.target_angle, robot.sensor.kompas)
        speed_geser = self.pid_jarak.compute(target_jarak, jarak_sekarang)
            
        speed_geser = max(-self.base_speed, min(self.base_speed, speed_geser))
        
        # Eksekusi motor tetap berjalan untuk memastikan robot bisa berhenti (speed 0) saat ada noise
        self._apply_motor(robot, 
                          speed_geser - kor_sudut,  -speed_geser - kor_sudut, 
                         -speed_geser + kor_sudut,   speed_geser + kor_sudut)
                          
        # Menggunakan toleransi 2cm sesuai kode asli Anda pada fungsi ini
        if target_jarak - 2 <= jarak_sekarang <= target_jarak + 2:
            self.stop(robot)
            if getattr(self, 'waktu_patokan', None) is None:
                self.waktu_patokan = now
            if now - self.waktu_patokan > 0.1:
                self.waktu_patokan = None
                self.pid_jarak.reset()
                self.pid_kompas2.reset()
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
        return False
 
    # =========================================================================
    # GERAKAN NON-MECANUM (LIFTER / PENGGERAK PW)
    # =========================================================================
    
    
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
            if self.hadap_sudut(robot, now):
                self.stop(robot)
                self.stateReturn = "turunBody"
        
        elif self.stateReturn == "turunBody":
            jarak_belakang = robot.sensor.ultrasonic_belakang
            self.turun_ke_titk(robot, 4)
            if jarak_belakang > 0:
                self.stop(robot)
                self.stateReturn = "MundurKetitik"

        elif self.stateReturn == "MundurKetitik":
            self.base_speed = 40
            self.max_pwm = 50
            if self.mundur_ke_titik(robot, 10, now):
                self.stop(robot)
                self.stateReturn = "HadapSudut"
                return True
        elif self.stateReturn == "geser ke titik kiri":
            if self.geser_ke_titik_kiri(robot, 47, now):
                self.stop(robot)
                self.stateReturn = "HadapSudut"
                return True
        return False
        