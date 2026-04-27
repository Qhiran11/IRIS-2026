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
        self.pid = PIDController()
        self.base_speed = 85 # Sesuai contoh Anda
        self.max_pwm = 120   # Batasan user saat ini
        self.target_angle = 0

    def _apply_motor(self, robot, m1, m2, m3, m4):
        """Helper untuk membatasi PWM dan mengirim ke objek motor"""
        robot.motor.m3_pwm = max(-self.max_pwm, min(self.max_pwm, int(m2)))
        robot.motor.m4_pwm = max(-self.max_pwm, min(self.max_pwm, int(m1)))
        robot.motor.m5_pwm = max(-self.max_pwm, min(self.max_pwm, int(m4)))
        robot.motor.m6_pwm = max(-self.max_pwm, min(self.max_pwm, int(m3)))

    def stop(self, robot):
        self._apply_motor(robot, 0, 0, 0, 0)
        self.pid.reset()

    # --- 10 GERAKAN UTAMA ---

    def maju(self, robot):
        
        kor = self.pid.compute(self.target_angle, robot.sensor.kompas)
        # Sesuai PID.ino: Kanan (m1,m3) = base - kor, Kiri (m2,m4) = base + kor [cite: 36-37]
        self._apply_motor(robot, self.base_speed - kor, self.base_speed + kor, 
                                 self.base_speed - kor, self.base_speed + kor)

    def mundur(self, robot):
        kor = self.pid.compute(self.target_angle, robot.sensor.kompas)
        self._apply_motor(robot, -self.base_speed - kor, -self.base_speed + kor, 
                                 -self.base_speed - kor, -self.base_speed + kor)

    def kanan(self, robot): # Strafe Kanan
        kor = self.pid.compute(self.target_angle, robot.sensor.kompas)
        self._apply_motor(robot, -self.base_speed - kor,  self.base_speed + kor, 
                                  self.base_speed - kor, -self.base_speed + kor)

    def kiri(self, robot): # Strafe Kiri
        kor = self.pid.compute(self.target_angle, robot.sensor.kompas)
        self._apply_motor(robot,  self.base_speed - kor, -self.base_speed + kor, 
                                 -self.base_speed - kor,  self.base_speed + kor)

    def maju_diagonal_kanan(self, robot):
        kor = self.pid.compute(self.target_angle, robot.sensor.kompas)
        self._apply_motor(robot, 0 - kor, self.base_speed + kor, self.base_speed - kor, 0 + kor)

    def maju_diagonal_kiri(self, robot):
        kor = self.pid.compute(self.target_angle, robot.sensor.kompas)
        self._apply_motor(robot, self.base_speed - kor, 0 + kor, 0 - kor, self.base_speed + kor)

    def mundur_diagonal_kanan(self, robot):
        kor = self.pid.compute(self.target_angle, robot.sensor.kompas)
        self._apply_motor(robot, -self.base_speed - kor, 0 + kor, 0 - kor, -self.base_speed + kor)

    def mundur_diagonal_kiri(self, robot):
        kor = self.pid.compute(self.target_angle, robot.sensor.kompas)
        self._apply_motor(robot, 0 - kor, -self.base_speed + kor, -self.base_speed - kor, 0 + kor)

    def putar_kanan(self, robot):
        # Putar tidak menggunakan koreksi PID agar tidak melawan rotasi
        self._apply_motor(robot, -self.base_speed, self.base_speed, -self.base_speed, self.base_speed)

    def putar_kiri(self, robot):
        self._apply_motor(robot, self.base_speed, -self.base_speed, self.base_speed, -self.base_speed)

    def hadap_sudut(self, robot):
        """Berputar di tempat untuk mengunci sudut tertentu menggunakan PID"""
        kor = self.pid.compute(self.target_angle, robot.sensor.kompas)

        self._apply_motor(robot, -kor, kor, -kor, kor)