class SensorData:
    def __init__(self):
        self.posisi_x = 0.0
        self.posisi_y = 0.0
        
        # --- DATA SENSOR (30% Bilangan Bulat / Int) ---
        self.switch = 0
        self.temp_kompas = 0
        self.kompas = 0
        self.jarak_depan = 0
        self.jarak_kiri = 0
        self.sensor_jarak = 0
        self.proxi_belakang = 0
        self.proxi_depan = 1

        self.tombak_terdeteksi = False
        self.tombak_x = 0
        self.tombak_y = 0
        self.koreksi_pid_tombak = 0

        # Di dalam class Sensor atau RobotData Anda
        self.data_qr = ""
        

        # sensor ultrasonic
        self.ultrasonic_kiri = 0
        self.ultrasonic_kanan = 0
        self.ultrasonic_belakang = 0
        
        # --- DATA BINARY (70% 0 atau 1) ---
        self.kfs_terdeteksi = False
        self.limit_kanan_capit = 0
        self.limit_kiri_capit = 0
            
        self.limit_capitBuka      = 1
        self.limit_capitJepit      = 1


        self.sensor_garis_1 = False
        self.sensor_garis_2 = False
        self.tombol_start = 0
        
        # Data Cadangan
        self.kompas2 = 0

        self.kompas3 = 0

        self.kfs_terdeteksi = 0

        self.sensor_kfs_depan = 0
        self.sensor_garis_1 = 0
        self.sensor_garis_2 = 0

        self.posisi_di_hutan = 0

    def update_dari_array(self, arr):
        """
        Memetakan array[12] dari STM32 ke variabel objek.
        Sesuaikan index [0-11] dengan urutan pengiriman di STM32 Anda.
        """
        if arr is not None and len(arr) >= 12:
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
            self.jarak_depan   = arr[1]
    
            self.ultrasonic_kiri    = arr[3]
            self.ultrasonic_kanan = arr[2]
            self.ultrasonic_belakang = arr[4]

            self.proxi_belakang      = arr[5]   
            
            self.limit_kanan_capit   = arr[6]
            self.limit_kiri_capit   = arr[7]
            
            self.limit_capitBuka      = arr[8]
            self.limit_capitJepit      = arr[9]

            self.proxi_depan      = arr[10]
            
            self.kompas2      = arr[11]
            
            self.kompas3      = arr[12]
            self.kfs_terdeteksi = arr[13]

            self.sensor_kfs_depan = arr[14]
            self.sensor_garis_1 = arr[15]
            self.sensor_garis_2 = arr[16]



class MotorCommand:
    def __init__(self):
        # Output untuk 6 Motor (PW: Relay, DC: PWM)
        self.relay_pw_kanan = 0  # data 0
        self.relay_pw_kiri = 0   # data 1
        self.m3_pwm = 0  # data 2
        self.m4_pwm = 0  # data 3
        self.m5_pwm = 0  # data 4
        self.m6_pwm = 0  # data 5

        self.mDorong1 = 0  # data 6
        self.mDorong2 = 0  # data 7
        
        # Kontrol Relay / Gripper
        self.capit_putar_kiri = 0  # data 8
        self.capit_putar_kanan = 0 # data 9
        self.capit_jepit = 0 # data 10
        
        # Kontrol Stepper
        self.stepper1 = 0 # data 11
        self.pwLogic = 0 # data 12

        # Relay tambahan (pin 40 & pin 42)
        self.relay_tambahan1 = 0 # data 13
        self.relay_tambahan2 = 0 # data 14
        self.cadangan3 = 0 # data 15
        self.cadangan4 = 0 # data 16
        self.cadangan5 = 0 # data 17
        self.cadangan6 = 0 # data 18
        self.cadangan7 = 0 # data 19

    def get_array_output(self):
        """
        Mengemas variabel menjadi array[20] untuk dikirim ke Arduino Due.
        """
        arr = [
            self.relay_pw_kanan, self.relay_pw_kiri, self.m3_pwm, 
            self.m4_pwm, self.m5_pwm, self.m6_pwm,
            self.mDorong1, self.mDorong2,
            self.capit_putar_kiri, self.capit_putar_kanan,
            self.capit_jepit, 
            self.stepper1, self.pwLogic,
            self.relay_tambahan1, self.relay_tambahan2, self.cadangan3, 
            self.cadangan4, self.cadangan5, self.cadangan6, self.cadangan7
        ]
        
        return arr


class Robot:
    def __init__(self):
        """Objek Utama yang menyatukan Sensor dan Motor"""
        self.sensor = SensorData()
        self.motor = MotorCommand()
        self.jumlah_kfs = 0
        self.zona_aktif = 1  # State awal robot