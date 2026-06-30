# File: ProsesUtama.py
import sys
import os
import time
import cv2
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Input import SensorReader
from Output import ArduinoDueWriter
from data_robot.robot_data import Robot
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


def hard_restart_sistem(sensor, writer, kamera, tombol_jetson, gerak, robot):
    print("\n[SYSTEM] MELAKUKAN HARD RESTART! Menginisialisasi ulang seluruh program...")
    
    # 1. Pastikan robot berhenti sebelum mati
    try:
        gerak.stop(robot)
        writer.kirim_data(robot.motor.get_array_output())
        time.sleep(0.1)
    except:
        pass

    # 2. Lepaskan semua resource hardware (SANGAT KRUSIAL)
    try:
        print("[RESTART] Menutup Serial Port...")
        # Pastikan class SensorReader dan ArduinoDueWriter Anda memiliki method .close()
        # Jika belum ada, Anda harus menambahkannya di file Input.py dan Output.py
        sensor.close() 
        writer.close() 
        
        print("[RESTART] Mematikan Kamera...")
        kamera.stop()
        
        print("[RESTART] Membersihkan GPIO...")
        tombol_jetson.cleanup()
    except Exception as e:
        print(f"[RESTART] Peringatan saat menutup hardware: {e}")
        
    print("[RESTART] Memulai ulang script dalam 1 detik...")
    time.sleep(1)
    
    # 3. Eksekusi ulang program
    python = sys.executable
    os.execv(python, ['python'] + sys.argv)


def main():
    print("Memulai Program Utama KRAI...")
    # ... (print logo Anda) ...

    robot = Robot()
 
    # --- INISIALISASI TELEMETRI ---
    telemetri = TelemetryServer()
    telemetri.start()
    # ------------------------------
    
    port_sensor = '/dev/ttyUSB0'   # Arduino Mega
    port_writer = '/dev/ttyACM0'   # Arduino Due

    # --- MONITORING SENSOR (INPUT) ---
    if os.path.exists(port_sensor):
        sensor = SensorReader(port=port_sensor, baudrate=115200)
        robot.InputTerhubung = True
        print("[INFO] Kabel Sensor terhubung di", port_sensor)
    else:
        sensor = None
        robot.InputTerhubung = False
        print("[WARNING] Kabel Sensor TIDAK terhubung!")

    # --- MONITORING WRITER (OUTPUT) ---
    if os.path.exists(port_writer):
        writer = ArduinoDueWriter(port=port_writer, baudrate=115200)
        robot.OutputTerhubung = True  # Tambahkan atribut ini di class Robot jika belum ada
        print("[INFO] Kabel Writer terhubung di", port_writer)
    else:
        writer = None
        robot.OutputTerhubung = False
        print("[WARNING] Kabel Writer TIDAK terhubung!")
    

    arena = MappingArena()
    hutan = MappingHutan()

    arena.jumlah_Naik = 3

 
    gerak = GerakanDasar()
    rakit = RakitSenjata()
    ambil_kfs = GerakanAmbilKFS() # Inisialisasi Otak Kecil
    masukMainhua = GerakanNaikTurun()
    zona3 = Zona3()

    # kamera = KameraSensor(robot.sensor, tampilkan_video=False)
    kamera = DeteksiQR(robot, tampilkan_video=False)
    kamera.start()
    
    is_running = False # Flag penanda apakah robot sedang standby atau running

    try:
        while True:
            robot.config.update() # Perbarui konfigurasi dari file secara dinamis
            array_input = sensor.baca_data()
            telemetri.kirim_data(robot)
            now = time.time()
            if array_input is not None:
                robot.sensor.update_dari_array(array_input) # Update memori robot
                if not is_running:
                    gerak.target_angle = 0
                    gerak.stop(robot)
                    # robot.motor.CapitTombakJepit = 0
                    # robot.motor.mDorong1 = 255 # BELAKANG
                    # robot.motor.mDorong2 = 255 # DEPAN
                    # gerak.penyeimbang(robot, now)
                    
                    
                    # gerak.geser_ke_titik_kanan(robot, 160, now)
                    # gerak.turun_roda2( robot)
                    # robot.motor.mDorong1 = -200
                    # robot.motor.CapitTombakNaikTurun = 1
                    # gerak.naikTurunBiasa(robot, 14)
                    gerak.turun_ke_titk(robot, robot.config.data.get("umum", {}).get("Tinggi"))
                    # gerak.naikTurunBiasa(robot,21)
                    # gerak.mundur(robot)
                    
                    data_keluar = robot.motor.get_array_output()                    
                    writer.kirim_data(data_keluar)
                    # robot.motor.CapitTombakNaikTurun = 1
                    # robot.motor.relayCapitKFSJepit = 0
                    # LOGIKA: Tahan di sini hingga tombol start ditekan
                    if robot.sensor.tombol_start == 0:
                        print("\n[SYSTEM] TOMBOL START DITEKAN! Memulai program...")
                        robot.ROBOT_MAIN_STATE = "START"
                        if robot.state.main_state == "FASE2":
                            robot.state.main_state = "GOGO"
                        else:
                            robot.state.reset_all() # Reset semua state ke kondisi awal
                        robot.sensor.switch = 0
                        gerak.target_angle = 0
                        robot.motor.CapitTombakNaikTurun = 0
                        robot.motor.CapitTombakJepit = 1
                        is_running = True       # Ubah mode menjadi Running
                        continue # Skip semua logika di bawah, kembali ke awal while
                    if robot.sensor.tombol_reset == 0:
                        print("\n[SYSTEM] MASTER RESET DITEKAN! Kembali ke Standby...")
                        robot.ROBOT_MAIN_STATE = "STANDBY"
                        robot.state.reset_all()
                        gerak.stop(robot)
                        kamera.start()
                        robot.motor.CapitTombakNaikTurun = 0
                        robot.motor.CapitTombakJepit = 1
                        writer.kirim_data(robot.motor.get_array_output()) # Paksa motor mati
                        robot.sensor.switch = 0
                        gerak.target_angle = 0
                        robot.sensor.update_dari_array(array_input) # Update memori robot
                        is_running = False # Kembalikan program ke fase Standby
                        continue # Langsung melompat kembali ke awal loop

                else:
                    if robot.sensor.tombol_reset == 0:
                        print("\n[SYSTEM] MASTER RESET DITEKAN! Kembali ke Standby...")
                        robot.ROBOT_MAIN_STATE = "STANDBY"
                        robot.state.reset_all()
                        gerak.stop(robot)
                        kamera.start()
                        robot.motor.CapitTombakNaikTurun = 0
                        robot.motor.CapitTombakJepit = 1
                        writer.kirim_data(robot.motor.get_array_output()) # Paksa motor mati
                        robot.sensor.switch = 0
                        gerak.target_angle = 0
                        robot.sensor.update_dari_array(array_input) # Update memori robot
                        is_running = False # Kembalikan program ke fase Standby
                        continue # Langsung melompat kembali ke awal loop
                        
                    # --- LOGIKA STATE MACHINE UTAMA ---
                    if robot.state.main_state == "READY":
                        gerak.stop(robot)
                        if (now - robot.state.main_then > 0.1):
                            robot.state.main_state = "GO"
                            # robot.state.main_state = "GOGO"
                            # robot.state.main_state = "NAIK"
                            # robot.state.main_state = "TURUN"
                            
                            # robot.state.main_state = "AMBILKFS"
                            robot.state.main_then = now
                
                    elif robot.state.main_state == "GO":
                        selesai = rakit.jalankan(robot, gerak, now)
                        # selesai = masukMainhua._proses_ke_tengah(robot, gerak, now)
                        if selesai:
                            robot.state.main_state = "FASE2"
                            robot.state.main_then = now
                            is_running = False
                            
                    elif robot.state.main_state == "GOGO":
                        
                        selesai = masukMainhua._proses_ke_tengah(robot, gerak, now)
                        if selesai:
                            robot.state.main_state = "NAIK"
                            gerak.stop(robot)
                            robot.state.main_then = now

                    elif robot.state.main_state == "AMBILKFS":
                        selesai = ambil_kfs.AmbilKFS(robot, gerak, now)
                        if selesai:
                            if robot.totalNaik == 1:
                                robot.state.main_state = "NAIK"
                            else:
                                robot.state.main_state = "PUTAR"
                            # return
        
                    elif robot.state.main_state == "NAIK":
                        selesai = masukMainhua._proses_naik(robot, gerak)
                        
                        if selesai:
                            robot.totalNaik += 1
                            print("[NAVIGASI] Naik Selesai.")
                            hutan.step_selesai() 
                            robot.state.main_state = "AMBILKFS" 

                    elif robot.state.main_state == "PUTAR":
                        gerak.target_angle = -90
                        selesai = gerak.hadap_sudut(robot, now)
                        if selesai:
                            robot.state.main_state = "TURUN"

                    elif robot.state.main_state == "TURUN":
                        selesai = masukMainhua._proses_turun(robot, gerak)
                        if selesai:
                            print("[NAVIGASI] Naik Selesai.")
                            robot.state.main_state = "PUTAR1"
                    elif robot.state.main_state == "PUTAR1":
                        gerak.target_angle = 0
                        selesai = gerak.hadap_sudut(robot, now)
                        if selesai:
                            robot.state.main_state = "NAIK1"
                    
                    elif robot.state.main_state == "NAIK1":
                        selesai = masukMainhua._proses_naik2(robot, gerak)
                        if selesai:
                            robot.state.main_state = "PUTAR2"

                    elif robot.state.main_state == "PUTAR2":
                        gerak.target_angle = -180
                        selesai = gerak.hadap_sudut(robot, now)
                        if selesai:
                            robot.state.main_state = "TURUN1"

                    elif robot.state.main_state == "TURUN1":
                        selesai = masukMainhua._proses_turun(robot, gerak)
                        if selesai:
                            robot.state.main_state = "TURUN2" 

                    elif robot.state.main_state == "TURUN2":
                        selesai = masukMainhua._proses_turun(robot, gerak)
                        if selesai:
                            robot.state.main_state = "PUTAR3"

                    elif robot.state.main_state == "PUTAR3":
                        gerak.target_angle = 0
                        selesai = gerak.hadap_sudut(robot, now)
                        if selesai:
                            robot.state.main_state = "ZONA3START"
                    
                    elif robot.state.main_state == "ZONA3START":
                        selesai = zona3.logic_zona3(robot, gerak, now)
                        if selesai:
                            robot.state.main_state = "FINISHED"
                
                
                # 4. EKSTRAK DAN KIRIM KE ARDUINO DUE (Hanya dieksekusi jika sedang is_running)
                if is_running:
                    # gerak.maju(robot)
                    data_keluar = robot.motor.get_array_output()
                    
                    writer.kirim_data(data_keluar) 

           
           
           
           
            # 5. ISTIRAHAT CPU (Sangat penting agar terminal tidak freeze)
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\n[FAILSAFE] Terminal dihentikan paksa (Ctrl+C)!")
    except Exception as e:
        print(f"\n[FAILSAFE] Terjadi Error Sistem: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("[FAILSAFE] Mematikan semua motor...")
        gerak.stop(robot)
        robot.motor.capit_jepit = 0
        try:
            writer.kirim_data(robot.motor.get_array_output())
            print("[FAILSAFE] Data stop berhasil dikirim ke roda.")
        except:
            print("[FAILSAFE] Gagal mengirim data stop (kabel mungkin terputus).")
            
        try:
            tombol_jetson.cleanup()
            print("[FAILSAFE] GPIO Cleanup selesai.")
        except:
            pass
            
        print("Program selesai.")
        sys.exit(0)

if __name__ == "__main__":
    main()