# File: InputKamera.py
import cv2
import imutils
import threading
import time
from imutils.video import VideoStream

# Fungsi kosong untuk callback trackbar OpenCV
def nothing(x):
    pass

class KameraSensor:
    def __init__(self, robot_sensor, tampilkan_video=False):
        """
        Inisialisasi Kamera sebagai Sensor Background.
        :param robot_sensor: Mengambil referensi dari robot.sensor (memori utama)
        :param tampilkan_video: Set True untuk debugging (akan menampilkan jendela OpenCV & Slider)
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
        # Jika mode kalibrasi aktif, buat Jendela Khusus Slider
        if self.tampilkan_video:
            cv2.namedWindow("Trackbars")
            # OpenCV menggunakan range H: 0-179, S: 0-255, V: 0-255
            cv2.createTrackbar("H_min", "Trackbars", 0, 179, nothing)
            cv2.createTrackbar("S_min", "Trackbars", 0, 255, nothing)
            cv2.createTrackbar("V_min", "Trackbars", 100, 255, nothing)
            cv2.createTrackbar("H_max", "Trackbars", 179, 179, nothing)
            cv2.createTrackbar("S_max", "Trackbars", 60, 255, nothing)
            cv2.createTrackbar("V_max", "Trackbars", 255, 255, nothing)

        while self.berjalan:
            frame = self.vs.read()
            if frame is None:
                continue

            # 1. Ambil Nilai HSV (Dari Slider jika aktif, atau Default jika tidak)
            if self.tampilkan_video:
                H_min = cv2.getTrackbarPos("H_min", "Trackbars")
                S_min = cv2.getTrackbarPos("S_min", "Trackbars")
                V_min = cv2.getTrackbarPos("V_min", "Trackbars")
                H_max = cv2.getTrackbarPos("H_max", "Trackbars")
                S_max = cv2.getTrackbarPos("S_max", "Trackbars")
                V_max = cv2.getTrackbarPos("V_max", "Trackbars")
            else:
                # Nilai default kalibrasi arena Anda
                H_min, S_min, V_min = 0, 0, 100
                H_max, S_max, V_max = 179, 60, 255

            orangeLower = (H_min, S_min, V_min)
            orangeUpper = (H_max, S_max, V_max)

            # 2. Proses Penyesuaian Gambar
            frame = imutils.resize(frame, width=800, height=600)
            blurred = cv2.GaussianBlur(frame, (11, 11), 0)
            hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

            mask = cv2.inRange(hsv, orangeLower, orangeUpper)
            mask = cv2.erode(mask, None, iterations=2)
            mask = cv2.dilate(mask, None, iterations=2)

            cnts = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)

            center = None

            # 3. Hanya Melacak SATU OBJEK TERBESAR
            if len(cnts) > 0:
                c = max(cnts, key=cv2.contourArea)
                ((x, y), radius) = cv2.minEnclosingCircle(c)
                M = cv2.moments(c)
                
                if M["m00"] > 0:
                    center = (int(M['m10'] / M['m00']), int(M['m01'] / M['m00']))

                if radius > 10:
                    # UPDATE MEMORI ROBOT (Hanya Titik Koordinat X dan Y)
                    self.sensor.bola_terdeteksi = True
                    self.sensor.bola_x = center[0]
                    self.sensor.bola_y = center[1]

                    # Visualisasi Tampilan Jendela
                    if self.tampilkan_video:
                        cv2.circle(frame, (int(x), int(y)), int(radius), (255, 255, 0), 2)
                        cv2.circle(frame, center, 5, (255, 255, 0), -1)
                        cv2.putText(frame, f"X:{center[0]} Y:{center[1]}", (center[0]+10, center[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            else:
                self.sensor.bola_terdeteksi = False
                self.sensor.bola_x = 0
                self.sensor.bola_y = 0

            # --- TAMPILAN JENDELA (Hanya jika tampilkan_video=True) ---
            if self.tampilkan_video:
                cv2.line(frame, (0, self.target_y), (800, self.target_y), (0, 0, 255), 1)
                cv2.line(frame, (self.target_x, 0), (self.target_x, 600), (0, 0, 255), 1)
                
                cv2.imshow("frame", frame)
                cv2.imshow("mask", mask)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    self.stop()
            else:
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
    class DummySensor:
        def __init__(self):
            self.bola_terdeteksi = False
            self.bola_x = 0
            self.bola_y = 0

    sensor_robot_dummy = DummySensor()

    # Aktifkan tampilkan_video=True untuk memunculkan window & slider kalibrasi
    kamera = KameraSensor(sensor_robot_dummy, tampilkan_video=True)

    try:
        kamera.start()
        
        while True:
            if sensor_robot_dummy.bola_terdeteksi:
                print(f"[TESTING] OBJEK KETEMU! Koordinat -> X: {sensor_robot_dummy.bola_x} | Y: {sensor_robot_dummy.bola_y}")
            else:
                print("[TESTING] Mencari objek...")
            
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n[TESTING] Dihentikan oleh user.")
    
    finally:
        kamera.stop()