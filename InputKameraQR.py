import cv2
import time

class DeteksiQR:
    def __init__(self, robot, tampilkan_video=False):
        self.robot = robot
        self.tampilkan_video = tampilkan_video
        self.detector = cv2.QRCodeDetector()
        self.qr_ditemukan = False 

    def jalankan(self):
        print("[KAMERA QR] Menginisialisasi kamera...")
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("[ERROR] Kamera tidak terdeteksi!")
            return

        # Pemanasan sensor lebih cepat (tanpa time.sleep yang memblokir program)
        for _ in range(5):
            cap.read()

        print("[KAMERA QR] Kamera SIAP. Mulai mendeteksi...")

        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            # Deteksi QR Code
            data, _, _ = self.detector.detectAndDecode(frame)

            # Jika QR terbaca
            if data:
                self.robot.sensor.data_qr = data
                print(f"[KAMERA QR] Instruksi Masuk: {data}")
                self.qr_ditemukan = True 
                break # Langsung keluar loop

            # Tampilan Video
            if self.tampilkan_video:
                cv2.imshow("Scanner QR", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("[KAMERA QR] Dibatalkan user.")
                    break
            else:
                time.sleep(0.01) # Cukup 10ms agar CPU tidak 100%, tapi deteksi tetap instan

        cap.release()
        if self.tampilkan_video:
            cv2.destroyAllWindows()
        print("[KAMERA QR] Kamera dimatikan.")


# =====================================================================
# BLOK PENGUJIAN STANDALONE 
# =====================================================================
if __name__ == "__main__":
    # Mock class disederhanakan
    class MockRobot:
        class MockSensor:
            data_qr = "https://res.cloudinary.com/drbivi2n4/image/upload/v1780206749/7a75927b-dab7-4057-9c01-7c4eca87824b.png"
        sensor = MockSensor()

    robot_tiruan = MockRobot()
    qr_detector = DeteksiQR(robot_tiruan, tampilkan_video=True)

    try:
        print("\n[TESTING] Program dimulai...")
        qr_detector.jalankan()
        
        print("\n=============================================")
        if qr_detector.qr_ditemukan:
            print(f"[TESTING SUKSES] Data di memori: '{robot_tiruan.sensor.data_qr}'")
        else:
            print("[TESTING GAGAL] QR tidak ditemukan / program dibatalkan.")
        print("=============================================\n")
            
    except KeyboardInterrupt:
        print("\n[TESTING] Dihentikan paksa oleh user.")