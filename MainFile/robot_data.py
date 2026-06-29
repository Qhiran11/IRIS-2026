import time # Tambahkan ini di bagian atas file
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
        self.kompas = 0
        # sensor ultrasonic
        self.ultrasonic_depan = 0
        self.ultrasonic_kiri = 0
        self.ultrasonic_kanan = 0
        self.ultrasonic_belakang = 0

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
        Memetakan array[12] dari STM32 ke variabel objek.
        Sesuaikan index [0-11] dengan urutan pengiriman di STM32 Anda.
        """
        if arr is not None and len(arr) >= 17:
            # Contoh pemetaan (Silakan sesuaikan dengan urutan di STM32)
            
            # 1. Ambil Offset di pembacaan pertama
            if self.switch == 0:
                self.temp_kompas = arr[0]
                self.switch = 1
                print(f"[KALIBRASI] Arah 0 diset pada: {self.temp_kompas} derajat")
            
            # 2. Hitung selisih relatif
            sudut_relatif = arr[0] - self.temp_kompas
            
            # 3. NORMALISASI (-180 hingga 180)
            if sudut_relatif > 180:
                sudut_relatif -= 360
            elif sudut_relatif < -180:
                sudut_relatif += 360
                
            # 4. Simpan hasil akhir
            self.kompas = sudut_relatif
            self.kompas2      = arr[9]
            self.ultrasonic_depan   = arr[1]
    
            self.ultrasonic_kiri    = arr[2]
            self.ultrasonic_kanan = arr[3]
            self.ultrasonic_belakang = arr[4]

            self.tombol_start = arr[5]
            self.tombol_reset = arr[6]

            self.proxi_belakang  = arr[7]
            self.proxi_depan     = arr[8] 

            

            self.limit_kanan_capit   = arr[9]
            self.limit_capitBuka      = arr[10]
            self.limit_capitJepit      = arr[11]
            self.proxi_depan1      = arr[12]
            
            self.kompas2      = arr[13]
            
            self.kompas3      = arr[12]
            self.kfs_terdeteksi = arr[13]

            self.sensor_kfs_depan = arr[14]
            



class MotorCommand:
    def __init__(self):
        # 6 Motor Driver
        self.m1_pwm = 0      # data 0
        self.m2_pwm = 0      # data 1
        self.m3_pwm = 0      # data 2
        self.m4_pwm = 0      # data 3
        self.m5_pwm = 0      # data 4
        self.m6_pwm = 0      # data 5

        # 2 Motor Relay (data mDorong1 & mDorong2 pindah ke PW relay)
        self.mDorong1 = 0    # data 6
        self.mDorong2 = 0    # data 7

        self.pwLogic = 0     # data 8

        # Relay tambahan (pin 40 & pin 42)
        self.CapitTombakJepit = 0 # data 9
        self.CapitTombakNaikTurun = 0 # data 10

        # Deprecated / Dummy variables to maintain backward compatibility with other scripts
        self.relayCapitKFSAngkat = 0
        self.relayCapitKFSJepit = 0

    def get_array_output(self):
        """
        Mengemas variabel menjadi array[11] untuk dikirim ke Arduino Due.
        """
        arr = [
            self.m1_pwm, self.m2_pwm, self.m3_pwm, 
            self.m4_pwm, self.m5_pwm, self.m6_pwm,
            self.mDorong1, self.mDorong2,
            self.pwLogic,
            self.CapitTombakJepit, self.CapitTombakNaikTurun,
            self.relayCapitKFSAngkat, self.relayCapitKFSJepit,  
            0,
            0
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
        self.targetJarakKanan = 8 # JARAK AWAL DI KANAN
        self.targetJarakBelakang = 15

        self.totalNaik = 0
        
        