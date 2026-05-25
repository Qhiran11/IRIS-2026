# File: MonitorDasbor.py (Dijalankan di Laptop Monitor)
import socket
import json
import time
import threading
from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from rich.console import Console

console = Console()
data_robot_terkini = {}

def cari_jetson(token_target):
    with console.status(f"[yellow]Mencari Sinyal Jetson Nano dengan Token [bold red]{token_target}[/bold red] di jaringan...[/yellow]", spinner="aesthetic"):
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.bind(('0.0.0.0', 5006))
        udp_sock.settimeout(10.0) # Waktu tunggu 10 detik

        try:
            while True:
                data, addr = udp_sock.recvfrom(1024)
                pesan = data.decode('utf-8')
                
                # Jika mendengar teriakan dari Jetson
                if pesan.startswith("NANOPA"):
                    _, token, port = pesan.split(":")
                    if token == token_target:
                        console.print(f"[bold green]✔ Jetson Ditemukan! Menghubungkan ke IP: {addr[0]}[/bold green]")
                        udp_sock.close()
                        return addr[0], int(port)
        except socket.timeout:
            console.print("[bold red]✖ Timeout! Jetson Nano tidak ditemukan. Pastikan Token benar dan jaringan sama.[/bold red]")
            udp_sock.close()
            return None, None
def buat_tabel(judul, dictionary_data):
    """Fungsi ajaib untuk membuat tabel dari data JSON apa pun secara dinamis"""
    
    # Tambahkan parameter row_styles di sini
    # Gunakan "grey50" (abu-abu) dan "blue" (biru)
    table = Table(
        title=judul, 
        style="cyan", 
        title_style="bold magenta", 
        expand=True,
        row_styles=["grey50", "blue"] 
    )
    
    # Karena row_styles mengatur warna baris, kita bisa menghapus style statis pada kolom 
    # agar warna selang-selingnya tidak tertimpa, atau biarkan jika ingin kolom tertentu tetap warnanya.
    table.add_column("Parameter", no_wrap=True)
    table.add_column("Nilai / Value", style="bold")
    
    for key, value in dictionary_data.items():
        # Beri warna hijau jika True, merah jika False
        str_val = str(value)
        if isinstance(value, bool):
            # Markup warna ini akan menimpa/override warna abu/biru bawaan row_styles (khusus untuk teks boolean ini)
            str_val = f"[green]{value}[/green]" if value else f"[red]{value}[/red]"
            
        table.add_row(str(key), str_val)
        
    return table
def generate_dashboard():
    """Fungsi untuk merender struktur UI Dasbor"""
    if not data_robot_terkini:
        return Panel("[cyan]Menunggu aliran data dari Robot KRAI...[/cyan]", title="Menghubungkan...")

    # Membagi layar menjadi 2 kolom (Kiri dan Kanan)
    layout = Layout()
    layout.split_row(
        Layout(name="kiri"),
        Layout(name="kanan")
    )

    # Dinamis membuat tabel berdasarkan data JSON yang datang
    tabel_sensor = buat_tabel("📡 Data Memori Sensor", data_robot_terkini.get("Sensor", {}))
    tabel_motor = buat_tabel("⚙️ Perintah Motor & Relay", data_robot_terkini.get("Motor", {}))
    tabel_status = buat_tabel("🤖 Status Utama Robot", data_robot_terkini.get("Status Robot", {}))

    layout["kiri"].update(Panel(tabel_sensor, border_style="blue"))
    
    # Membagi layar kanan atas dan bawah
    layout_kanan = Layout()
    layout_kanan.split_column(
        Layout(Panel(tabel_status, border_style="yellow"), size=10),
        Layout(Panel(tabel_motor, border_style="red"))
    )
    
    layout["kanan"].update(layout_kanan)
    return layout

def main():
    console.print("\n[bold cyan]=== MONITOR TELEMETRI NANOPA 2026 ===[/bold cyan]\n")
    token = console.input("[bold white]Masukkan 4 Karakter Token dari Jetson : [/bold white]").upper()
    
    # 1. Fase Pencarian IP otomatis
    ip, port = cari_jetson(token)
    if not ip: return

    # 2. Fase Koneksi Data
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        tcp_sock.connect((ip, port))
        time.sleep(1)
    except Exception as e:
        console.print(f"[red]Gagal menyambung ke data stream: {e}[/red]")
        return

    # 3. Thread Penerima Data di Background
    def terima_data():
        global data_robot_terkini
        buffer = ""
        while True:
            try:
                chunk = tcp_sock.recv(4096).decode('utf-8')
                if not chunk: break
                buffer += chunk
                # Pisahkan JSON berdasarkan baris baru (\n)
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    data_robot_terkini = json.loads(line)
            except Exception:
                break

    threading.Thread(target=terima_data, daemon=True).start()

    # 4. Render Layar Dinamis (60 FPS)
    try:
        with Live(generate_dashboard(), refresh_per_second=30, screen=True) as live:
            while True:
                time.sleep(0.05)
                live.update(generate_dashboard())
    except KeyboardInterrupt:
        console.print("\n[bold red]Menutup Dasbor Telemetri...[/bold red]")
        tcp_sock.close()

if __name__ == "__main__":
    main()