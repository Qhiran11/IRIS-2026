import time
import os
import json
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


class PIDTwiddleTuner:
    def __init__(self, initial_p, initial_dp, name="tuner"):
        self.name = name
        self.p = list(initial_p)    # [kp_max, kp_min, ki_min, Kd]
        self.dp = list(initial_dp)  # [dkp_max, dkp_min, dki_min, dKd]
        self.best_p = list(initial_p)
        self.best_time = float('inf')
        
        self.current_i = 0
        self.sub_state = "START"  # "START", "AWAITING_ADD_RESULT", "AWAITING_SUB_RESULT"
        self.trial_count = 0
        self.current_candidate = list(initial_p)

    def get_next_candidate(self):
        if self.sub_state == "START":
            self.current_candidate = list(self.p)
        elif self.sub_state == "AWAITING_ADD_RESULT":
            self.current_candidate = list(self.p)
            self.current_candidate[self.current_i] += self.dp[self.current_i]
        elif self.sub_state == "AWAITING_SUB_RESULT":
            self.current_candidate = list(self.p)
            self.current_candidate[self.current_i] -= self.dp[self.current_i]
            
        # Batasi agar nilai PID tidak negatif
        for idx in range(len(self.current_candidate)):
            self.current_candidate[idx] = max(0.0, self.current_candidate[idx])
            
        return self.current_candidate

    def register_result(self, elapsed_time):
        self.trial_count += 1
        candidate = list(self.current_candidate)
        print(f"\n==================================================")
        print(f"[{self.name}] TRIAL #{self.trial_count} SELESAI")
        print(f"Batas Diuji  : kp_max={candidate[0]:.4f}, kp_min={candidate[1]:.4f}, ki_min={candidate[2]:.4f}, Kd={candidate[3]:.4f}")
        print(f"Waktu tempuh  : {elapsed_time:.3f} detik")
        print(f"Waktu terbaik : {self.best_time:.3f} detik")
        print(f"==================================================")
        
        if self.sub_state == "START":
            self.best_time = elapsed_time
            self.best_p = list(candidate)
            self.sub_state = "AWAITING_ADD_RESULT"
            print(f"[{self.name}] Baseline awal diset. Waktu terbaik: {self.best_time:.3f}s. Mulai tuning kp_max...")
            return
            
        i = self.current_i
        param_names = ["kp_max", "kp_min", "ki_min", "Kd"]
        
        if elapsed_time < self.best_time:
            # Ada peningkatan! Simpan nilai baru ini dan perbesar langkah pencarian
            self.best_time = elapsed_time
            self.best_p = list(candidate)
            self.p[i] = candidate[i]
            self.dp[i] *= 1.1
            print(f"[{self.name}] BERHASIL! Ditemukan batas PID lebih cepat: kp_max={self.best_p[0]:.4f}, kp_min={self.best_p[1]:.4f}, ki_min={self.best_p[2]:.4f}, Kd={self.best_p[3]:.4f}")
            print(f"[{self.name}] Memperbesar dp {param_names[i]} menjadi {self.dp[i]:.4f}")
            # Lanjut ke parameter berikutnya
            self.current_i = (self.current_i + 1) % len(self.p)
            self.sub_state = "AWAITING_ADD_RESULT"
        else:
            # Tidak ada peningkatan
            if self.sub_state == "AWAITING_ADD_RESULT":
                # Coba arah sebaliknya (pengurangan)
                self.sub_state = "AWAITING_SUB_RESULT"
                print(f"[{self.name}] Penambahan {param_names[i]} tidak membantu. Mencoba pengurangan...")
            elif self.sub_state == "AWAITING_SUB_RESULT":
                # Kedua arah gagal, kembalikan ke nilai awal, perkecil langkah pencarian
                self.dp[i] *= 0.9
                print(f"[{self.name}] Pengurangan juga tidak membantu. Memperkecil dp {param_names[i]} menjadi {self.dp[i]:.4f}")
                # Lanjut ke parameter berikutnya
                self.current_i = (self.current_i + 1) % len(self.p)
                self.sub_state = "AWAITING_ADD_RESULT"


class GerakanDasar:
    def __init__(self):
        self.pid_kompas = PIDController(Kp=5.0, Ki=0.001, Kd=5.0)
        self.pid_kompas2 = PIDController(Kp=5.0, Ki=0.001, Kd=5.0)
        self.pid_jarak = PIDController(Kp=5.0, Ki=0.001, Kd=5.0) 

        self.pid_tinggi = PIDController(Kp=10.0, Ki=0.0, Kd=0.0)
        self.pid_pitch = PIDController(Kp=4.0, Ki=0.0, Kd=0.0)
        
        # State & tuner auto-tuning
        self.tuners = {}
        self.tuning_states = {}
        self.start_distances = {}
        
        # Tentukan kecepatan maksimal motor (misalnya 255 atau 155 sesuai spesifikasi motor/driver)
        self.base_speed = 100  # Batas minimal PWM saat robot butuh koreksi
        self.max_pwm = 250 

        self.delay = NonBlockingDelay()
         
        self.target_angle = 0
        self.waktu_patokan = 0

        self.stateReturn = "HadapSudut"

        # --- VARIABEL UNTUK FILTER NOISE SENSOR ---
        self.last_valid_jarak_kanan = None
        self.last_valid_jarak_kiri = None
        self.noise_threshold = 50  # Batas maksimal perubahan nilai secara tiba-tiba (cm)
        # Jika nilai lompat lebih dari 5

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
            robot.motor.mDorong2 = -255
        else:
            robot.motor.mDorong1 = 0
            robot.motor.mDorong2 = 0
    
    def turun_ke_titk(self, robot, target_jarak, tun="off"):
        temp_pitch=3
        now = time.time()
            
        jarak_sekarang = robot.sensor.ultrasonic_bawah_tengah
        pitch_sekarang = robot.sensor.pitch_kompas
        
        # 1. Hitung error jarak dan pitch
        error_jarak = jarak_sekarang - target_jarak
        abs_error = abs(error_jarak)
        
        error_pitch = pitch_sekarang - temp_pitch # Menghitung selisih dari patokan 3 derajat
        
        is_tuning = tun in ["on", "ON", "True", True]
        
        if is_tuning:
            is_running_trial = self._handle_tuning(robot, "turun_ke_titik", target_jarak, jarak_sekarang, now, tolerance=1.0)
            if not is_running_trial:
                return False
            tuner = self._get_tuner(robot, "turun_ke_titik")
            candidate = tuner.get_next_candidate()
            kp_max, kp_min, ki_min, Kd = candidate[0], candidate[1], candidate[2], candidate[3]
            
            def map_value(x, in_min, in_max, out_min, out_max):
                x = max(in_min, min(in_max, x))
                return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

            dinamis_Kp = map_value(abs_error, 3, 30, kp_min, kp_max)
            dinamis_Ki = map_value(abs_error, 1, 10, ki_min, 0.0)
            self.pid_tinggi.set_tunings(dinamis_Kp, dinamis_Ki, Kd)
        else:
            use_tuned = False
            if hasattr(robot, 'config') and robot.config.data:
                pid_cfg = robot.config.data.get("pid_values", {}).get("turun_ke_titik")
                if pid_cfg:
                    kp_max = pid_cfg.get("kp_max", 10.0)
                    kp_min = pid_cfg.get("kp_min", 2.0)
                    ki_min = pid_cfg.get("ki_min", 0.09)
                    Kd = pid_cfg.get("Kd", 1.0)
                    
                    def map_value(x, in_min, in_max, out_min, out_max):
                        x = max(in_min, min(in_max, x))
                        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

                    dinamis_Kp = map_value(abs_error, 3, 30, kp_min, kp_max)
                    dinamis_Ki = map_value(abs_error, 1, 10, ki_min, 0.0)
                    self.pid_tinggi.set_tunings(dinamis_Kp, dinamis_Ki, Kd)
                    use_tuned = True
                    
            if not use_tuned:
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
        if not is_tuning:
            if abs_error <= 1 and abs(error_pitch) <= 1:
                robot.motor.mDorong1 = 0
                robot.motor.mDorong2 = 0
                self.pid_tinggi.reset()
                self.pid_pitch.reset()
                return True
            
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
            
    def turun_ke_titk_no_pitch(self, robot, target_jarak, tun="off"):
        now = time.time()
            
        jarak_sekarang = robot.sensor.ultrasonic_bawah_tengah
        
        # 1. Hitung error jarak
        error_jarak = jarak_sekarang - target_jarak
        abs_error = abs(error_jarak)
        
        is_tuning = tun in ["on", "ON", "True", True]
        
        if is_tuning:
            is_running_trial = self._handle_tuning(robot, "turun_ke_titik_no_pitch", target_jarak, jarak_sekarang, now, tolerance=1.0)
            if not is_running_trial:
                return False
            tuner = self._get_tuner(robot, "turun_ke_titik_no_pitch")
            candidate = tuner.get_next_candidate()
            kp_max, kp_min, ki_min, Kd = candidate[0], candidate[1], candidate[2], candidate[3]
            
            def map_value(x, in_min, in_max, out_min, out_max):
                x = max(in_min, min(in_max, x))
                return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

            dinamis_Kp = map_value(abs_error, 3, 30, kp_min, kp_max)
            dinamis_Ki = map_value(abs_error, 1, 10, ki_min, 0.0)
            self.pid_tinggi.set_tunings(dinamis_Kp, dinamis_Ki, Kd)
        else:
            use_tuned = False
            if hasattr(robot, 'config') and robot.config.data:
                pid_cfg = robot.config.data.get("pid_values", {}).get("turun_ke_titik_no_pitch")
                if pid_cfg:
                    kp_max = pid_cfg.get("kp_max", 10.0)
                    kp_min = pid_cfg.get("kp_min", 2.0)
                    ki_min = pid_cfg.get("ki_min", 0.09)
                    Kd = pid_cfg.get("Kd", 1.0)
                    
                    def map_value(x, in_min, in_max, out_min, out_max):
                        x = max(in_min, min(in_max, x))
                        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

                    dinamis_Kp = map_value(abs_error, 3, 30, kp_min, kp_max)
                    dinamis_Ki = map_value(abs_error, 1, 10, ki_min, 0.0)
                    self.pid_tinggi.set_tunings(dinamis_Kp, dinamis_Ki, Kd)
                    use_tuned = True
                    
            if not use_tuned:
                # =========================================================
                # CONTINUOUS ADAPTIVE TUNING (JARAK & WAKTU)
                # =========================================================
                def map_value(x, in_min, in_max, out_min, out_max):
                    x = max(in_min, min(in_max, x))
                    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

                # A. Tuning Kp Berdasarkan Jarak
                dinamis_Kp = map_value(abs_error, 3, 30, 2.0, 10.0)
                
                # B. Tuning Ki Berdasarkan Jarak & Waktu (Mencegah macet 1 menit)
                dinamis_Ki = map_value(abs_error, 1, 10, 0.09, 0.0)
                
                # Terapkan nilai dinamis ke objek PID tinggi
                self.pid_tinggi.set_tunings(dinamis_Kp, dinamis_Ki, 1.0) 
                # =========================================================

        # 2. Toleransi: Berhenti jika masuk range aman (+- 1cm)
        if not is_tuning:
            if abs_error <= 1:
                robot.motor.mDorong1 = 0
                robot.motor.mDorong2 = 0
                self.pid_tinggi.reset()
                return True
            
        # 3. Hitung PID Ketinggian (Menghasilkan Base PWM)
        base_pwm = self.pid_tinggi.compute(target=target_jarak, current=jarak_sekarang)
        
        # 5. NO PITCH MIXING
        pwm_belakang = base_pwm
        pwm_depan = base_pwm
        
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
        if hasattr(self, 'start_distances'):
            self.start_distances.clear()
        

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
        

    def kanan(self, robot): # Strafe Kiri
        robot.state.gerak_dasar_aktif = "KIRI"
        kor = self.pid_kompas.compute(self.target_angle, robot.sensor.kompas)
        self._apply_motor(robot, 
                          -self.base_speed - kor,  self.base_speed - kor, 
                           self.base_speed + kor, -self.base_speed + kor)
        

    def kiri(self, robot): # Strafe Kanan
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

    def _get_tuner(self, robot, func_name):
        if func_name not in self.tuners:
            # Muat parameter PID dari config jika ada, atau gunakan default
            pid_cfg = None
            if hasattr(robot, 'config') and robot.config.data:
                pid_cfg = robot.config.data.get("pid_values", {}).get(func_name)
            
            if pid_cfg is None:
                if func_name == "maju_ke_titik":
                    initial_p = [6.0, 1.1, 0.1, 1.0]
                    initial_dp = [1.0, 0.2, 0.02, 0.2]
                elif func_name == "mundur_ke_titik":
                    initial_p = [6.0, 2.0, 0.1, 1.0]
                    initial_dp = [1.0, 0.3, 0.02, 0.2]
                elif func_name == "geser_ke_titik_kanan":
                    initial_p = [5.0, 1.0, 1.5, 1.0]
                    initial_dp = [1.0, 0.2, 0.1, 0.2]
                elif func_name == "geser_ke_titik_kiri":
                    initial_p = [10.0, 1.0, 0.2, 1.0]
                    initial_dp = [1.0, 0.2, 0.03, 0.2]
                elif func_name in ["turun_ke_titik", "turun_ke_titik_no_pitch"]:
                    initial_p = [10.0, 2.0, 0.09, 1.0]
                    initial_dp = [1.0, 0.3, 0.02, 0.2]
                else:
                    initial_p = [5.0, 1.0, 0.1, 1.0]
                    initial_dp = [1.0, 0.2, 0.02, 0.2]
            else:
                initial_p = [
                    pid_cfg.get("kp_max", 8.0),
                    pid_cfg.get("kp_min", 1.1),
                    pid_cfg.get("ki_min", 0.1),
                    pid_cfg.get("Kd", 1.0)
                ]
                if func_name == "geser_ke_titik_kanan":
                    initial_dp = [1.5, 0.3, 0.3, 0.3]
                elif func_name == "geser_ke_titik_kiri":
                    initial_dp = [2.5, 0.3, 0.06, 0.3]
                elif func_name in ["turun_ke_titik", "turun_ke_titik_no_pitch"]:
                    initial_dp = [2.5, 0.5, 0.03, 0.3]
                else:
                    initial_dp = [2.0, 0.5, 0.05, 0.3]
                
            self.tuners[func_name] = PIDTwiddleTuner(initial_p, initial_dp, name=func_name)
        return self.tuners[func_name]

    def _handle_tuning(self, robot, func_name, target_jarak, jarak_sekarang, now, tolerance=1.0):
        tuner = self._get_tuner(robot, func_name)
        
        if func_name not in self.tuning_states:
            self.tuning_states[func_name] = {
                "state": "IDLE", # "IDLE", "RUNNING", "WAITING_FOR_RESET"
                "start_time": None,
                "approach_start_time": None,
                "reset_detect_time": None,
                "waktu_patokan": None,
                "prev_error": None,
                "prev_time": None
            }
            
        t_state = self.tuning_states[func_name]
        abs_error = abs(jarak_sekarang - target_jarak)
        
        # Tentukan jarak ketika robot dianggap mulai mendekati target
        # Roda: 15 cm, Tinggi (lifter): 5 cm
        approach_threshold = 5.0 if func_name in ["turun_ke_titik", "turun_ke_titik_no_pitch"] else 15.0
        
        if t_state["state"] == "IDLE":
            if abs_error > 15.0:
                t_state["state"] = "RUNNING"
                t_state["start_time"] = now
                t_state["approach_start_time"] = None
                t_state["waktu_patokan"] = None
                t_state["prev_error"] = abs_error
                t_state["prev_time"] = now
                print(f"\n[TUNING {func_name}] Memulai Uji Coba #{tuner.trial_count + 1}...")
                candidate = tuner.get_next_candidate()
                print(f"[TUNING {func_name}] Mencoba Batas PID: kp_max={candidate[0]:.4f}, kp_min={candidate[1]:.4f}, ki_min={candidate[2]:.4f}, Kd={candidate[3]:.4f}")
            else:
                t_state["state"] = "WAITING_FOR_RESET"
                t_state["reset_detect_time"] = None
                print(f"\n[TUNING {func_name}] Robot terlalu dekat dengan target ({jarak_sekarang:.1f} cm vs target {target_jarak} cm).")
                print(f"[TUNING {func_name}] Silakan mundurkan robot (> 15 cm error) untuk mulai.")
                
        elif t_state["state"] == "WAITING_FOR_RESET":
            self.stop(robot)
            if abs_error > 15.0:
                if t_state["reset_detect_time"] is None:
                    t_state["reset_detect_time"] = now
                elif now - t_state["reset_detect_time"] > 1.5:
                    t_state["state"] = "RUNNING"
                    t_state["start_time"] = now
                    t_state["approach_start_time"] = None
                    t_state["waktu_patokan"] = None
                    t_state["reset_detect_time"] = None
                    print(f"\n[TUNING {func_name}] Memulai Uji Coba #{tuner.trial_count + 1}...")
                    candidate = tuner.get_next_candidate()
                    print(f"[TUNING {func_name}] Mencoba Batas PID: kp_max={candidate[0]:.4f}, kp_min={candidate[1]:.4f}, ki_min={candidate[2]:.4f}, Kd={candidate[3]:.4f}")
            else:
                t_state["reset_detect_time"] = None
                
        elif t_state["state"] == "RUNNING":
            # Deteksi ketika robot mulai masuk area mendekati target
            if t_state["approach_start_time"] is None and abs_error <= approach_threshold:
                t_state["approach_start_time"] = now
                print(f"[TUNING {func_name}] Robot mendekati target (jarak: {jarak_sekarang:.1f} cm, error <= {approach_threshold} cm). Memulai perhitungan waktu...")
                
            elapsed = now - t_state["start_time"]
            if elapsed > 10.0:
                print(f"[TUNING {func_name}] Timeout! Uji coba #{tuner.trial_count + 1} gagal (waktu total melebihi 10 detik).")
                tuner.register_result(99.0)
                self._save_pid_to_config(robot, func_name, tuner.best_p)
                t_state["state"] = "WAITING_FOR_RESET"
                t_state["reset_detect_time"] = None
                t_state["approach_start_time"] = None
                self.stop(robot)
            elif abs_error <= tolerance:
                if t_state["waktu_patokan"] is None:
                    t_state["waktu_patokan"] = now
                elif now - t_state["waktu_patokan"] > 0.1:
                    # Sukses mencapai target
                    # Hitung waktu dari sejak mulai mendekati target
                    if t_state["approach_start_time"] is not None:
                        waktu_hitung = now - t_state["approach_start_time"]
                        # Kurangi 0.1s waktu patokan stabil agar pengukuran murni waktu tempuh mendekati target
                        waktu_hitung = max(0.0, waktu_hitung - 0.1)
                    else:
                        # Jika dari awal sudah di dalam zona, ukur dari total waktu berjalan
                        waktu_hitung = max(0.0, (now - t_state["start_time"]) - 0.1)
                        
                    tuner.register_result(waktu_hitung)
                    self._save_pid_to_config(robot, func_name, tuner.best_p)
                    t_state["state"] = "WAITING_FOR_RESET"
                    t_state["reset_detect_time"] = None
                    t_state["waktu_patokan"] = None
                    t_state["approach_start_time"] = None
                    self.stop(robot)
            else:
                t_state["waktu_patokan"] = None
                
        return t_state["state"] == "RUNNING"

    def _save_pid_to_config(self, robot, func_name, best_p):
        if hasattr(robot, 'config') and robot.config.data is not None:
            if "pid_values" not in robot.config.data:
                robot.config.data["pid_values"] = {}
            robot.config.data["pid_values"][func_name] = {
                "kp_max": round(best_p[0], 4),
                "kp_min": round(best_p[1], 4),
                "ki_min": round(best_p[2], 4),
                "ki_max": 0.0,
                "Kd": round(best_p[3], 4)
            }
            robot.config.save_config()

    def maju_ke_titik(self, robot, target_jarak, now, tun="off"):
        robot.state.gerak_dasar_aktif = "MAJU KE TITIK"
        jarak_sekarang = robot.sensor.ultrasonic_depan

        # Antisipasi jika sensor membaca error atau di luar jangkauan
        if jarak_sekarang <= 0 or jarak_sekarang == -1:
            return False
            
        abs_error = abs(jarak_sekarang - target_jarak)
        
        is_tuning = tun in ["on", "ON", "True", True]
        
        if is_tuning:
            is_running_trial = self._handle_tuning(robot, "maju_ke_titik", target_jarak, jarak_sekarang, now, tolerance=1.0)
            if not is_running_trial:
                return False
            tuner = self._get_tuner(robot, "maju_ke_titik")
            candidate = tuner.get_next_candidate()
            kp_max, kp_min, ki_min, Kd = candidate[0], candidate[1], candidate[2], candidate[3]
            dinamis_Kp = self._map_value(abs_error, 5, 30, kp_min, kp_max)
            dinamis_Ki = self._map_value(abs_error, 1, 10, ki_min, 0.0)
            self.pid_jarak.set_tunings(dinamis_Kp, dinamis_Ki, Kd)
        else:
            use_tuned = False
            if hasattr(robot, 'config') and robot.config.data:
                pid_cfg = robot.config.data.get("pid_values", {}).get("maju_ke_titik")
                if pid_cfg:
                    kp_max = pid_cfg.get("kp_max", 8.0)
                    kp_min = pid_cfg.get("kp_min", 1.1)
                    ki_min = pid_cfg.get("ki_min", 0.1)
                    Kd = pid_cfg.get("Kd", 1.0)
                    
                    dinamis_Kp = self._map_value(abs_error, 5, 30, kp_min, kp_max)
                    dinamis_Ki = self._map_value(abs_error, 1, 10, ki_min, 0.0)
                    self.pid_jarak.set_tunings(dinamis_Kp, dinamis_Ki, Kd)
                    use_tuned = True
            
            if not use_tuned:
                # --- ADAPTIVE TUNING PID JARAK ---
                # Kp: Saat sisa 30cm, Kp agresif (misal 8.0). Saat sisa 5cm, Kp mengecil (misal 3.0)
                dinamis_Kp = self._map_value(abs_error, 5, 30, 1.1, 8.0)
                # Ki: Aktif menendang gesekan hanya saat jarak < 10cm
                dinamis_Ki = self._map_value(abs_error, 1, 10, 0.1, 0.0)
                self.pid_jarak.set_tunings(dinamis_Kp, dinamis_Ki, self.pid_jarak.Kd)
                # ---------------------------------

        # Batasi kecepatan maksimal secara dinamis mendekati target (berlaku untuk semua jarak)
        current_limit = self.base_speed
        if abs_error <= 30.0:
            current_limit = self._map_value(abs_error, 3, 30, 20, self.base_speed)

        kor_sudut = self.pid_kompas2.compute(self.target_angle, robot.sensor.kompas)
        speed_jarak = self.pid_jarak.compute(target_jarak, jarak_sekarang)

        # Batasi output PID sesuai base_speed dinamis
        speed_jarak = max(-current_limit, min(current_limit, speed_jarak))

        self._apply_motor(
            robot,
            speed_jarak - kor_sudut,
            speed_jarak - kor_sudut,
            speed_jarak + kor_sudut,
            speed_jarak + kor_sudut
        )

        if not is_tuning:
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
 


    def geser_ke_titik_kanan(self, robot, target_jarak, now, tun="off"):
        robot.state.gerak_dasar_aktif = "geser ke titik kanan"
        jarak_sekarang = robot.sensor.ultrasonic_kanan

        if jarak_sekarang > target_jarak + 50 and target_jarak > 200:
            speed_geser = 30
            self.stop(robot)

        if jarak_sekarang <= 0:
            self.stop(robot)
            speed_geser = 0
        
        else:
            abs_error = abs(jarak_sekarang - target_jarak)
            
            is_tuning = tun in ["on", "ON", "True", True]
            
            if is_tuning:
                is_running_trial = self._handle_tuning(robot, "geser_ke_titik_kanan", target_jarak, jarak_sekarang, now, tolerance=2.0)
                if not is_running_trial:
                    return False
                tuner = self._get_tuner(robot, "geser_ke_titik_kanan")
                candidate = tuner.get_next_candidate()
                kp_max, kp_min, ki_min, Kd = candidate[0], candidate[1], candidate[2], candidate[3]
                dinamis_Kp = self._map_value(abs_error, 5, 30, kp_min, kp_max)
                dinamis_Ki = self._map_value(abs_error, 1, 10, ki_min, 0.0)
                self.pid_jarak.set_tunings(dinamis_Kp, dinamis_Ki, Kd)
            else:
                use_tuned = False
                if hasattr(robot, 'config') and robot.config.data:
                    pid_cfg = robot.config.data.get("pid_values", {}).get("geser_ke_titik_kanan")
                    if pid_cfg:
                        kp_max = pid_cfg.get("kp_max", 5.0)
                        kp_min = pid_cfg.get("kp_min", 1.0)
                        ki_min = pid_cfg.get("ki_min", 1.5)
                        Kd = pid_cfg.get("Kd", 1.0)
                        
                        dinamis_Kp = self._map_value(abs_error, 5, 30, kp_min, kp_max)
                        dinamis_Ki = self._map_value(abs_error, 1, 10, ki_min, 0.0)
                        self.pid_jarak.set_tunings(dinamis_Kp, dinamis_Ki, Kd)
                        use_tuned = True
                
                if not use_tuned:
                    # --- ADAPTIVE TUNING PID JARAK ---
                    dinamis_Kp = self._map_value(abs_error, 5, 30, 1.0, 5.0) 
                    dinamis_Ki = self._map_value(abs_error, 1, 10, 1.5, 0.0)
                    self.pid_jarak.set_tunings(dinamis_Kp, dinamis_Ki, self.pid_jarak.Kd)
                    # ---------------------------------
            
            speed_geser = self.pid_jarak.compute(target_jarak, jarak_sekarang)
            
        # Batasi kecepatan maksimal secara dinamis mendekati target (berlaku untuk semua jarak)
        current_limit = self.base_speed
        if jarak_sekarang > 0:
            abs_error = abs(jarak_sekarang - target_jarak)
            if abs_error <= 30.0:
                current_limit = self._map_value(abs_error, 3, 30, 20, self.base_speed)

        kor_sudut = self.pid_kompas2.compute(self.target_angle, robot.sensor.kompas)
        speed_geser = max(-current_limit, min(current_limit, speed_geser))
        
        self._apply_motor(robot, 
                          -speed_geser - kor_sudut,  speed_geser - kor_sudut, 
                           speed_geser + kor_sudut, -speed_geser + kor_sudut)
                           
        if not is_tuning:
            if target_jarak - 2 <= jarak_sekarang <= target_jarak + 2:
                self.stop(robot)
                if getattr(self, 'waktu_patokan', None) is None:
                    self.waktu_patokan = now
                if now - self.waktu_patokan > 0.05:
                    self.waktu_patokan = None  
                    self.pid_jarak.reset()
                    self.pid_kompas2.reset()
                    self.last_valid_jarak_kanan = None  # <--- SANGAT PENTING: Reset memori filter
                    return True
            else:
                self.waktu_patokan = None
            
        return False
    
    
    def geser_ke_titik_kiri(self, robot, target_jarak, now, tun="off"):
        robot.state.gerak_dasar_aktif = "geser ke titik kiri"
        jarak_sekarang = robot.sensor.ultrasonic_kiri
        
        # ====================================================
        # NOISE FILTER (OUTLIER REJECTION)
        # ====================================================
        if jarak_sekarang <= 0 or jarak_sekarang == -1:
            if self.last_valid_jarak_kiri is not None:
                jarak_sekarang = self.last_valid_jarak_kiri

        if self.last_valid_jarak_kiri is not None:
            if abs(jarak_sekarang - self.last_valid_jarak_kiri) > self.noise_threshold:
                # Abaikan nilai noise (buang), tetap gunakan nilai terakhir yang masuk akal
                jarak_sekarang = self.last_valid_jarak_kiri
            else:
                self.last_valid_jarak_kiri = jarak_sekarang
        else:
            if jarak_sekarang > 0:
                self.last_valid_jarak_kiri = jarak_sekarang
        # ====================================================

        # Karena sudah difilter di atas, kita bisa lebih aman menggunakan jarak_sekarang
        if jarak_sekarang <= 0 or jarak_sekarang == -1:
            self.kiri(robot)
            return False
            
        abs_error = abs(jarak_sekarang - target_jarak)
        
        is_tuning = tun in ["on", "ON", "True", True]
        
        if is_tuning:
            is_running_trial = self._handle_tuning(robot, "geser_ke_titik_kiri", target_jarak, jarak_sekarang, now, tolerance=2.0)
            if not is_running_trial:
                return False
            tuner = self._get_tuner(robot, "geser_ke_titik_kiri")
            candidate = tuner.get_next_candidate()
            kp_max, kp_min, ki_min, Kd = candidate[0], candidate[1], candidate[2], candidate[3]
            dinamis_Kp = self._map_value(abs_error, 5, 30, kp_min, kp_max)
            dinamis_Ki = self._map_value(abs_error, 1, 10, ki_min, 0.0)
            self.pid_jarak.set_tunings(dinamis_Kp, dinamis_Ki, Kd)
        else:
            use_tuned = False
            if hasattr(robot, 'config') and robot.config.data:
                pid_cfg = robot.config.data.get("pid_values", {}).get("geser_ke_titik_kiri")
                if pid_cfg:
                    kp_max = pid_cfg.get("kp_max", 10.0)
                    kp_min = pid_cfg.get("kp_min", 1.0)
                    ki_min = pid_cfg.get("ki_min", 0.2)
                    Kd = pid_cfg.get("Kd", 1.0)
                    
                    dinamis_Kp = self._map_value(abs_error, 5, 30, kp_min, kp_max)
                    dinamis_Ki = self._map_value(abs_error, 1, 10, ki_min, 0.0)
                    self.pid_jarak.set_tunings(dinamis_Kp, dinamis_Ki, Kd)
                    use_tuned = True
            
            if not use_tuned:
                # --- ADAPTIVE TUNING PID JARAK ---
                dinamis_Kp = self._map_value(abs_error, 5, 30, 1.0, 10.0)
                dinamis_Ki = self._map_value(abs_error, 1, 10, 0.2, 0.0)
                self.pid_jarak.set_tunings(dinamis_Kp, dinamis_Ki, self.pid_jarak.Kd)
                # ---------------------------------

        # Batasi kecepatan maksimal secara dinamis mendekati target (berlaku untuk semua jarak)
        current_limit = self.base_speed
        if abs_error <= 30.0:
            current_limit = self._map_value(abs_error, 3, 30, 20, self.base_speed)

        kor_sudut = self.pid_kompas2.compute(self.target_angle, robot.sensor.kompas)
        speed_geser = self.pid_jarak.compute(target_jarak, jarak_sekarang)
            
        speed_geser = max(-current_limit, min(current_limit, speed_geser))
        
        # Eksekusi motor
        self._apply_motor(robot, 
                          speed_geser - kor_sudut,  -speed_geser - kor_sudut, 
                         -speed_geser + kor_sudut,   speed_geser + kor_sudut)
                          
        if not is_tuning:
            if target_jarak - 2 <= jarak_sekarang <= target_jarak + 2:
                self.stop(robot)
                if getattr(self, 'waktu_patokan', None) is None:
                    self.waktu_patokan = now
                if now - self.waktu_patokan > 0.1:
                    self.waktu_patokan = None
                    self.pid_jarak.reset()
                    self.pid_kompas2.reset()
                    self.last_valid_jarak_kiri = None  # <--- SANGAT PENTING: Reset memori filter
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
    def turun_roda1(self, robot):
        jarak_sekarang = robot.sensor.ultrasonic_bawah_depan
        jarak_target = 9
    
        if jarak_sekarang <= jarak_target:
            # Jika sudah sampai atau melewati target, berhenti
            robot.motor.mDorong2 = 0
            return True
        else:
            selisih_jarak = jarak_sekarang - jarak_target
            faktor_pengali = 10 
            kecepatan_hitung = -5 - (selisih_jarak * faktor_pengali)
            if kecepatan_hitung < -255:
                kecepatan_hitung = -255
            
            robot.motor.mDorong2 = kecepatan_hitung
            return False
            
    def turun_roda2(self, robot):
        jarak_sekarang = robot.sensor.ultrasonic_bawah_belakang
        jarak_target = 9
    
        if jarak_sekarang <= jarak_target:
            # Jika sudah sampai atau melewati target, berhenti
            robot.motor.mDorong1 = 0
            return True
        else:
            selisih_jarak = jarak_sekarang - jarak_target
            faktor_pengali = 10 
            kecepatan_hitung = -10 - (selisih_jarak * faktor_pengali)
            if kecepatan_hitung < -245:
                kecepatan_hitung = -245
            
            robot.motor.mDorong1 = kecepatan_hitung
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
            
            if self.turun_ke_titk(robot, 5):
                self.stop(robot)
                self.stateReturn = "MundurKetitik"

        elif self.stateReturn == "MundurKetitik":
            self.base_speed = 40
            self.max_pwm = 50
            if self.mundur_ke_titik(robot, 10, now):
                self.stop(robot)
                self.stateReturn = "geser ke titik kiri"
               
        elif self.stateReturn == "geser ke titik kiri":
            if self.geser_ke_titik_kiri(robot, 57, now):
                self.stop(robot)
                self.stateReturn = "HadapSudut"
                return True 
        return False
        
