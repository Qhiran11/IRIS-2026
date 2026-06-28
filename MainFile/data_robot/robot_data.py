import time # Tambahkan ini di bagian atas file
from data_robot.ConfigManager import ConfigManager
# Tambahkan kelas ini sebelum class Robot
class SystemState:
    def __init__(self):
        self.reset_all()
        self.gerak_dasar_aktif = "IDLE"

    def reset_all(self):
        """Fungsi ini bertindak seperti tombol Reset Mikrokontroler"""
        now = time.time() # Ambil waktu sekarang

        
        
        # --- 1. State Proses Utama ---
        self.main_state = "READY"
        self.main_temp_state = ""
        self.main_then = now # Ubah dari 0.0

        # --- 2. State Rakit Senjata ---
        self.rakit_state = "IDLE"
        self.rakit_start_time = now # Ubah dari 0.0
        self.rakit_transition_start = now # Ubah dari 0.0
        self.rakit_next_state = ""
        self.rakit_is_done = False

        # --- 3. State Naik Turun ---
        self.naikturun_state = "IDLE"
        self.naikturun_sub_state = "SIAP"
        self.naikturun_sub_state1 = "PERISAPAN"
        self.naikturun_sub_state2 = "PERISAPAN"
        self.naikturun_start_time = now # Ubah dari 0.0
        self.naikturun_transition_start = now
        self.naikturun_transition_start1 = now
        self.naikturun_transition_start2 = now
        
        self.naikturun_then = now # Ubah dari 0.0
        self.naikturun_is_done = False

        # --- 4. State Zona 3 ---
        self.zona3_state = "READY"
        self.zona3_then = now # Ubah dari 0.0

        # --- 5. State Ambil KFS ---
        self.kfs_state = "IDLE"
        self.kfs_start_time = now # Ubah dari 0.0
        self.kfs_then = now # Ubah dari 0.0
        self.kfs_transition_start = now
        self.kfs_next_state = ""
        self.kfs_is_done = False


class SensorData:
    def __init__(self):
        self.temp_kompas = 0
        self.temp_pitch = 0  # [BARU] Variabel untuk menyimpan kalibrasi awal pitch
        
        self.kompas = 0
        # sensor ultrasonic
        self.ultrasonic_depan = 0
        self.ultrasonic_kiri = 0
        self.ultrasonic_kanan = 0
        self.ultrasonic_belakang = 0

        # Sensor tambahan baru
        self.ultrasonic_bawah_depan = 0
        self.ultrasonic_bawah_tengah = 0
        self.ultrasonic_bawah_belakang = 0
        self.pitch_kompas = 0

        self.tombol_start = 1
        self.tombol_reset = 1
        self.cekTombak = 0
        # --- DATA SENSOR (30% Bilangan Bulat / Int) ---
        self.switch = 0
        self.proxi_belakang = 0
        self.proxi_depan = 1

        # Di dalam class Sensor atau RobotData Anda
        self.data_qr = ""
        
        # --- DATA BINARY (70% 0 atau 1) ---
        self.kfs_terdeteksi = False
        self.limit_kanan_capit = 0
        self.limit_kiri_capit = 0
            
        self.limit_capitBuka      = 1
        self.limit_capitJepit      = 1
        
        # Data Cadangan
        self.kompas2 = 0
        self.kompas3 = 0
        
        self.kfs_terdeteksi = 0
        self.sensor_kfs_depan = 0
        self.posisi_di_hutan = 0
        

    def update_dari_array(self, arr):
        """
        Memetakan array data dari Arduino Mega ke variabel objek.
        """
        if arr is not None and len(arr) >= 17:
            # 1. Ambil Offset di pembacaan pertama untuk Kompas dan Pitch
            if self.switch == 0:
                self.temp_kompas = arr[0]
                self.temp_pitch = arr[10]  # [BARU] Simpan kalibrasi awal pitch
                self.switch = 1
                print(f"[KALIBRASI] Arah 0 diset pada: {self.temp_kompas} derajat")
                print(f"[KALIBRASI] Pitch 0 diset pada: {self.temp_pitch} derajat") # Log tambahan
            
            # ---------------------------------------------------------
            # 2a. Hitung selisih relatif dan NORMALISASI KOMPAS
            # ---------------------------------------------------------
            sudut_relatif = arr[0] - self.temp_kompas
            
            # NORMALISASI (-180 hingga 180)
            if sudut_relatif > 180:
                sudut_relatif -= 360
            elif sudut_relatif < -180:
                sudut_relatif += 360
                
            self.kompas = sudut_relatif
            
            # ---------------------------------------------------------
            # 2b. Hitung selisih relatif dan NORMALISASI PITCH [BARU]
            # ---------------------------------------------------------
            pitch_relatif = arr[10] - self.temp_pitch
            
            # NORMALISASI (-180 hingga 180)
            if pitch_relatif > 180:
                pitch_relatif -= 360
            elif pitch_relatif < -180:
                pitch_relatif += 360
            
            self.pitch_kompas = pitch_relatif
            
            
            # Pemetaan sensor ultrasonik utama
            self.ultrasonic_depan    = arr[1]  # S4 (Depan)
            self.ultrasonic_kiri     = arr[2]  # S7 (Kiri via UART)
            self.ultrasonic_kanan    = arr[3]  # S2 (Kanan)
            self.ultrasonic_belakang = arr[4]  # S5 (Belakang)

            # Tombol data dari Nano
            self.tombol_start = arr[6]  # Nano_A
            self.tombol_reset = arr[5]  # Nano_B

            # Sensor tambahan baru
            self.ultrasonic_bawah_depan    = arr[7]  # S3 (Bawah Depan)
            self.ultrasonic_bawah_tengah   = arr[8]  # S1 (Bawah Tengah)
            self.ultrasonic_bawah_belakang = arr[9]  # S6 (Bawah Belakang)
            # self.pitch_kompas = arr[10]  # <--- Ini dihapus/diganti dengan logika di atas

            # Backward compatibility / Cadangan
            # Catatan: Jika kompas2 juga butuh dinormalisasi, Anda bisa menggantinya dengan self.pitch_kompas
            self.kompas2 = arr[10] # simpan pitch ke kompas2 (Raw / Mentah)
            self.kompas3 = arr[0]  # (Raw / Mentah)


class MotorCommand:
    def __init__(self):
        # 6 Motor Driver
        self.m0_pwm = 0      # FR (index 2)
        self.m1_pwm = 0      # FL (index 3)
        self.m2_pwm = 0      # BR (index 4)
        self.m3_pwm = 0      # BL (index 5)
        
        # 2 Motor Power Window (index 0 & 1)
        self.mDorong1 = 0    # PW Kanan (index 0)
        self.mDorong2 = 0    # PW Kiri (index 1)

        # PCA Motor
        self.pca_motor = 0   # index 6

        # Relays
        self.CapitTombakJepit = 0     # index 7 (Relay 1 - pin 40)
        self.CapitTombakNaikTurun = 0 # index 8 (Relay 2 - pin 42)
        self.relayCapitKFSJepit = 0   # index 9 (Relay 3 - pin 36)
        self.relayCapitKFSAngkat = 0  # index 9 (Relay 3 - pin 36)

        # Backward compatibility placeholders
        self.pwLogic = 0
        self.m4_pwm = 0
        self.m5_pwm = 0
        self.m6_pwm = 0
        self.capit_jepit = 0

    def get_array_output(self):
        """
        Mengemas variabel menjadi array[15] untuk dikirim ke Arduino Mega/Due.
        Sesuai dengan protokol Output.ino:
        - index 0: PW Kanan (M0)
        - index 1: PW Kiri (M1)
        - index 2: FR (M2)
        - index 3: FL (M3)
        - index 4: BR (M4)
        - index 5: BL (M5)
        - index 6: PCA Motor
        - index 7: Relay 1 (pin 40)
        - index 8: Relay 2 (pin 42)
        - index 9: Relay 3 (pin 36)
        - index 10-14: Unused
        """
        # Konversi perintah PW dari biner (1 / -1) ke PWM (255 / -255) jika diperlukan
        pw_r = self.mDorong1
        if pw_r == 1: pw_r = 255
        elif pw_r == -1: pw_r = -255

        pw_l = self.mDorong2
        if pw_l == 1: pw_l = 255
        elif pw_l == -1: pw_l = -255

        # Relay 3 aktif jika salah satu dari KFS Capit jepit/angkat bernilai 1
        r3 = 1 if (self.relayCapitKFSJepit == 1 or self.relayCapitKFSAngkat == 1) else 0

        arr = [
            int(pw_r),                            # index 0 (PW Kanan / M0)
            int(pw_l),                            # index 1 (PW Kiri / M1)
            int(self.m0_pwm),                     # index 2 (FR / M2)
            int(self.m1_pwm),                     # index 3 (FL / M3)
            int(self.m2_pwm),                     # index 4 (BR / M4)
            int(self.m3_pwm),                     # index 5 (BL / M5)
            int(self.pca_motor),                  # index 6 (PCA Motor)
            int(self.CapitTombakJepit),           # index 7 (Relay 1 - pin 40)
            int(self.CapitTombakNaikTurun),       # index 8 (Relay 2 - pin 42)
            int(r3),                              # index 9 (Relay 3 - pin 36)
            0,                                    # index 10 (Unused)
            0,                                    # index 11 (Unused)
            0,                                    # index 12 (Unused)
            0,                                    # index 13 (Unused)
            0                                     # index 14 (Unused)
        ]
        return arr


class Robot:
    def __init__(self):
        """Objek Utama yang menyatukan Sensor dan Motor"""
        self.sensor = SensorData()
        self.motor = MotorCommand()
        self.jumlah_kfs = 0
        self.zona_aktif = 1  # State awal robot
        self.state = SystemState() # [BARU] Menambahkan State Manager terpusat
        self.InputTerhubung = False
        self.OutputTerhubung = False

        self.ROBOT_MAIN_STATE = "STANDBY"
        self.config = ConfigManager('config.json')
        self.targetJarakKanan = self.config.data.get("umum", {}).get("target_jarak_kanan_awal", 8) # JARAK AWAL DI KANAN
        self.targetJarakBelakang = self.config.data.get("umum", {}).get("target_jarak_belakang_awal", 15)

        self.totalNaik = 0
        