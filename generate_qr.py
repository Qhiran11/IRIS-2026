import qrcode
from fpdf import FPDF
import os

print("=== GENERATOR QR CODE TIM NANOPA 2026 ===")

# 1. Meminta input kalimat dari Anda saat program dijalankan
data_qr = input("Masukkan kalimat atau instruksi untuk QR Code: ")

# 2. Membuat logika QR Code
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=10,
    border=4,
)
qr.add_data(data_qr)
qr.make(fit=True)

# Membuat gambar sementara
img = qr.make_image(fill_color="black", back_color="white")
nama_gambar = "temp_qr.png"
img.save(nama_gambar)

# 3. Membuat struktur file PDF
pdf = FPDF()
pdf.add_page()

# Menambahkan Judul
pdf.set_font("Arial", size=16, style='B')
pdf.cell(200, 10, txt="QR Code - Tim NANOPA 2026", ln=True, align='C')
pdf.ln(10)

# Menempelkan Gambar QR Code ke posisi tengah
# A4 memiliki lebar 210mm. Posisi x=65 dan lebar=80mm akan membuatnya tepat di tengah.
pdf.image(nama_gambar, x=65, y=40, w=80)

# Menambahkan isi kalimat ke bagian bawah gambar
# pdf.set_y(130)
# pdf.set_font("Arial", size=12)
# pdf.cell(200, 10, txt=f"Data: {data_qr}", ln=True, align='C')

# 4. Simpan ke file PDF
nama_pdf = "Hasil_QRCode_NANOPA.pdf"
pdf.output(nama_pdf)

# Menghapus file gambar sementara agar rapi
if os.path.exists(nama_gambar):
    os.remove(nama_gambar)

print(f"\nBerhasil! QR Code Anda telah disimpan di dalam file: {nama_pdf}")