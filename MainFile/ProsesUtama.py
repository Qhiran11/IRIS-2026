# File: ProsesUtama.py
import sys
import os
import time
import cv2
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Input import SensorReader
from Output import ArduinoDueWriter
from robot_data import Robot
from GerakanCapitKFS import GerakanCapitKFS
from GerakanAmbilKFS import GerakanAmbilKFS
from MappingArena import OpticalEncoder
from GerakanAmbilPasangRakitSenjata import RakitSenjata


from GerakanDasar import GerakanDasar

def main():
    print("Memulai Program Utama KRAI...")
    # ... (print logo Anda) ...

    r2 = Robot() 
    sensor = SensorReader(port='COM36', baudrate=115200) 
    writer = ArduinoDueWriter(port='COM29', baudrate=115200) 
    gerak = GerakanDasar()
    rakit = RakitSenjata()
    # Capit = GerakanCapitKFS()
    # ambil_kfs = GerakanAmbilKFSn() # Inisialisasi Otak Kecil


    # --- INISIALISASI KAMERA & ENCODER OPTIK ---
    # print("Menyiapkan Kamera Optical Odometry...")
    # cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) # Ganti index kamera jika perlu (0, 1, 2)
    # Turunkan resolusi kamera hardware agar loop lebih cepat
    
    # encoder = OpticalEncoder(sensitivity=2.0, deadzone=1.0) # Sesuaikan sensitivitas dan deadzone sesuai kebutuhan

    # INISIALISASI VARIABEL UNTUK TRACKING TIMEOUT
    array_temp = [0] * 12
    errorCount = 0
    last_change_time = time.time()
    rakit = RakitSenjata()


    # ... (Kode inisialisasi di atas tetap sama) ...

    while True:
        # 1. BACA SENSOR DARI ARDUINO MEGA
        array_input = sensor.baca_data()

        # Pastikan data ada (tidak None/kabel tidak putus)
        if array_input is not None:
            # Update memori robot
            r2.sensor.update_dari_array(array_input)
            
            # Print untuk debugging
            print(f"K: {r2.sensor.kompas} | D: {r2.sensor.jarak_depan} | Kri: {r2.sensor.jarak_kiri} | r1 {r2.motor.m1_pwm}  r2 {r2.motor.m2_pwm}  r3 {r2.motor.m3_pwm}  r4 {r2.motor.m4_pwm}  r5 {r2.motor.m5_pwm}  r6 {r2.motor.m6_pwm} ")

            # 2. TENTUKAN TARGET ARAH (Opsional, 0 adalah lurus mengikuti saat robot dinyalakan)
            # gerak.target_angle = 90  

            # 3. KALKULASI PID DAN GERAKAN
            # gerak.hadap_sudut(r2)
            # gerak.maju(r2)
            # rakit.RakitSenjata()
            selesai = rakit.jalankan(r2, gerak, 90)
            
            # if selesai:
            #     print("Proses Rakit Berhasil.")
                # Lanjut ke tugas berikutnya...
            


            
            # 4. EKSTRAK DAN KIRIM KE ARDUINO DUE (Ini yang sebelumnya hilang)
            data_keluar = r2.motor.get_array_output()
            writer.kirim_data(data_keluar)

        # 5. ISTIRAHAT CPU (Sangat penting agar terminal tidak freeze)
        time.sleep(0.01)

if __name__ == "__main__":
    main()