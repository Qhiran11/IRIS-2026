import json
import os
import time

class ConfigManager:
    def __init__(self, filename="config.json"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.filepath = os.path.join(base_dir, filename)
        self.data = {}
        self.last_modified_time = 0
        self.last_check_time = 0
        
        # Load data saat pertama kali program dijalankan
        self.load_config()

    def load_config(self):
        """Membaca file JSON dengan aman."""
        if not os.path.exists(self.filepath):
            print(f"[CONFIG WARNING] File {self.filepath} tidak ditemukan. Pastikan file ada di direktori yang sama.")
            return

        try:
            with open(self.filepath, 'r') as file:
                new_data = json.load(file)
            
            # Jika berhasil diload, perbarui data di memori
            self.data = new_data
            self.last_modified_time = os.path.getmtime(self.filepath)
            print("[CONFIG] Berhasil memuat konfigurasi terbaru!")
            
        except json.JSONDecodeError as e:
            # Cegah program crash kalau kamu salah ketik koma/tanda kutip saat edit JSON di lapangan
            print(f"[CONFIG ERROR] Format JSON salah! Menggunakan nilai terakhir. Error: {e}")
        except Exception as e:
            print(f"[CONFIG ERROR] Terjadi kesalahan saat membaca config: {e}")

    def update(self):
        """Fungsi ini dipanggil di loop utama untuk mengecek perubahan file."""
        now = time.time()
        
        # Cek perubahan file hanya 1 kali setiap detik agar tidak memberatkan kinerja prosesor
        if now - self.last_check_time > 1.0:
            self.last_check_time = now
            try:
                if os.path.exists(self.filepath):
                    current_modified_time = os.path.getmtime(self.filepath)
                    # Jika waktu modifikasi file berubah (baru di-save), load ulang
                    if current_modified_time != self.last_modified_time:
                        print("[CONFIG] Perubahan file terdeteksi. Memperbarui nilai...")
                        self.load_config()
            except Exception as e:
                pass


    def save_config(self):
        """Menulis ulang seluruh data konfigurasi saat ini kembali ke file JSON secara aman."""
        try:
            with open(self.filepath, 'w') as file:
                # json.dump akan mengubah data dictionary kembali menjadi teks format JSON yang rapi (indent=4)
                json.dump(self.data, file, indent=4)
            # Update waktu modifikasi agar ConfigManager tahu ini versi paling baru
            self.last_modified_time = os.path.getmtime(self.filepath)
            print("[CONFIG] Berhasil menyimpan perubahan otomatis ke file!")
        except Exception as e:
            print(f"[CONFIG ERROR] Gagal menyimpan file: {e}")