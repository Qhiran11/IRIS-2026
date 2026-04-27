// // Mendefinisikan daftar pin yang akan dibaca
// // Pin 28-46 (total 19 pin) + A0, A1 (2 pin) = 21 pin
// // Catatan: Jika ingin tepat 20, silakan sesuaikan isi array di bawah
// const int pinList[] = {
//   28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, A0, A1
// };

// // Menghitung jumlah pin secara otomatis
// const int numPins = sizeof(pinList) / sizeof(pinList[0]);

// void setup() {
//   Serial.begin(9600);
  
//   // Mengatur semua pin sebagai input
//   for (int i = 0; i < numPins; i++) {
//     pinMode(pinList[i], INPUT_PULLUP); 
//     // Gunakan INPUT_PULLUP jika pin tidak terhubung ke resistor eksternal
//     // pinMode(pinList[i], INPUT_PULLUP); 
//   }
// }

// void loop() {
//   Serial.println("--- Membaca Status Pin ---");
  
//   for (int i = 0; i < numPins; i++) {
//     int status = digitalRead(pinList[i]);
    
//     Serial.print("Pin ");
//     Serial.print(pinList[i]);
//     Serial.print(": ");
//     Serial.println(status == HIGH ? "HIGH (1)" : "LOW (0)");
//   }
  
//   delay(1000); // Tunggu 1 detik sebelum membaca ulang
// }