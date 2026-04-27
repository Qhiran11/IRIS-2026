import cv2

import numpy as np



class OpticalEncoder:

    def __init__(self, sensitivity=1.0, deadzone=0.5):

        # State awal

        self.x = 0.0

        self.y = 0.0

        

        # Konfigurasi

        self.sensitivity = sensitivity # Pengali kecepatan

        self.deadzone = deadzone       # Mengabaikan noise kecil agar tidak drift

        

        # Setup untuk Optical Flow

        self.prev_frame = None

        self.compress_w = 80

        self.compress_h = 60

        self.block_size = 8

        self.search_range = 12



    def update(self, frame):

        """

        Input: Frame dari kamera (BGR)

        Output: Tuple (x, y) koordinat terkini

        """

        # Resize dan grayscale untuk efisiensi

        frame_small = cv2.resize(frame, (self.compress_w, self.compress_h))

        gray = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)



        if self.prev_frame is None:

            self.prev_frame = gray

            return self.x, self.y



        # Menghitung delta gerak (optical flow)

        dx, dy = self._calculate_delta(self.prev_frame, gray)



        # Terapkan deadzone dan sensitivity

        # Jika perubahan terlalu kecil, dianggap 0 (statis)

        if abs(dx) < self.deadzone: dx = 0

        if abs(dy) < self.deadzone: dy = 0



        # Akumulasi ke koordinat (Logika Rotary Encoder)

        self.x += (dx * self.sensitivity)

        self.y += (dy * self.sensitivity)



        self.prev_frame = gray

        return self.x, self.y



    def reset(self):

        """Reset koordinat kembali ke 0,0"""

        self.x = 0.0

        self.y = 0.0



    def _calculate_delta(self, old_img, new_img):

        # Menggunakan grid 3x3 untuk estimasi gerakan global

        points = [

            (18, 12), (36, 12), (54, 12),

            (18, 28), (36, 28), (54, 28),

            (18, 44), (36, 44), (54, 44)

        ]



        total_dx, total_dy = 0, 0

        

        for (sx, sy) in points:

            best_dx, best_dy = 0, 0

            min_sad = float('inf')

            

            # Batas pencarian

            block_old = old_img[sy:sy+self.block_size, sx:sx+self.block_size]

            

            # Pencarian blok matching

            # Catatan: Dalam produksi nyata, gunakan cv2.calcOpticalFlowFarneback untuk kecepatan

            for dy in range(-self.search_range, self.search_range + 1):

                for dx in range(-self.search_range, self.search_range + 1):

                    # Clamp index agar tidak out of bounds

                    ny, nx = sy + dy, sx + dx

                    if ny < 0 or nx < 0 or ny+self.block_size > self.compress_h or nx+self.block_size > self.compress_w:

                        continue

                        

                    block_new = new_img[ny:ny+self.block_size, nx:nx+self.block_size]

                    sad = np.sum(np.abs(block_old.astype(np.int32) - block_new.astype(np.int32)))

                    

                    if sad < min_sad:

                        min_sad = sad

                        best_dx, best_dy = dx, dy

            

            total_dx += best_dx

            total_dy += best_dy



        return total_dx / len(points), total_dy / len(points)



# Contoh penggunaan:

# encoder = OpticalEncoder(sensitivity=1.0, deadzone=0.7)

# cap = cv2.VideoCapture(2, cv2.CAP_DSHOW)

# cap = cv2.VideoCapture(0)

# while True:

#     _, frame = cap.read()
#     pos_x, pos_y = encoder.update(frame)
#     print(f"Posisi: X={pos_x:.2f}")