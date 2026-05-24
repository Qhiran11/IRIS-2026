// // const int relayPin1 = 40; // kiri
// // const int relayPin2 = 42; // kiri

// const int relayPin1 = 10; // kiri
// const int relayPin2 = 11; // kiri
// const int relayPin3 = 6;  // kanan
// const int relayPin4 = 7;  // kanan

// bool kondisiNaik = true; // penanda mode awal

// // ======================================================
// // SETUP
// // ======================================================

// void setup() {

//   SerialUSB.begin(115200);

//   pinMode(relayPin1, OUTPUT);
//   pinMode(relayPin2, OUTPUT);
//   pinMode(relayPin3, OUTPUT);
//   pinMode(relayPin4, OUTPUT);

//   matikanSemuaRelay();

//   SerialUSB.println("Sistem siap");
//   SerialUSB.println("Input '1' untuk toggle naik/turun");
// }

// // ======================================================
// // LOOP
// // ======================================================

// void loop() {

//   if (SerialUSB.available()) {

//     char input = SerialUSB.read();

//     // abaikan enter
//     if (input == '\n' || input == '\r') {
//       return;
//     }

//     // ==========================================
//     // INPUT 1 -> TOGGLE
//     // ==========================================

//     if (input == '1') {

//       if (kondisiNaik) {
//         modeNaik();
//       } else {
//         modeTurun();
//       }

//       // toggle kondisi
//       kondisiNaik = !kondisiNaik;
//     }

//     // ==========================================
//     // INPUT LAIN -> MATI
//     // ==========================================

//     else {

//       matikanSemuaRelay();

//       SerialUSB.print("Semua relay mati. Input diterima: ");
//       SerialUSB.println(input);
//     }
//   }
// }

// // ======================================================
// // MODE NAIK
// // ======================================================

// void modeNaik() {

//   SerialUSB.println("MODE NAIK");

//   // relay aktif LOW

  
//   digitalWrite(relayPin4, HIGH);
//   digitalWrite(relayPin2, HIGH);
//   delay(1000);
//   digitalWrite(relayPin3, LOW);
//   digitalWrite(relayPin1, LOW);
  
// }

// // ======================================================
// // MODE TURUN
// // ======================================================

// void modeTurun() {

//   SerialUSB.println("MODE TURUN");

//   // relay aktif LOW

//   digitalWrite(relayPin1, HIGH);
//   digitalWrite(relayPin3, HIGH);
  
//   delay(1000);
//   digitalWrite(relayPin2, LOW);
//   digitalWrite(relayPin4, LOW);
// }

// // ======================================================
// // MATIKAN SEMUA
// // ======================================================

// void matikanSemuaRelay() {

//   digitalWrite(relayPin1, HIGH);
//   digitalWrite(relayPin2, HIGH);
//   digitalWrite(relayPin3, HIGH);
//   digitalWrite(relayPin4, HIGH);
// }