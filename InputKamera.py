# File: InputKamera.py
import cv2
import imutils
import threading
import time
from imutils.video import VideoStream

class KameraSensor:
    def __init__(self, robot_sensor, tampilkan_video=False):
        """
        Inisialisasi Kamera sebagai Sensor Background.
        :param robot_sensor: Mengambil referensi dari robot.sensor (memori utama)
        :param tampilkan_video: Set True untuk debugging (akan menampilkan jendela OpenCV)
        """
        self.sensor = robot_sensor
        self.tampilkan_video = tampilkan_video
        self.berjalan = False
        
        # Target crosshair di tengah layar
        self.target_x = 400 # Titik tengah frame (karena lebar 800)
        self.target_y = 300 # Titik tengah frame (karena tinggi 600)
        
        self.vs = None
        self.thread = None

    def start(self):
        print("[KAMERA] Memulai pemanasan sensor kamera...")
        # Gunakan src=0 untuk kamera USB pertama. Sesuaikan jika pakai CSI Jetson.
        self.vs = VideoStream(src=0).start()
        time.sleep(2.0) # Wajib: pemanasan buffer kamera
        
        self.berjalan = True
        # Memulai OpenCV di thread terpisah agar tidak membebani ProsesUtama.py
        self.thread = threading.Thread(target=self.update, args=())
        self.thread.daemon = True # Thread otomatis mati saat program utama dihentikan
        self.thread.start()
        print("[KAMERA] Sensor kamera berhasil berjalan di background.")

    def update(self):
        # Konfigurasi WARNA (Wajib dikalibrasi di arena Anda)
        # Nilai HSV untuk bola orange (sesuaikan jika perlu)
        H_min, S_min, V_min = 0, 150, 100
        H_max, S_max, V_max = 25, 255, 255
        
        orangeLower = (H_min, S_min, V_min)
        orangeUpper = (H_max, S_max, V_max)

        while self.berjalan:
            frame = self.vs.read()
            if frame is None:
                continue

            # 1. Proses Penyesuaian Gambar
            frame = imutils.resize(frame, width=800, height=600)
            blurred = cv2.GaussianBlur(frame, (11, 11), 0)
            hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

            mask = cv2.inRange(hsv, orangeLower, orangeUpper)
            mask = cv2.erode(mask, None, iterations=2)
            mask = cv2.dilate(mask, None, iterations=2)

            cnts = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)

            center = None

            # 2. Hanya Melacak SATU OBJEK TERBESAR
            if len(cnts) > 0:
                c = max(cnts, key=cv2.contourArea)
                ((x, y), radius) = cv2.minEnclosingCircle(c)
                M = cv2.moments(c)
                
                if M["m00"] > 0:
                    center = (int(M['m10'] / M['m00']), int(M['m01'] / M['m00']))

                if radius > 10:
                    # 3. UPDATE MEMORI ROBOT (Hanya Titik Koordinat X dan Y)
                    self.sensor.bola_terdeteksi = True
                    self.sensor.bola_x = center[0]
                    self.sensor.bola_y = center[1]

                    # 4. Visualisasi Tampilan Jendela
                    if self.tampilkan_video:
                        # Lingkaran pelacak dan titik tengah: CYAN (Biru Muda)
                        cv2.circle(frame, (int(x), int(y)), int(radius), (255, 255, 0), 2)
                        cv2.circle(frame, center, 5, (255, 255, 0), -1)
                        # Opsi tambahan: Print posisi (x,y) di atas objek agar mudah terbaca di video
                        cv2.putText(frame, f"X:{center[0]} Y:{center[1]}", (center[0]+10, center[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            else:
                # Jika tidak ada bola, reset nilai koordinat
                self.sensor.bola_terdeteksi = False
                self.sensor.bola_x = 0
                self.sensor.bola_y = 0

            # --- TAMPILAN JENDELA (Hanya jika tampilkan_video=True) ---
            if self.tampilkan_video:
                # Menambahkan Crosshair (tanda tambah) Merah di tengah frame
                cv2.line(frame, (0, self.target_y), (800, self.target_y), (0, 0, 255), 1)
                cv2.line(frame, (self.target_x, 0), (self.target_x, 600), (0, 0, 255), 1)
                
                # Menampilkan kedua jendela: frame dan mask
                cv2.imshow("frame", frame)
                cv2.imshow("mask", mask)
                
                # Menggantikan fungsi 'keyboard' agar aman di Linux Jetson
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    self.stop()
            else:
                # Memberi sedikit jeda istirahat untuk CPU Jetson jika window tidak ditampilkan
                time.sleep(0.01)

    def stop(self):
        print("[KAMERA] Mematikan sensor kamera...")
        self.berjalan = False
        if self.vs is not None:
            self.vs.stop()
        if self.tampilkan_video:
            cv2.destroyAllWindows()

# =====================================================================
# BLOK PENGUJIAN STANDALONE (Hanya berjalan jika file ini di-run langsung)
# =====================================================================
if __name__ == "__main__":
    # Buat tiruan memori robot dengan menghapus variabel PID
    class DummySensor:
        def __init__(self):
            self.bola_terdeteksi = False
            self.bola_x = 0
            self.bola_y = 0

    sensor_robot_dummy = DummySensor()

    # Aktifkan tampilkan_video=True untuk melihat hasilnya
    kamera = KameraSensor(sensor_robot_dummy, tampilkan_video=True)

    try:
        kamera.start()
        
        while True:
            if sensor_robot_dummy.bola_terdeteksi:
                # Print hanya nilai koordinat
                print(f"[TESTING] BOLA KETEMU! Koordinat -> X: {sensor_robot_dummy.bola_x} | Y: {sensor_robot_dummy.bola_y}")
            else:
                print("[TESTING] Mencari bola...")
            
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n[TESTING] Dihentikan oleh user.")
    
    finally:
        kamera.stop()