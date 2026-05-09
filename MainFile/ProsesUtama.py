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
from GerakanAmbilPasangRakitSenjata import RakitSenjata
from GerakanNaikTurun import GerakanNaikTurun
from MappingArena import MappingArena
from Zona3 import Zona3


from GerakanDasar import GerakanDasar

def main():
    print("Memulai Program Utama KRAI...")
    # ... (print logo Anda) ...

    robot = Robot()
    
    sensor = SensorReader(port='COM36', baudrate=115200) 
    writer = ArduinoDueWriter(port='COM48', baudrate=115200)

    arena = MappingArena()

    arena.jumlah_Naik = 3

 
    gerak = GerakanDasar()
    rakit = RakitSenjata()
    Capit = GerakanCapitKFS()
    ambil_kfs = GerakanAmbilKFS() # Inisialisasi Otak Kecil
    array_temp = [0] * 12
    errorCount = 0
    last_change_time = time.time()
    rakit = RakitSenjata()
    masukMainhua = GerakanNaikTurun()
    zona3 = Zona3()

    bool_putar_ganti = "NAIK"

    STATE = "READY"
    # STATE = "PROSESTURUN"
    


    # ... (Kode inisialisasi di atas tetap sama) ...
    try:
        # time.sleep(5)
        then = time.time()
        while True:
            # 1. BACA SENSOR DARI ARDUINO MEGA
            array_input = sensor.baca_data()
            now = time.time()
            

            

            # Pastikan data ada (tidak None/kabel tidak putus)
            if array_input is not None:
                robot.sensor.update_dari_array(array_input) # Update memori robot

                
                # Print untuk debugging
                # print(f"K: {robot.sensor.kompas} | D: {robot.sensor.jarak_depan}  | ultr_kiri : {robot.sensor.ultrasonic_kiri} | ultr_kanan : {robot.sensor.ultrasonic_kanan} | ultrasonic_belakang : {robot.sensor.ultrasonic_belakang} ")
                # print(f"K: {robot.sensor.kompas} | D: {robot.sensor.jarak_depan}  | kiri : {robot.sensor.ultrasonic_kiri} | kanan : {robot.sensor.ultrasonic_kanan} | blkng : {robot.sensor.ultrasonic_belakang} | K2: {robot.sensor.kompas2} | K3: {robot.sensor.kompas3} ")
                # print (f"Motor : r1 {robot.motor.m1_pwm}  robot {robot.motor.m2_pwm}  r3 {robot.motor.m3_pwm}  r4 {robot.motor.m4_pwm}  r5 {robot.motor.m5_pwm}  r6 {robot.motor.m6_pwm} ")
                # print(f" sensor {robot.sensor.proxi_belakang}, depan {robot.sensor.jarak_depan}")
                # print(f"limit_kanan_capit : {robot.sensor.limit_kanan_capit} | limit_kiri_capit : {robot.sensor.limit_kiri_capit}")
                print(f"limit_kanan_capit : {robot.sensor.limit_capitBuka} | limit_kiri_capit : {robot.sensor.limit_capitJepit} | proxi_depan : {robot.sensor.proxi_depan}")
                # 2. TENTUKAN TARGET ARAH (Opsional, 0 adalah lurus mengikuti saat robot dinyalakan)
                # gerak.target_angle = -180  

                
                # gerak.base_speed =  40
                # gerak.geser_ke_tengah(robot)

                

                # gerak.mundur_diagonal_kiri(robot)

                # gerak.maju_diagonal_kanan(robot)

                # 3. KALKULASI PID DAN GERAKAN
                # gerak.hadap_sudut(robot)
                # gerak.mundur(robot)
                # selesai = rakit.RakitSenjata()
                # selesai = masukMainhua._proses_ke_tengah(robot, gerak)
                # selesai = rakit.jalankan(robot, gerak, 90, 20)
                
                




                # Capit.posisiPutar(robot)

                # gerak.turun(robot)

                # if (bool_putar_ganti == "NAIK"):
                #     selesai = masukMainhua._proses_naik(robot, gerak)
                #     if selesai:
                #         print("Proses Rakit Berhasi l.")
                        # print(f"K: {robot.sensor.kompas} |    D: {robot.sensor.jarak_depan}  | ultrasonic_kiri : {robot.sensor.ultrasonic_kiri} | ultrasonic_kanan : {robot.sensor.ultrasonic_kanan} | ultrasonic_belakang : {robot.sensor.ultrasonic_belakang} ")
                #         time.sleep(3)
                #         bool_putar_ganti = "TURUN"
                
                # elif (bool_putar_ganti == "TURUN"):
                #     selesai = masukMainhua._proses_turun(robot, gerak)
                #     if selesai:
                #         print("Proses Rakit Berhasi l.")
                #         print(f"K: {robot.sensor.kompas} | D: {robot.sensor.jarak_depan}  | ultrasonic_kiri : {robot.sensor.ultrasonic_kiri} | ultrasonic_kanan : {robot.sensor.ultrasonic_kanan} | ultrasonic_belakang : {robot.sensor.ultrasonic_belakang} ")
                #         time.sleep(3)
                #         bool_putar_ganti = "NAIK"
               
                #         # break   
                #     # Lanjut ke tugas berikutnya...
                    
                # Capit.MajuMundur(robot, 800)
                

                # gerak.turun(robot)
                # if (now - then > 2.0):
                #     print("Program selesai.")
                #     break

                # robot.motor.mDorong1 = 100
                # robot.motor.mDorong2 = -100

                # match STATE:
                #     case "READY":
                #         gerak.stop(robot)
                #         if (now - then > 2.0):
                #             STATE = "GO"
                #             then = now
                #     case "GO":
                #         selesai = rakit.jalankan(robot, gerak, 90, 20)
                #         if selesai:
                #             STATE = "GOGO"
                #             then = now
                #     case "GOGO":
                #         selesai = masukMainhua._proses_ke_tengah(robot, gerak)
                #         if selesai:
                #             STATE = "NAIK"
                #             then = now
                #     case "NAIK":
                #         selesai = masukMainhua._proses_naik(robot, gerak)
                #         if (selesai):
                #             STATE = "HITUNGNAIK"
                #             then = now
                        
                #     case "HITUNGNAIK":
                #         arena.jumlah_Naik = arena.jumlah_Naik - 1
                #         print(arena.jumlah_Naik)
                #         if (arena.jumlah_Naik > 0):
                #             STATE = "NAIK"
                #         else:
                #             gerak.stop(robot)
                #             gerak.target_angle = -180
                #             time.sleep(1)
                #             then = now
                #             STATE = "PENGECEKAN"

                #     case "PENGECEKAN":
                #         if (arena.jumlah_Turun == 3):
                #             print(f"K: {robot.sensor.kompas} | D: {robot.sensor.jarak_depan}  | ultrasonic_kiri : {robot.sensor.ultrasonic_kiri} | ultrasonic_kanan : {robot.sensor.ultrasonic_kanan} | ultrasonic_belakang : {robot.sensor.ultrasonic_belakang} ")
                #             break
                #         else :
                #             if arena.jumlah_Turun == 0:
                #                 gerak.target_angle = -180
                #             if arena.jumlah_Turun == 1:
                #                 gerak.target_angle = -90
                #             if arena.jumlah_Turun == 2:
                #                 gerak.target_angle = -180
                #             then = time.time()                            
                #             STATE =  "PROSESTURUN1"

                #     case "PROSESTURUN1":
                #         if (robot.sensor.kompas == gerak.target_angle or robot.sensor.kompas == -gerak.target_angle):
                #             gerak.stop(robot)
                #             if time.time() - then > 0.1:
                #                 gerak.stop(robot)
                #                 STATE =  "TURUN"
                #         else:
                #             gerak.hadap_sudut(robot)
                #             then = time.time()
                    
                #     case "TURUN":
                #         selesai = masukMainhua._proses_turun(robot, gerak)
                #         if selesai:
                #             arena.jumlah_Turun = arena.jumlah_Turun + 1
                #             STATE =  "PENGECEKAN"
                            
                            
                # selesai = zona3.logic_zona3(robot, gerak)
                            


                selesai = ambil_kfs.jalankan_kombinasi_1(robot)
                if selesai:
                    break

                # selesai = Capit.buka(robot)
                # if selesai:
                #     break


                



                # 4. EKSTRAK DAN KIRIM KE ARDUINO DUE (Ini yang sebelumnya hilang)

                data_keluar = robot.motor.get_array_output()
                writer.kirim_data(data_keluar) 

            # 5. ISTIRAHAT CPU (Sangat penting agar terminal tidak freeze)
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\n[FAILSAFE] Terminal dihentikan paksa (Ctrl+C)!")

    except Exception as e:
        print(f"\n[FAILSAFE] Terjadi Error Sistem: {e}")

    finally:
        print("[FAILSAFE] Mematikan semua motor...")
        
        # 1. Nol-kan semua nilai PWM dan target
        gerak.stop(robot)
        robot.motor.stepper1 = 0
        robot.motor.capit_putar_kiri = 0
        robot.motor.capit_putarobot = 0
        robot.motor.capit_jepit = 0
        
        # 2. Paksa kirim array berisi angka 0 ke Arduino Due
        try:
            writer.kirim_data(robot.motor.get_array_output())
            print("[FAILSAFE] Data stop berhasil dikirim ke roda.")
        except:
            print("[FAILSAFE] Gagal mengirim data stop (kabel mungkin terputus).")
            
        print("Program selesai.")
        sys.exit(0)

if __name__ == "__main__":
    main()