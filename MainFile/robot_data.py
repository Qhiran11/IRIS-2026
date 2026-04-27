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
        
        # --- DATA BINARY (70% 0 atau 1) ---
        self.kfs_terdeteksi = False
        self.limit_switch_atas = False
        self.limit_switch_bawah = False
        self.sensor_garis_1 = False
        self.sensor_garis_2 = False
        self.tombol_start = False
        
        # Data Cadangan
        self.cadangan_1 = 0
        self.cadangan_2 = 0

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
            self.proxi_belakang    = arr[3]
            self.jarak_kiri       = arr[2]
            
            # Data Binary (mengubah 0/1 menjadi True/False)
            self.jarak_depan   = arr[1]
            self.limit_switch_atas = bool(arr[4])
            self.limit_switch_bawah = bool(arr[5])
            self.sensor_garis_1   = bool(arr[6])
            self.sensor_garis_2   = bool(arr[7])
            self.tombol_start     = bool(arr[8])
            
            self.cadangan_1      = arr[9]
            self.cadangan_2      = arr[10]
            self.cadangan_3      = arr[11]


class MotorCommand:
    def __init__(self):
        # Output untuk 6 Motor (PWM)
        self.m1_pwm = 0
        self.m2_pwm = 0
        self.m3_pwm = 0
        self.m4_pwm = 0
        self.m5_pwm = 0
        self.m6_pwm = 0
        
        # Kontrol Relay / Gripper
        self.relay_pompa = 0
        self.capit_putar1 = 0
        self.capit_putar2 = 0
        self.capit_jepit = 0
        
        # Kontrol Stepper
        self.stepper1 = 0 # M11
        self.motorlain = 0 # M12

    def get_array_output(self):
        """
        Mengemas variabel menjadi array[13] untuk dikirim ke Arduino Due.
        """
        arr = [
            self.m1_pwm, self.m2_pwm, self.m3_pwm, 
            self.m4_pwm, self.m5_pwm, self.m6_pwm,
            self.motorlain, self.relay_pompa,
            self.capit_putar1, self.capit_putar2,
            self.capit_jepit, 
            self.stepper1, self.motorlain
        ]
        
        return arr


class Robot:
    def __init__(self):
        """Objek Utama yang menyatukan Sensor dan Motor"""
        self.sensor = SensorData()
        self.motor = MotorCommand()
        self.zona_aktif = 1  # State awal robot