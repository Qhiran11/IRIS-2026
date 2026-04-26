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


from GerakanDasar import GerakanDasar

def main():
    print("Memulai Program Utama KRAI...")
    # ... (print logo Anda) ...

    r2 = Robot() 
    # sensor = SensorReader(port='COM36', baudrate=115200) 
    writer = ArduinoDueWriter(port='COM29', baudrate=115200) 
    gerak = GerakanDasar()
    Capit = GerakanCapitKFS()
    ambil_kfs = GerakanAmbilKFS() # Inisialisasi Otak Kecil


    # --- INISIALISASI KAMERA & ENCODER OPTIK ---
    print("Menyiapkan Kamera Optical Odometry...")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) # Ganti index kamera jika perlu (0, 1, 2)
    # Turunkan resolusi kamera hardware agar loop lebih cepat
    
    encoder = OpticalEncoder(sensitivity=1.5, deadzone=0.5)

    # INISIALISASI VARIABEL UNTUK TRACKING TIMEOUT
    array_temp = [0] * 12
    errorCount = 0
    last_change_time = time.time()

    # while True:  # MAIN LOOP
    #     array_input = sensor.baca_data()
    #     current_time = time.time()

    #     # 1. JIKA ADA DATA YANG MASUK
    #     if array_input is not None:
    #         # Cek apakah datanya benar-benar baru (tidak nyangkut)
    #         if array_input != array_temp:
    #             array_temp = array_input.copy()  # Simpan sebagai data terakhir
    #             last_change_time = current_time  # Reset timer (jantung masih berdetak)
    #             errorCount = 0 

    #         # Eksekusi rutin robot
    #         r2.sensor.update_dari_array(array_input)
            
    #         gerak.target_angle = 0
    #         gerak.maju(r2)
            
    #         if (r2.sensor.kompas == gerak.target_angle):
    #             gerak.pid.reset()
                
    #         data_keluar = r2.motor.get_array_output()
    #         print(f"Kompas={r2.sensor.kompas}, jarak={r2.sensor.jarak_depan}, Motor={data_keluar}")

    #         # writer.kirim_data(data_keluar)

    #     # 2. PENGECEKAN TIMEOUT (Di luar if-else utama)
    #     # Jika selisih waktu sekarang dan terakhir kali data berubah lebih dari 0.5 detik
    #     if (current_time - last_change_time) > 1:
    #         print(f"[ERROR COUNT {errorCount}] Error: Array tidak berubah atau koneksi Arduino Mega terputus!")
    #         errorCount += 1
    #         # FITUR SAFETY: Hentikan robot agar tidak menabrak saat hilang sinyal
    #         # gerak.stop(r2)
    #         # writer.kirim_data(r2.motor.get_array_output())
            
    #         # Anda bisa me-reset timer lagi di sini jika hanya ingin print sekali per 0.5 detik, 
    #         # atau biarkan saja agar pesan terus muncul sampai koneksi pulih.
    #         last_change_time = current_time 

    #     time.sleep(0.01) # Istirahat CPU sebentar


    while True:
        # if langkah > 0:
        # selesai = ambil_kfs.jalankan_kombinasi_1(r2, writer)

        # 2. BACA SENSOR OPTIK (Kamera Bawah)

        ret, frame = cap.read()
        if ret:
            # Dapatkan delta X dan Y dari gerakan lantai
            pos_x, pos_y = encoder.update(frame)
            
            # Simpan hasil optical flow ke dalam memori robot
            r2.sensor.posisi_x = pos_x
            r2.sensor.posisi_y = pos_y

            print(f"Optical Encoder - Posisi: X={r2.sensor.posisi_x}, Y={r2.sensor.posisi_y:.2f}")

            # Opsional: Tampilkan ke layar (Beratkan CPU, gunakan hanya saat debug)
            # cv2.imshow("Optical Flow Debug", frame)
            # cv2.waitKey(1)
            
        else:
            print("[WARNING] Kamera Optical Encoder terputus!")

        # Delay CPU ringan
        # time.sleep(0.01)
        
        # Capit.MajuMundur(r2, writer, "maju")
        # # print("mundur")
        # time.sleep(2)

        # Capit.MajuMundur(r2, writer, "tengah")
        # # # print("tengah")
        # time.sleep(2)

        # Capit.jepit(r2, writer, "buka")
        # Capit.putar_kedepan_full(r2, writer)
        

        # Capit.tengah(r2, writer)
        # print("tengah")
        # time.sleep(2)
        





            # langkah -= 1
        # elif langkah == 0:
        #     r2.motor.stepper1 = 0
        #     data_keluar = r2.motor.get_array_output()
        #     writer.kirim_data(data_keluar)
        #     # time.sleep(1)


        # Atau
        # r2.motor.stepper1 = -1 (Mundur)
        # r2.motor.stepper1 = 0  (Stop instan tanpa overshoot)
        

        # time.sleep(1)


if __name__ == "__main__":
    main()