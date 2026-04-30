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
from GerakanNaikTurun import GerakanNaikTurun


from GerakanDasar import GerakanDasar

def main():
    print("Memulai Program Utama KRAI...")
    # ... (print logo Anda) ...

    r2 = Robot() 
    sensor = SensorReader(port='COM13', baudrate=115200) 
    # writer = ArduinoDueWriter(port='COM29', baudrate=115200) 
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
    masukMainhua = GerakanNaikTurun()


    # ... (Kode inisialisasi di atas tetap sama) ...
    try:
        then = time.time()
        while True:
            # 1. BACA SENSOR DARI ARDUINO MEGA
            array_input = sensor.baca_data()
            now = time.time()
            

            

            # Pastikan data ada (tidak None/kabel tidak putus)
            if array_input is not None:
                # Update memori robot
                r2.sensor.update_dari_array(array_input)
                
                # Print untuk debugging
                print(f"K: {r2.sensor.kompas} | D: {r2.sensor.jarak_depan}  | ultrasonic_kiri : {r2.sensor.ultrasonic_kiri} | ultrasonic_kanan : {r2.sensor.ultrasonic_kanan} | ultrasonic_belakang : {r2.sensor.ultrasonic_belakang} ")
                # print (f"Motor : r1 {r2.motor.m1_pwm}  r2 {r2.motor.m2_pwm}  r3 {r2.motor.m3_pwm}  r4 {r2.motor.m4_pwm}  r5 {r2.motor.m5_pwm}  r6 {r2.motor.m6_pwm} ")

                # 2. TENTUKAN TARGET ARAH (Opsional, 0 adalah lurus mengikuti saat robot dinyalakan)
                # gerak.target_angle = 0  

                
                # gerak.base_speed = gerak.max_pwm = 120
                # gerak.geser_ke_tengah(r2)

                

                # gerak.mundur_diagonal_kiri(r2)

                # gerak.maju_diagonal_kanan(r2)

                # 3. KALKULASI PID DAN GERAKAN
                # gerak.hadap_sudut(r2)
                # gerak.mundur(r2)
                # rakit.RakitSenjata()
                # selesai = masukMainhua._proses_naik(r2, gerak)
                # selesai = rakit.jalankan(r2, gerak, 90, 20)
                
                # if selesai:
                    # print("Proses Rakit Berhasi l.")
                    # print(f"K: {r2.sensor.kompas} | D: {r2.sensor.jarak_depan}  | ultrasonic_kiri : {r2.sensor.ultrasonic_kiri} | ultrasonic_kanan : {r2.sensor.ultrasonic_kanan} | ultrasonic_belakang : {r2.sensor.ultrasonic_belakang} ")
                    # break
                    # Lanjut ke tugas berikutnya...
                
                

                # gerak.naik(r2)
                # if (now - then > 2.0):
                #     print("Program selesai.")
                #     break
                    

                
                # 4. EKSTRAK DAN KIRIM KE ARDUINO DUE (Ini yang sebelumnya hilang)
                data_keluar = r2.motor.get_array_output()
                # writer.kirim_data(data_keluar) 

            # 5. ISTIRAHAT CPU (Sangat penting agar terminal tidak freeze)
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\n[FAILSAFE] Terminal dihentikan paksa (Ctrl+C)!")

    except Exception as e:
        print(f"\n[FAILSAFE] Terjadi Error Sistem: {e}")

    finally:
        print("[FAILSAFE] Mematikan semua motor...")
        
        # 1. Nol-kan semua nilai PWM dan target
        gerak.stop(r2)
        r2.motor.stepper1 = 0
        r2.motor.capit_putar1 = 0
        r2.motor.capit_putar2 = 0
        r2.motor.capit_jepit = 0
        
        # 2. Paksa kirim array berisi angka 0 ke Arduino Due
        try:
            writer.kirim_data(r2.motor.get_array_output())
            print("[FAILSAFE] Data stop berhasil dikirim ke roda.")
        except:
            print("[FAILSAFE] Gagal mengirim data stop (kabel mungkin terputus).")
            
        print("Program selesai.")
        sys.exit(0)

if __name__ == "__main__":
    main()