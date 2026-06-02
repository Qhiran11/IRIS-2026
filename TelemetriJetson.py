# File: TelemetriJetson.py
import socket
import threading
import json
import random
import string
import time

class TelemetryServer:
    def __init__(self, port=5005):
        self.port = port
        # Generate 4 Karakter Token secara acak (Huruf & Angka)
        # self.token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        self.token = "IRIS"
        self.berjalan = False
        self.client_socket = None
        self.latest_data = None
        self.data_lock = threading.Lock()

        # Setup UDP untuk Broadcast (Agar komputer monitor menemukan IP Jetson)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # Setup TCP untuk pengiriman Data Robot
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_socket.bind(('0.0.0.0', self.port))
        self.tcp_socket.listen(1)

    def start(self):
        self.berjalan = True
        print(f"\n========================================")
        print(f"[TELEMETRI] Server Aktif!")
        print(f"[TELEMETRI] TOKEN KONEKSI ANDA: {self.token}")
        print(f"========================================\n")
        
        # Jalankan di background agar tidak membebani ProsesUtama.py
        threading.Thread(target=self._broadcast_token, daemon=True).start()
        threading.Thread(target=self._terima_koneksi, daemon=True).start()
        threading.Thread(target=self._kirim_data_loop, daemon=True).start()

    def _broadcast_token(self):
        while self.berjalan:
            # Format Teriakan UDP: NANOPA:<TOKEN>:<PORT>
            pesan = f"NANOPA:{self.token}:{self.port}"
            try:
                # Kirim ke seluruh perangkat di jaringan (Broadcast)
                self.udp_socket.sendto(pesan.encode('utf-8'), ('255.255.255.255', 5006))
            except Exception:
                pass
            time.sleep(1) # Broadcast setiap 1 detik

    def _terima_koneksi(self):
        while self.berjalan:
            try:
                conn, addr = self.tcp_socket.accept()
                print(f"[TELEMETRI] Komputer Monitor Terhubung dari IP: {addr[0]}")
                self.client_socket = conn
            except Exception:
                pass

    def _kirim_data_loop(self):
        while self.berjalan:
            client = self.client_socket
            if client:
                data_to_send = None
                with self.data_lock:
                    if self.latest_data:
                        data_to_send = self.latest_data
                
                if data_to_send:
                    try:
                        # Ubah ke JSON dan kirim ke komputer monitor
                        pesan = json.dumps(data_to_send) + "\n"
                        client.sendall(pesan.encode('utf-8'))
                    except Exception:
                        # Jika komputer monitor terputus
                        try:
                            client.close()
                        except Exception:
                            pass
                        if self.client_socket == client:
                            self.client_socket = None
            time.sleep(0.05) # Batasi pengiriman telemetry ke 20 Hz (setiap 50ms)

    def kirim_data(self, robot):
        # Ambil data robot secara cepat (non-blocking)
        data = {
            "Sensor": {k: v for k, v in robot.sensor.__dict__.items() if not k.startswith('_')},
            "Motor": {k: v for k, v in robot.motor.__dict__.items() if not k.startswith('_')},
            "Status Robot": {
                "Main State": robot.state.main_state,
                "Rakit State": robot.state.rakit_state,
                "Naik Turun State": robot.state.naikturun_state,
                "Zona 3 State": robot.state.zona3_state,
                "KFS State": robot.state.kfs_state,
                "Gerakan Dasar Aktif": robot.state.gerak_dasar_aktif,
            }
        }
        with self.data_lock:
            self.latest_data = data

    def stop(self):
        self.berjalan = False
        if self.client_socket: self.client_socket.close()
        self.tcp_socket.close()
        self.udp_socket.close()