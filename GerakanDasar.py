class PIDController:
    def __init__(self, Kp=8.0, Ki=0.001, Kd=15.0):
        # Parameter diambil dari PID.ino [cite: 28]
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.prev_error = 0
        self.integral = 0

    def compute(self, target, current):
        # Logika normalisasi sudut -180 sampai 180 [cite: 32]
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
        # 1. Buat dua objek PID yang berbeda
        self.pid_kompas = PIDController(Kp=8.0, Ki=0.001, Kd=15.0)
        self.pid_kompas2 = PIDController(Kp=5.0, Ki=0.001, Kd=10.0)
        # Tuning PID Jarak berbeda: Butuh Kp lebih besar agar agresif di awal, 
        # Ki = 0, Kd sedang untuk mengerem. (Silakan kalibrasi nanti)
        self.pid_jarak = PIDController(Kp=8.0, Ki=0.001, Kd=15.0) 
        
        self.base_speed = 85 
        self.max_pwm = 120   
        self.target_angle = 0

    def _apply_motor(self, robot, m1, m2, m3, m4):
        """Helper untuk membatasi PWM dan mengirim ke objek motor"""
        robot.motor.m3_pwm = max(-self.max_pwm, min(self.max_pwm, int(m2)))
        robot.motor.m4_pwm = max(-self.max_pwm, min(self.max_pwm, int(m1)))
        robot.motor.m5_pwm = max(-self.max_pwm, min(self.max_pwm, int(m4)))
        robot.motor.m6_pwm = max(-self.max_pwm, min(self.max_pwm, int(m3)))

    def stop(self, robot):
        self._apply_motor(robot, 0, 0, 0, 0)
        self.pid_kompas.reset()
        self.pid_jarak.reset()

    # --- 10 GERAKAN UTAMA ---


    def mundur_ke_titik(self, robot, target_jarak):
        kor_sudut = self.pid_kompas2.compute(self.target_angle, robot.sensor.kompas)
        jarak_sekarang = robot.sensor.ultrasonic_belakang
        speed_jarak = self.pid_jarak.compute(target_jarak, jarak_sekarang)

        
        speed_jarak = max(-self.base_speed, min(self.base_speed, speed_jarak))
        self._apply_motor(robot, 
                          -speed_jarak - kor_sudut, -speed_jarak + kor_sudut, 
                          -speed_jarak - kor_sudut, -speed_jarak + kor_sudut)

    def maju(self, robot):
        
        kor = self.pid_kompas2.compute(self.target_angle, robot.sensor.kompas)
        # Sesuai PID.ino: Kanan (m1,m3) = base - kor, Kiri (m2,m4) = base + kor [cite: 36-37]
        self._apply_motor(robot, self.base_speed - kor, self.base_speed + kor, 
                                 self.base_speed - kor, self.base_speed + kor)

    def mundur(self, robot):
        kor = self.pid_kompas.compute(self.target_angle, robot.sensor.kompas)
        self._apply_motor(robot, -self.base_speed - kor, -self.base_speed + kor, 
                                 -self.base_speed - kor, -self.base_speed + kor)

    def kanan(self, robot): # Strafe Kanan
        kor = self.pid_kompas.compute(self.target_angle, robot.sensor.kompas)
        self._apply_motor(robot, -self.base_speed - kor,  self.base_speed + kor, 
                                  self.base_speed - kor, -self.base_speed + kor)

    def kiri(self, robot): # Strafe Kiri
        kor = self.pid_kompas.compute(self.target_angle, robot.sensor.kompas)
        self._apply_motor(robot,  self.base_speed - kor, -self.base_speed + kor, 
                                 -self.base_speed - kor,  self.base_speed + kor)



    # DIAGONAL MOVEMENT  =====================================================================
    def maju_diagonal_kanan(self, robot):
        kor = self.pid_kompas2.compute(self.target_angle, robot.sensor.kompas)
        self._apply_motor(robot, 0 - kor, self.base_speed + kor, self.base_speed - kor, 0 + kor)

    def maju_diagonal_kiri(self, robot):
        kor = self.pid_kompas2.compute(self.target_angle, robot.sensor.kompas)
        self._apply_motor(robot, self.base_speed - kor, 0 + kor, 0 - kor, self.base_speed + kor)

    def mundur_diagonal_kanan(self, robot):
        kor = self.pid_kompas2.compute(self.target_angle, robot.sensor.kompas)
        self._apply_motor(robot, -self.base_speed - kor, 0 + kor, 0 - kor, -self.base_speed + kor)

    def mundur_diagonal_kiri(self, robot):
        kor = self.pid_kompas2.compute(self.target_angle, robot.sensor.kompas)
        self._apply_motor(robot, 0 - kor, -self.base_speed + kor, -self.base_speed - kor, 0 + kor)
    # DIAGONAL MOVEMENT =====================================================================






    def geser_ke_tengah(self, robot):
        """
        Menggeser robot agar berjarak 265cm dari dinding kanan.
        Toleransi: 262cm - 268cm.
        Murni menggunakan PID Jarak tanpa intervensi kompas.
        Jika sensor = -1, paksa geser ke kanan mencari dinding.
        """
        target_kanan = 265
        jarak = robot.sensor.ultrasonic_kanan
        speed_geser = 0

        # 1. Logika Jarak & PID
        if jarak == -1:
            # Sensor tidak melihat dinding (terlalu jauh ke kiri atau error)
            # Paksa robot geser ke KANAN dengan kecepatan maksimal (45)
            speed_geser = 85 
            
        elif jarak > jarak - 3 and jarak < jarak + 3:
            # Sudah berada di rentang target, hentikan pergeseran
            speed_geser = 0 
            self.pid_jarak.reset()
            return True
            
        else:
            # Hitung kecepatan geser dengan PID Jarak
            # Error positif (terlalu jauh) -> speed positif (Geser Kanan)
            # Error negatif (terlalu dekat) -> speed negatif (Geser Kiri)
            speed_geser = self.pid_jarak.compute(target_kanan, jarak)
            
            # Batasi kecepatan maksimal 45 PWM
            speed_geser = max(-85, min(85, speed_geser))
        
        # 2. Eksekusi ke Motor (Murni Strafe)
        # Formasi Strafe: Kanan = (-m1, +m2, +m3, -m4). Kiri kebalikannya.
        self._apply_motor(robot, 
                          -speed_geser,  speed_geser, 
                           speed_geser, -speed_geser)
    
    def maju_ke_titik(self, robot, target_jarak):
        """Maju ke depan hingga jarak tertentu dari tembok depan"""
        kor_sudut = self.pid_kompas.compute(self.target_angle, robot.sensor.kompas)
        
        # Hitung kecepatan berdasarkan jarak depan
        speed_maju = self.pid_jarak.compute(target_jarak, robot.sensor.jarak_depan)
        speed_maju = max(-45, min(45, speed_maju))
        
        # Rumus Maju + Koreksi Kompas
        self._apply_motor(robot, 
                          speed_maju - kor_sudut, speed_maju + kor_sudut, 
                          speed_maju - kor_sudut, speed_maju + kor_sudut)
    def hadap_sudut(self, robot):
        """Berputar di tempat untuk mengunci sudut tertentu menggunakan PID"""
        kor = self.pid_kompas.compute(self.target_angle, robot.sensor.kompas)

        self._apply_motor(robot, -kor, kor, -kor, kor)


    def naik(self, robot):
        """
        Menggerakkan motor M5 dan M6 untuk mengangkat lifter.
        Pastikan pin M5 dan M6 sudah benar di hardware.
        Target: Menekan tombol lifter di ketinggian tertentu.
        """
        speed = 200 

        robot.motor.m2_pw = speed
        robot.motor.m1_pw = speed
        
    def turun(self, robot):
        """
        Menggerakkan motor M5 dan M6 untuk menurunkan lifter.
        """
        # Kecepatan: Kita set -85 (Putaran Negatif untuk turun)
        speed = -85
        
        robot.motor.m2_pw = speed
        robot.motor.m1_pw = speed
    