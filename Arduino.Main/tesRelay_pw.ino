// // // Mendefinisikan pin relay sesuai dengan pin yang Anda berikan
// const int relayCapit2 = 43; // kiri (Naik)
// // const int relayCapit2 = 47; // kiri (Turun)

// // const int relayCapit2 = 39; // kanan (Naik)
// // const int relayCapit2 = 37; // kanan (Turun)
// // const int relayCapit2 = 38;

// void setup() {
//   // Memulai komunikasi serial (opsional, untuk debugging di Serial Monitor)
//   Serial.begin(9600);
  
//   // Mengatur pin relay sebagai OUTPUT agar dapat mengirim sinyal
//   pinMode(relayCapit2, OUTPUT);

//   // Mengatur status awal relay saat perangkat pertama kali dinyalakan.
//   // Catatan: Sebagian besar modul relay Arduino bersifat "Active LOW"
//   // yang berarti HIGH = Mati, dan LOW = Menyala.
//   digitalWrite(relayCapit2, HIGH); 
//   Serial.println("Sistem Siap. Relay dalam keadaan MATI.");
// }

// void loop() {
//   // Menyalakan relay (mengirim sinyal LOW untuk relay Active LOW)
//   digitalWrite(relayCapit2, LOW);
//   Serial.println("Relay MENYALA");
//   delay(2000); // Menunggu selama 2000 milidetik (2 detik)

//   // Mematikan relay (mengirim sinyal HIGH untuk relay Active LOW)
//   digitalWrite(relayCapit2, HIGH);
//   Serial.println("Relay MATI");
//   delay(2000); // Menunggu selama 2 detik sebelum mengulang
// }