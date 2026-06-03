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
from MappingHutan import MappingHutan
from TelemetriJetson import TelemetryServer
from GerakanDasar import GerakanDasar
from InputKamera import KameraSensor
from InputKameraQR import DeteksiQR
from InputTombol import TombolKontrol

def main():
    print("Memulai Program Utama KRAI...")
    # ... (print logo Anda) ...

    robot = Robot()

    # --- INISIALISASI TELEMETRI ---
    telemetri = TelemetryServer()
    telemetri.start()
    # ------------------------------
    
    sensor = SensorReader(port='/dev/ttyUSB0', baudrate=115200) 
    writer = ArduinoDueWriter(port='/dev/ttyACM0', baudrate=115200)

    arena = MappingArena()
    hutan = MappingHutan()

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

    # kamera = KameraSensor(robot.sensor, tampilkan_video=False)
    kamera = DeteksiQR(robot, tampilkan_video=False)
    kamera.start()

    prosesAmbilKfs = False

    bool_putar_ganti = "NAIK"
    detectKfs = ""
    tombol_jetson = TombolKontrol(pin_start=31, pin_reset=33)
    
    is_running = False # Flag penanda apakah robot sedang standby atau running

    try:
        # kamera.start() # Mulai sensor kamera di background
        # time.sleep(5)
        
        while True:
            # ==============================================================
            # 1. BACA SENSOR & TELEMETRI (SELALU JALAN DI LATAR)
            # ==============================================================
            array_input = sensor.baca_data()
            telemetri.kirim_data(robot)
            now = time.time()

            # Pastikan data ada (tidak None/kabel tidak putus)
            if array_input is not None:
                robot.sensor.update_dari_array(array_input) # Update memori robot
                if not is_running:
                    # Pastikan motor benar-benar mati saat standby
                    # gerak.target_angle = -40
                    gerak.stop(robot) #    <==================TESTING
                    data_keluar = robot.motor.get_array_output()                    
                    writer.kirim_data(data_keluar) 

                    
                    # LOGIKA: Tahan di sini hingga tombol start ditekan
                    if robot.sensor.tombol_start == 0:
                        print("\n[SYSTEM] TOMBOL START DITEKAN! Memulai program...")
                        robot.state.reset_all() # Reset semua state ke kondisi awal
                        robot.jumlah_kfs = 0    # Reset counter fisik
                        # hutan.reset()         # (Opsional) Panggil jika Anda punya fungsi reset rute
                        
                        is_running = True       # Ubah mode menjadi Running
                        time.sleep(0.01)
                        continue # Skip semua logika di bawah, kembali ke awal while

                else:


                    if robot.sensor.tombol_reset == 0:
                        print("\n[SYSTEM] MASTER RESET DITEKAN! Kembali ke Standby...")
                        robot.state.reset_all()
                        gerak.stop(robot)
                        writer.kirim_data(robot.motor.get_array_output()) # Paksa motor mati
                        is_running = False # Kembalikan program ke fase Standby
                        continue # Langsung melompat kembali ke awal loop
                        
                    # --- LOGIKA STATE MACHINE UTAMA ---
                    if robot.state.main_state == "READY":
                        gerak.stop(robot)
                        if (now - robot.state.main_then > 0.3):
                            robot.state.main_state = "GO"
                            robot.state.main_then = now
                
                    elif robot.state.main_state == "GO":
                        selesai = rakit.jalankan(robot, gerak, 90, 2)
                        if selesai:
                            robot.state.main_state = "GOGO1"
                            robot.state.main_then = now
                            
                    elif robot.state.main_state == "GOGO":
                        selesai = masukMainhua._proses_ke_tengah(robot, gerak)
                        if selesai:
                            robot.state.main_state = "CEK_RUTE"
                            robot.state.main_then = now

                    elif robot.state.main_state == "AMBILKFS":
                        selesai = ambil_kfs.jalankan_kombinasi_1(robot, gerak)
                        if selesai:
                            robot.jumlah_kfs += 1
                            robot.state.main_state = "CEK_RUTE"
                            
                    # ==============================================================
                    # SIKLUS NAVIGASI OTOMATIS
                    # ==============================================================
                    elif robot.state.main_state == "CEK_RUTE":
                        move = hutan.get_next_move()
                        
                        if move is None:
                            print("[NAVIGASI] Tiba di Zona 3!")
                            robot.state.main_state = "ZONA3"
                        else:
                            aksi, sudut_hadap, petak_tujuan = move
                            gerak.target_angle = sudut_hadap 
                            
                            print(f"[NAVIGASI] Menuju Petak {petak_tujuan}. Aksi: {aksi}. Hadap: {sudut_hadap}°")
                            
                            robot.state.main_then = now
                            robot.state.main_state = "PUTAR_POSISI"
                            robot.state.main_temp_state = aksi 
                            
                    elif robot.state.main_state == "PUTAR_POSISI":
                        if (robot.sensor.kompas >= gerak.target_angle - 2 and robot.sensor.kompas <= gerak.target_angle + 2):
                            gerak.stop(robot)
                            if (now - robot.state.main_then > 0.1): 
                                robot.state.main_state = robot.state.main_temp_state 
                        else:
                            gerak.base_speed = 60
                            gerak.hadap_sudut(robot)
                            robot.state.main_then = now
                            
                    elif robot.state.main_state == "NAIK":
                        selesai = masukMainhua._proses_naik(robot, gerak)
                        if selesai:
                            print("[NAVIGASI] Naik Selesai.")
                            hutan.step_selesai() 
                            robot.state.main_state = "CEK_RUTE" 
                            
                    elif robot.state.main_state == "TURUN":
                        selesai = masukMainhua._proses_turun(robot, gerak)
                        if selesai:
                            print("[NAVIGASI] Turun Selesai.")
                            hutan.step_selesai() 
                            robot.state.main_state = "CEK_RUTE" 

                    elif robot.state.main_state == "DATAR":
                        print("[NAVIGASI] Rute Datar belum dibuat. Skip petak.")
                        hutan.step_selesai()
                        robot.state.main_state = "CEK_RUTE"

                    # ==============================================================
                    elif robot.state.main_state == "ZONA3":
                        selesai = zona3.logic_zona3(robot, gerak)
                        if selesai:
                            # Opsional: Kembali ke standby setelah tugas paling akhir selesai
                            # is_running = False 
                            pass # Biarkan atau lakukan aksi lain

                
                
                # 4. EKSTRAK DAN KIRIM KE ARDUINO DUE (Hanya dieksekusi jika sedang is_running)
                if is_running:
                    # gerak.maju(robot)
                    data_keluar = robot.motor.get_array_output()
                    
                    writer.kirim_data(data_keluar) 

           
           
           
           
            # 5. ISTIRAHAT CPU (Sangat penting agar terminal tidak freeze)
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        # ... (Biarkan bagian ini tetap seperti aslinya)
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
            
        # 3. Clean up GPIO pins
        try:
            tombol_jetson.cleanup()
            print("[FAILSAFE] GPIO Cleanup selesai.")
        except:
            pass
            
        print("Program selesai.")
        sys.exit(0)

if __name__ == "__main__":
    main()