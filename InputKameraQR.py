import cv2
import threading
import time
from pyzbar.pyzbar import decode

class DeteksiQR:
    def __init__(self, robot, tampilkan_video=False):
        self.robot = robot
        self.tampilkan_video = tampilkan_video
        self.berjalan = False
        self.qr_ditemukan = False 
        self.print_flag = False

    def start(self):
        """Memulai deteksi kamera di latar belakang (tidak memblokir program utama)"""
        if not self.berjalan:
            self.berjalan = True
            threading.Thread(target=self._loop_kamera, daemon=True).start()

    def _loop_kamera(self):
        print("[KAMERA QR] Menginisialisasi kamera...")
        cap = cv2.VideoCapture(0)

        # Setel resolusi anti-lag (Sangat Penting)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        if not cap.isOpened():
            print("[ERROR] Kamera tidak terdeteksi!")
            self.berjalan = False
            return

        # Pemanasan sensor
        for _ in range(5):
            cap.read()

        print("[KAMERA QR] Kamera SIAP. Selalu mendeteksi di background...")

        while self.berjalan:
            ret, frame = cap.read()
            if not ret:
                continue

            # Deteksi QR menggunakan PyZbar
            qrcodes = decode(frame)

            if qrcodes:
                barcode = qrcodes[0]
                data = "Qr Ditemukan"
                
                # Update data ke memori sensor robot secara real-time
                self.robot.sensor.data_qr = data
                self.qr_ditemukan = True 
                
                # Tampilkan log
                if not self.print_flag:
                    print(f"\n[KAMERA QR] Terdeteksi: {data}")
                    self.print_flag = True
                
                # Jika mode testing nyala, tampilkan kotak hijau
                if self.tampilkan_video:
                    (x, y, w, h) = barcode.rect
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
                    cv2.imshow("Scanner QR", frame)
                    cv2.waitKey(500) # Tahan gambar sebentar agar terlihat
            else:
                if self.print_flag:
                    print("[KAMERA QR] Tidak ada QR yang terdeteksi.")
                    self.print_flag = False
                self.robot.sensor.data_qr = "QR Tidak Ditemukan"
                self.qr_ditemukan = False

            # Menampilkan jendela video (HANYA saat mode testing)
            if self.tampilkan_video:
                cv2.imshow("Scanner QR", frame)
                # Tekan 'q' pada keyboard untuk mematikan mode testing
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("\n[KAMERA QR] Dibatalkan user via tombol 'q'.")
                    self.berjalan = False
                    break

        # Membersihkan hardware setelah selesai
        cap.release()
        if self.tampilkan_video:
            cv2.destroyAllWindows()
        print("[KAMERA QR] Kamera dimatikan.")

    def stop(self):
        """Mematikan kamera dari program utama"""
        self.berjalan = False


# =====================================================================
# BLOK PENGUJIAN STANDALONE (MANUAL TESTING)
# =====================================================================
if __name__ == "__main__":
    # Mock class (Robot Bohongan) untuk menampung data
    class MockRobot:
        class MockSensor:
            data_qr = "Kosong"
        sensor = MockSensor()

    robot_tiruan = MockRobot()
    
    # PENTING: Untuk pengujian manual, nyalakan fitur tampilkan_video
    qr_detector = DeteksiQR(robot_tiruan, tampilkan_video=False)

    try:
        print("\n[TESTING] Program dimulai.")
        print("[TESTING] Tekan Ctrl+C di terminal atau 'q' di video untuk keluar.")
        
        # Jalankan sensor di background
        qr_detector.start()
        
        # Karena start() berjalan di thread terpisah (paralel), kita harus 
        # menahan program utama agar tidak langsung tertutup
        while qr_detector.berjalan:
            time.sleep(1) # Tahan terminal selama status kamera masih berjalan
            
        # Mengeksekusi hasil akhir ketika loop di atas terputus
        print("\n=============================================")
        if qr_detector.qr_ditemukan:
            print(f"[TESTING SUKSES] Data di memori: '{robot_tiruan.sensor.data_qr}'")
        else:
            print("[TESTING GAGAL] QR tidak ditemukan / program dibatalkan.")
        print("=============================================\n")
            
    except KeyboardInterrupt:
        # Jika ditekan Ctrl + C pada terminal
        qr_detector.stop()
        print("\n[TESTING] Dihentikan paksa oleh user (Ctrl+C).")