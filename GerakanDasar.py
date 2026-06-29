import json
import os
import time


class PIDController:

    def __init__(self, Kp=8.0, Ki=0.001, Kd=15.0):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.prev_error = 0
        self.integral = 0

    def compute(self, target, current):
        error = current - target
        if error > 180:
            error -= 360
        if error < -180:
            error += 360

        self.integral += error
        self.integral = max(
            -500, min(500, self.integral)
        )  # Anti Anti-Windup Clamping
        derivative = error - self.prev_error
        output = (
            (self.Kp * error) + (self.Ki * self.integral) + (self.Kd * derivative)
        )
        self.prev_error = error
        return output

    def reset(self):
        self.prev_error = 0
        self.integral = 0

    def set_tunings(self, Kp, Ki, Kd):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd


class GerakanDasar:

    def __init__(self, config_path="config.json"):
        self.config_path = config_path

        # Inisialisasi PID awal default
        self.pid_kompas = PIDController(Kp=5.0, Ki=0.001, Kd=5.0)
        self.pid_kompas2 = PIDController(Kp=5.0, Ki=0.001, Kd=5.0)
        self.pid_jarak = PIDController(Kp=5.0, Ki=0.05, Kd=1.0)
        self.pid_tinggi = PIDController(Kp=10.0, Ki=0.0, Kd=0.0)
        self.pid_pitch = PIDController(Kp=4.0, Ki=0.0, Kd=0.0)

        # Base parameters
        self.base_speed = 100
        self.max_pwm = 250
        

        self.target_angle = 0
        self.waktu_patokan = None
        self.stateReturn = "HadapSudut"

        # Variabel Filter Noise
        self.last_valid_jarak_kanan = None
        self.last_valid_jarak_kiri = None
        self.noise_threshold = 50

        # --- VARIABEL PELACAK WAKTU AUTO-TUNING ---
        self.waktu_mulai_gerak = None
        self.gerakan_sebelumnya = None

        # Muat konfigurasi dari JSON jika tersedia
        self.load_config_json()

    def load_config_json(self):
        """Memuat parameter PID dari JSON tanpa menghapus data lain."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    self.config_data = json.load(f)
                print(f"[CONFIG] Berhasil memuat konfigurasi dari {self.config_path}")
                
                # Cek apakah blok "auto_tuning_pid" sudah ada di config.json
                # Jika belum, tambahkan blok defaultnya
                if "auto_tuning_pid" not in self.config_data:
                    self.config_data["auto_tuning_pid"] = self._get_default_tuning()
                    self.save_config_json()
                    
            except Exception as e:
                print(f"[CONFIG] Gagal membaca JSON: {e}")
                # Jangan langsung overwrite jika gagal baca (mungkin format JSON error)
        else:
            # Jika file benar-benar tidak ada
            self.config_data = {
                "auto_tuning_pid": self._get_default_tuning()
            }
            self.save_config_json()

    def _get_default_tuning(self):
        """Mengembalikan nilai default untuk auto-tuning."""
        return {
            "maju_ke_titik": {"kp_max": 8.0, "kp_min": 1.1, "ki_max": 0.0, "ki_min": 0.1},
            "mundur_ke_titik": {"kp_max": 8.0, "kp_min": 2.0, "ki_max": 0.0, "ki_min": 0.1},
            "geser_ke_titik_kanan": {"kp_max": 5.0, "kp_min": 1.0, "ki_max": 0.0, "ki_min": 1.5},
            "geser_ke_titik_kiri": {"kp_max": 10.0, "kp_min": 1.0, "ki_max": 0.0, "ki_min": 0.2}
        }

    def save_config_json(self):
        """Menyimpan keseluruhan file JSON dengan aman."""
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config_data, f, indent=4)
            print(f"[AUTO-TUNING] File {self.config_path} berhasil diperbarui!")
        except Exception as e:
            print(f"[AUTO-TUNING] Gagal menyimpan file JSON: {e}")

    
    
    def _generate_default_config(self):
        """Membuat struktur default jika file JSON belum ada."""
        self.config_data = {
            "maju_ke_titik": {
                "kp_max": 8.0,
                "kp_min": 1.1,
                "ki_max": 0.0,
                "ki_min": 0.1,
            },
            "mundur_ke_titik": {
                "kp_max": 8.0,
                "kp_min": 2.0,
                "ki_max": 0.0,
                "ki_min": 0.1,
            },
            "geser_ke_titik_kanan": {
                "kp_max": 5.0,
                "kp_min": 1.0,
                "ki_max": 0.0,
                "ki_min": 1.5,
            },
            "geser_ke_titik_kiri": {
                "kp_max": 10.0,
                "kp_min": 1.0,
                "ki_max": 0.0,
                "ki_min": 0.2,
            },
        }
        self.save_config_json()

    def save_config_json(self):
        """Menulis ulang seluruh isi file JSON dengan parameter PID terbaru."""
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config_data, f, indent=4)
            print(f"[AUTO-TUNING] File {self.config_path} berhasil diperbarui!")
        except Exception as e:
            print(f"[AUTO-TUNING] Gagal menyimpan file JSON: {e}")

    def _map_value(self, x, in_min, in_max, out_min, out_max):
        x = max(in_min, min(in_max, x))
        return (x - in_min) * (out_max - out_min) / (
            in_max - in_min
        ) + out_min

    def _manage_time_tracker(self, nama_gerak, now):
        """Helper untuk mengatur pencatatan waktu awal gerakan secara non-blocking."""
        if (
            self.gerakan_sebelumnya != nama_gerak
            or self.waktu_mulai_gerak is None
        ):
            self.waktu_mulai_gerak = now
            self.gerakan_sebelumnya = nama_gerak

    def _apply_motor(self, robot, FL, FR, BL, BR):
        FL_val = max(-self.max_pwm, min(self.max_pwm, int(FL)))
        FR_val = max(-self.max_pwm, min(self.max_pwm, int(FR)))
        BL_val = max(-self.max_pwm, min(self.max_pwm, int(BL)))
        BR_val = max(-self.max_pwm, min(self.max_pwm, int(BR)))

        robot.motor.m1_pwm = FL_val
        robot.motor.m0_pwm = FR_val
        robot.motor.m3_pwm = BL_val
        robot.motor.m2_pwm = BR_val

    def stop(self, robot):
        robot.state.gerak_dasar_aktif = "STOP"
        self.stop_motors(robot)
        self.waktu_mulai_gerak = None

    def stop_motors(self, robot):
        self._apply_motor(robot, 0, 0, 0, 0)
        robot.motor.mDorong1 = 0
        robot.motor.mDorong2 = 0
        self.pid_kompas.reset()
        self.pid_kompas2.reset()
        self.pid_jarak.reset()

    # =========================================================================
    # SINKRONISASI GERAKAN MENUGU TITIK DENGAN AUTO-TUNING BERBASIS JSON
    # =========================================================================

    def maju_ke_titik(self, robot, target_jarak, now):
        robot.state.gerak_dasar_aktif = "MAJU KE TITIK"
        jarak_sekarang = robot.sensor.ultrasonic_depan

        if jarak_sekarang <= 0 or jarak_sekarang == -1:
            return False

        self._manage_time_tracker("maju_ke_titik", now)
        abs_error = abs(jarak_sekarang - target_jarak)

        # Ambil batasan parameter dari data JSON
        p = self.config_data["auto_tuning_pid"]["maju_ke_titik"]
        dinamis_Kp = self._map_value(abs_error, 5, 30, p["kp_min"], p["kp_max"])
        dinamis_Ki = self._map_value(abs_error, 1, 10, p["ki_min"], p["ki_max"])

        self.pid_jarak.set_tunings(dinamis_Kp, dinamis_Ki, self.pid_jarak.Kd)

        kor_sudut = self.pid_kompas2.compute(
            self.target_angle, robot.sensor.kompas
        )
        speed_jarak = self.pid_jarak.compute(target_jarak, jarak_sekarang)
        speed_jarak = max(-self.base_speed, min(self.base_speed, speed_jarak))

        self._apply_motor(
            robot,
            speed_jarak - kor_sudut,
            speed_jarak - kor_sudut,
            speed_jarak + kor_sudut,
            speed_jarak + kor_sudut,
        )

        if target_jarak - 1 <= jarak_sekarang <= target_jarak + 1:
            self.stop_motors(robot)
            if self.waktu_patokan is None:
                self.waktu_patokan = now
            if now - self.waktu_patokan > 0.1:
                settle_time = now - self.waktu_mulai_gerak
                print(
                    f"[TUNING] Maju Ke Titik Selesai! Settle Time: {settle_time:.3f} s"
                )

                # Logika Optimasi Otomatis (Contoh penyempurnaan adaptif)
                if settle_time > 1.5:  # Jika terlalu lambat, naikkan Kp Max
                    self.config_data["auto_tuning_pid"]["maju_ke_titik"]["kp_max"] = min(
                        12.0, p["kp_max"] + 0.2
                    )
                    self.save_config_json()

                self.stop(robot)
                self.waktu_patokan = None
                return True
        else:
            self.waktu_patokan = None
        return False

    def mundur_ke_titik(self, robot, target_jarak, now):
        robot.state.gerak_dasar_aktif = "MUNDUR KE TITIK"
        jarak_sekarang = robot.sensor.ultrasonic_belakang

        if jarak_sekarang <= 0 or jarak_sekarang == -1:
            self._apply_motor(
                robot,
                -self.base_speed,
                -self.base_speed,
                self.base_speed,
                self.base_speed,
            )
            return False

        self._manage_time_tracker("mundur_ke_titik", now)
        abs_error = abs(jarak_sekarang - target_jarak)

        p = self.config_data["auto_tuning_pid"]["mundur_ke_titik"]
        dinamis_Kp = self._map_value(abs_error, 5, 30, p["kp_min"], p["kp_max"])
        dinamis_Ki = self._map_value(abs_error, 1, 10, p["ki_min"], p["ki_max"])

        self.pid_jarak.set_tunings(dinamis_Kp, dinamis_Ki, self.pid_jarak.Kd)

        kor_sudut = self.pid_kompas2.compute(
            self.target_angle, robot.sensor.kompas
        )
        speed_jarak = self.pid_jarak.compute(target_jarak, jarak_sekarang)
        speed_jarak = max(-self.base_speed, min(self.base_speed, speed_jarak))

        self._apply_motor(
            robot,
            -speed_jarak - kor_sudut,
            -speed_jarak - kor_sudut,
            -speed_jarak + kor_sudut,
            -speed_jarak + kor_sudut,
        )

        if target_jarak - 1 <= jarak_sekarang <= target_jarak + 1:
            self.stop_motors(robot)
            if self.waktu_patokan is None:
                self.waktu_patokan = now
            if now - self.waktu_patokan > 0.1:
                settle_time = now - self.waktu_mulai_gerak
                print(
                    f"[TUNING] Mundur Ke Titik Selesai! Settle Time: {settle_time:.3f} s"
                )

                if settle_time > 1.5:
                    self.config_data["auto_tuning_pid"]["mundur_ke_titik"]["kp_max"] = min(
                        12.0, p["kp_max"] + 0.2
                    )
                    self.save_config_json()

                self.stop(robot)
                self.waktu_patokan = None
                return True
        else:
            self.waktu_patokan = None
        return False

    def geser_ke_titik_kanan(self, robot, target_jarak, now):
        robot.state.gerak_dasar_aktif = "geser ke titik kanan"
        jarak_sekarang = robot.sensor.ultrasonic_kanan

        if jarak_sekarang <= 0 or jarak_sekarang == -1:
            return False

        self._manage_time_tracker("geser_ke_titik_kanan", now)
        abs_error = abs(jarak_sekarang - target_jarak)

        p = self.config_data["auto_tuning_pid"]["geser_ke_titik_kanan"]
        dinamis_Kp = self._map_value(abs_error, 5, 30, p["kp_min"], p["kp_max"])
        dinamis_Ki = self._map_value(abs_error, 1, 10, p["ki_min"], p["ki_max"])

        self.pid_jarak.set_tunings(dinamis_Kp, dinamis_Ki, self.pid_jarak.Kd)
        speed_geser = self.pid_jarak.compute(target_jarak, jarak_sekarang)

        kor_sudut = self.pid_kompas2.compute(
            self.target_angle, robot.sensor.kompas
        )
        speed_geser = max(-self.base_speed, min(self.base_speed, speed_geser))

        self._apply_motor(
            robot,
            -speed_geser - kor_sudut,
            speed_geser - kor_sudut,
            speed_geser + kor_sudut,
            -speed_geser + kor_sudut,
        )

        if target_jarak - 2 <= jarak_sekarang <= target_jarak + 2:
            self.stop_motors(robot)
            if self.waktu_patokan is None:
                self.waktu_patokan = now
            if now - self.waktu_patokan > 0.05:
                settle_time = now - self.waktu_mulai_gerak
                print(
                    f"[TUNING] Geser Kanan Selesai! Settle Time: {settle_time:.3f} s"
                )

                if settle_time > 1.8:
                    self.config_data["auto_tuning_pid"]["geser_ke_titik_kanan"]["kp_max"] = min(
                        10.0, p["kp_max"] + 0.3
                    )
                    self.save_config_json()

                self.stop(robot)
                self.waktu_patokan = None
                self.last_valid_jarak_kanan = None
                return True
        else:
            self.waktu_patokan = None
        return False

    def geser_ke_titik_kiri(self, robot, target_jarak, now):
        robot.state.gerak_dasar_aktif = "geser ke titik kiri"
        jarak_sekarang = robot.sensor.ultrasonic_kiri

        # Outlier noise rejection filter
        if jarak_sekarang <= 0 or jarak_sekarang == -1:
            if self.last_valid_jarak_kiri is not None:
                jarak_sekarang = self.last_valid_jarak_kiri

        if self.last_valid_jarak_kiri is not None:
            if (
                abs(jarak_sekarang - self.last_valid_jarak_kiri)
                > self.noise_threshold
            ):
                jarak_sekarang = self.last_valid_jarak_kiri
            else:
                self.last_valid_jarak_kiri = jarak_sekarang
        else:
            if jarak_sekarang > 0:
                self.last_valid_jarak_kiri = jarak_sekarang

        if jarak_sekarang <= 0 or jarak_sekarang == -1:
            return False

        self._manage_time_tracker("geser_ke_titik_kiri", now)
        abs_error = abs(jarak_sekarang - target_jarak)

        p = self.config_data["auto_tuning_pid"]["geser_ke_titik_kiri"]
        dinamis_Kp = self._map_value(abs_error, 5, 30, p["kp_min"], p["kp_max"])
        dinamis_Ki = self._map_value(abs_error, 1, 10, p["ki_min"], p["ki_max"])

        self.pid_jarak.set_tunings(dinamis_Kp, dinamis_Ki, self.pid_jarak.Kd)
        speed_geser = self.pid_jarak.compute(target_jarak, jarak_sekarang)

        kor_sudut = self.pid_kompas2.compute(
            self.target_angle, robot.sensor.kompas
        )
        speed_geser = max(-self.base_speed, min(self.base_speed, speed_geser))

        self._apply_motor(
            robot,
            speed_geser - kor_sudut,
            -speed_geser - kor_sudut,
            -speed_geser + kor_sudut,
            speed_geser + kor_sudut,
        )

        if target_jarak - 2 <= jarak_sekarang <= target_jarak + 2:
            self.stop_motors(robot)
            if self.waktu_patokan is None:
                self.waktu_patokan = now
            if now - self.waktu_patokan > 0.1:
                settle_time = now - self.waktu_mulai_gerak
                print(
                    f"[TUNING] Geser Kiri Selesai! Settle Time: {settle_time:.3f} s"
                )

                if settle_time > 1.8:
                    self.config_data["auto_tuning_pid"]["geser_ke_titik_kiri"]["kp_max"] = min(
                        15.0, p["kp_max"] + 0.3
                    )
                    self.save_config_json()

                self.stop(robot)
                self.waktu_patokan = None
                self.last_valid_jarak_kiri = None
                return True
        else:
            self.waktu_patokan = None
        return False