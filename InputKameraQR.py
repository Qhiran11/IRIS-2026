import cv2
import time

class DeteksiQR:
    def __init__(self, robot, tampilkan_video=False):
        """
        Inisialisasi Sensor QR Code (Tanpa Thread).
        :param robot: Referensi ke class memori utama robot
        :param tampilkan_video: Jika True, munculkan jendela OpenCV untuk testing
        """
        self.satu = 0
        self.robot = robot
        self.tampilkan_video = tampilkan_video
        self.detector = cv2.QRCodeDetector()
        
        # Sinyal bahwa tugas selesai
        self.qr_ditemukan = False 

    def jalankan(self):
        """Memulai kamera dan memblokir program utama sampai QR Code ditemukan."""
        print("[KAMERA QR] Menginisialisasi kamera...")
        cap = cv2.VideoCapture(0)

        # 1. Pastikan hardware kamera bisa diakses
        if not cap.isOpened():
            print("[ERROR] Kamera tidak terdeteksi atau gagal dibuka!")
            return

        # 2. Pemanasan Sensor (Wajib agar tidak ada frame gelap/ngelag di awal)
        print("[KAMERA QR] Memanaskan sensor kamera...")
        for _ in range(10):
            cap.read()
            time.sleep(0.1)

        print("[KAMERA QR] Kamera SIAP. Mulai mendeteksi QR Code...")

        # 3. Looping Utama (Akan menahan baris kode lain di luar fungsi ini)
        while True:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            # Deteksi QR Code
            data, bbox, _ = self.detector.detectAndDecode(frame)
            
            # Gambar garis kotak hijau pada QR Code di layar (Opsional)
            if bbox is not None and self.tampilkan_video:
                n_lines = len(bbox[0])
                for i in range(n_lines):
                    pt1 = tuple(map(int, bbox[0][i]))
                    pt2 = tuple(map(int, bbox[0][(i+1) % n_lines]))
                    cv2.line(frame, pt1, pt2, color=(0, 255, 0), thickness=2)

            # --- LOGIKA: JIKA QR DITEMUKAN ---
            if data:
                self.robot.sensor.data_qr = data
                # print(f"[KAMERA QR] Instruksi Masuk: {data}")
                self.satu += 1
                print(f"jumlah data = {self.satu}")
                self.qr_ditemukan = True 
                # break # Keluar dari loop kamera

            # --- TAMPILAN JENDELA ---
            if self.tampilkan_video:
                cv2.imshow("Kamera Scanner QR", frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("[KAMERA QR] Dibatalkan oleh user.")
                    break
            else:
                # Jeda agar tidak boros CPU jika tanpa jendela
                time.sleep(0.05)

        # 4. Bersihkan resource karena QR sudah ketemu atau user menekan 'q'
        cap.release()
        if self.tampilkan_video:
            cv2.destroyAllWindows()
        print("[KAMERA QR] Kamera dimatikan.")


# =====================================================================
# BLOK PENGUJIAN STANDALONE 
# =====================================================================
if __name__ == "__main__":
    # 1. Class Tiruan (Mock)
    class MockSensor:
        def __init__(self):
            self.data_qr = "Testing Nanopa" # Kosongkan awal

    class MockRobot:
        def __init__(self):
            self.sensor = MockSensor()

    robot_tiruan = MockRobot()
    
    # 2. Inisialisasi
    qr_detector = DeteksiQR(robot_tiruan, tampilkan_video=True)

    try:
        print("\n[TESTING] Program dimulai. Bersiap menyalakan kamera...")
        
        # 3. Jalankan Kamera
        # Program akan TERTENTI (berhenti) di baris ini sampai QR terbaca
        qr_detector.jalankan()
        
        # 4. Baris program selanjutnya (Hanya jalan setelah fungsi di atas selesai)
        print("\n=============================================")
        print("[TESTING] Pengecekan setelah kamera mati...")
        if qr_detector.qr_ditemukan:
            print(f"[TESTING SUKSES] Data terkunci di memori: '{robot_tiruan.sensor.data_qr}'")
            print("[TESTING] Melanjutkan ke baris program robot selanjutnya (misal: Robot bergerak...)")
        else:
            print("[TESTING GAGAL] Program selesai tetapi QR tidak ditemukan (Mungkin dibatalkan manual).")
        print("=============================================\n")
            
    except KeyboardInterrupt:
        print("\n[TESTING] Dihentikan paksa oleh user.")