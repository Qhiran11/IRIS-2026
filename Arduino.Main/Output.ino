// // arduino_10_motor_v4_non_blocking.ino (IRIS 2026 KRAI Standard)
// #include <Wire.h>
// #include <Adafruit_PWMServoDriver.h>

// int lajuawal = 0;

// Adafruit_PWMServoDriver pca = Adafruit_PWMServoDriver(0x40);

// // Pin M0-M5: 2 PW, 4 DC
// const int PIN_ENB[]   = {30, 26, 24, 28, 32, 34};
// const int PIN_PWM_R[] = {7,  11, 13,  9,  3,  5};
// const int PIN_PWM_L[] = {6,  10, 12,  8,  2,  4};

// // Pin Stepper
// const int STP1_ENA = 37; const int STP1_DIR = 39; const int STP1_PULL = 41;
// const int STP2_ENA = 43; const int STP2_DIR = 47; const int STP2_PULL = 49;

// // --- STEPPER TIMING ---
// unsigned long lastStepMicros1 = 0;
// unsigned long lastStepMicros2 = 0;
// const unsigned long stepInterval = 400; // Microseconds
// bool pullState1 = false;
// bool pullState2 = false;

// // --- STATE TRACKER PCA & RAMPING ---
// int lastPcaVal[5] = {0, 0, 0, 0, 0};
// int pcaEnPins[5] = {22, 23, 27, 25, 31};
// int pcaChRight[5] = {6, 12, 11, 14, 2};
// int pcaChLeft[5]  = {7, 13, 10, 15, 3};

// int16_t targetSpeeds[13] = {0}; 
// float currentSpeeds[13] = {0.0};
// const float RAMP_TIME_MS = 200.0; 
// const float MAX_SPEED_DELTA = 255.0; 
// const float ACCEL_RATE = MAX_SPEED_DELTA / RAMP_TIME_MS; 

// unsigned long lastRampTime = 0;
// unsigned long lastSerialTime = 0;
// unsigned long lastTelemetryTime = 0;

// int limit1 = 46;
// int limit2 = 45;

// byte rxBuffer[30];
// int rxIndex = 0;
// enum SerialState { HEADER1, HEADER2, DATA, CHECKSUM, END1, END2 };
// SerialState rxState = HEADER1;

// void setup() {
//   Serial.begin(115200);

//   for (int i = 0; i < 6; i++) {
//     pinMode(PIN_ENB[i], OUTPUT); digitalWrite(PIN_ENB[i], HIGH);
//     pinMode(PIN_PWM_R[i], OUTPUT); pinMode(PIN_PWM_L[i], OUTPUT);
//   }

//   pinMode(STP1_ENA, OUTPUT); digitalWrite(STP1_ENA, LOW); 
//   pinMode(STP1_DIR, OUTPUT); pinMode(STP1_PULL, OUTPUT);
//   pinMode(STP2_ENA, OUTPUT); digitalWrite(STP2_ENA, LOW); 
//   pinMode(STP2_DIR, OUTPUT); pinMode(STP2_PULL, OUTPUT);

//   pinMode(limit1, INPUT_PULLUP);
//   pinMode(limit2, INPUT_PULLUP);

//   Wire.begin();
//   pca.begin();
//   pca.setPWMFreq(2000);
//   for(int i = 0; i < 5; i++){
//     pinMode(pcaEnPins[i], OUTPUT); digitalWrite(pcaEnPins[i], HIGH);
//   }
// }

// void loop() {
//   processSerial();

//   if (millis() - lastSerialTime > 300) {
//     // lajuawal = 0;
//     for (int i = 0; i < 13; i++) targetSpeeds[i] = 0;
//   }

//   applyRamping();
//   updateMotors();
//   updateSteppersNonBlocking();
  
//   if (millis() - lastTelemetryTime >= 100) {
//      sendTelemetry();
//      lastTelemetryTime = millis();
//   }
// }
//   // --- Tambahkan/Ubah di bagian variabel global ---
// // --- Tambahkan variabel global baru ---
// long remainingSteps = 0;
// bool readyToAccept = true; // Flag untuk mengunci spam data yang sama

// void updateSteppersNonBlocking() {
//   unsigned long currentMicros = micros();
//   int incomingData = targetSpeeds[11]; // Data dari Python (misal 800)

//   // --- LOGIKA FILTER SPAM ---
//   if (incomingData != 0 && readyToAccept) {
//     // 1. Terima data hanya saat flag ready (pertama kali data muncul)
//     remainingSteps = incomingData; 
//     readyToAccept = false; // KUNCI! Jangan terima data lagi sampai dikirim angka 0
//   } 
//   else if (incomingData == 0) {
//     // 2. Jika Python kirim 0, buka kembali kuncinya
//     readyToAccept = true;
//   }

//   // --- LOGIKA GERAK STEPPER ---
//   if (remainingSteps != 0) {
//     // Tentukan Arah
//     if (remainingSteps > 0) {
//       digitalWrite(STP1_DIR, LOW);
//       digitalWrite(STP2_DIR, HIGH);
//     } else {
//       digitalWrite(STP1_DIR, HIGH);
//       digitalWrite(STP2_DIR, LOW);
//     }

//     // Interval Pulse
//     if (currentMicros - lastStepMicros1 >= stepInterval) {
//       lastStepMicros1 = currentMicros;
//       pullState1 = !pullState1;
      
//       digitalWrite(STP1_PULL, pullState1);
//       digitalWrite(STP2_PULL, pullState1); // STP2 mengikuti STP1 agar sinkron

//       // Kurangi sisa step setiap satu siklus HIGH-LOW selesai
//       if (pullState1 == LOW) {
//         if (remainingSteps > 0) remainingSteps--;
//         else remainingSteps++;
//       }
//     }
//   }
// }

// void processSerial() {
//   while (Serial.available()) {
//     byte b = Serial.read();
//     switch (rxState) {
//       case HEADER1: if (b == 0xAA) rxState = HEADER2; break;
//       case HEADER2: if (b == 0x55) rxState = DATA; rxIndex = 0; break;
//       case DATA: rxBuffer[rxIndex++] = b; if (rxIndex >= 26) rxState = CHECKSUM; break;
//       case CHECKSUM: rxBuffer[26] = b; rxState = END1; break;
//       case END1: if (b == 0x0D) rxState = END2; else rxState = HEADER1; break;
//       case END2:
//         if (b == 0x0A) {
//           byte calcXor = 0;
//           for (int i = 0; i < 26; i++) calcXor ^= rxBuffer[i];
//           if (calcXor == rxBuffer[26]) {
//              for(int i = 0; i < 13; i++) targetSpeeds[i] = rxBuffer[i*2] | (rxBuffer[(i*2)+1] << 8);
//              lastSerialTime = millis();
//           }
//         }
//         rxState = HEADER1; break;
//     }
//   }
// }

// void applyRamping() {
//   unsigned long now = millis();
//   unsigned long dt = now - lastRampTime;
//   if (dt > 0) {
//      float maxChange = ACCEL_RATE * dt; 
//      for(int i = 0; i < 13; i++) {
//          float diff = targetSpeeds[i] - currentSpeeds[i];
//          if (abs(diff) <= maxChange) currentSpeeds[i] = targetSpeeds[i]; 
//          else if (diff > 0) currentSpeeds[i] += maxChange; 
//          else currentSpeeds[i] -= maxChange; 
//      }
//      lastRampTime = now;
//   }
// }

// void updateMotors() {
//   for (int i = 0; i < 6; i++) setL298(i, constrain((int)currentSpeeds[i], -255, 255));
  
//   for (int i = 0; i < 5; i++) {
//     int rawSpeed = (int)currentSpeeds[i+6];
//     int val = constrain((abs(rawSpeed) < 3 ? 0 : rawSpeed), -255, 255);
//     int mappedVal = map(val, -255, 255, -4095, 4095);

//     if (mappedVal != lastPcaVal[i]) {
//       if (mappedVal > 0) { pca.setPWM(pcaChLeft[i], 0, 0); pca.setPWM(pcaChRight[i], 0, mappedVal); }
//       else if (mappedVal < 0) { pca.setPWM(pcaChRight[i], 0, 0); pca.setPWM(pcaChLeft[i], 0, -mappedVal); }
//       else { pca.setPWM(pcaChRight[i], 0, 0); pca.setPWM(pcaChLeft[i], 0, 0); }
//       lastPcaVal[i] = mappedVal;
//     }
//   }
// }

// // Tambahkan 2 variabel global ini di bagian atas (luar fungsi) untuk menyimpan arah yang dikunci


// // Tambahkan 2 variabel global ini di bagian atas
// int arah_awal_0 = 0; // 1 (Kanan), -1 (Kiri), 0 (Berhenti)
// int arah_awal_1 = 0; 

// void setL298(int index, int pwm) {
//   // === KHUSUS MOTOR 0 ===
//   if (index == 0) {
//     if (digitalRead(limit1) == 0) { // JIKA MENTOK
//       // Berhenti jika arah perintah SAMA dengan arah mentok, atau jika disuruh stop
//       if ((pwm > 0 && arah_awal_0 > 0) || (pwm < 0 && arah_awal_0 < 0) || pwm == 0) {
//         analogWrite(PIN_PWM_R[index], 0); analogWrite(PIN_PWM_L[index], 0); 
//       } 
//       else { // Beda arah, izinkan lolos
//         if (pwm > 0) { analogWrite(PIN_PWM_R[index], pwm); analogWrite(PIN_PWM_L[index], 0); }
//         else if (pwm < 0) { analogWrite(PIN_PWM_R[index], 0); analogWrite(PIN_PWM_L[index], -pwm); }
//       }
//     }
//     else { // JIKA TIDAK MENTOK (Simpan Arah Terakhir)
//       if (pwm > 0) { analogWrite(PIN_PWM_R[index], pwm); analogWrite(PIN_PWM_L[index], 0); arah_awal_0 = 1; }
//       else if (pwm < 0) { analogWrite(PIN_PWM_R[index], 0); analogWrite(PIN_PWM_L[index], -pwm); arah_awal_0 = -1; }
//       else { analogWrite(PIN_PWM_R[index], 0); analogWrite(PIN_PWM_L[index], 0); arah_awal_0 = 0; }
//     }
//   }

//   // === KHUSUS MOTOR 1 ===
//   else if (index == 1) { // <-- HARUS ELSE IF
//     if (digitalRead(limit2) == 0) {
//       if ((pwm > 0 && arah_awal_1 > 0) || (pwm < 0 && arah_awal_1 < 0) || pwm == 0) {
//         analogWrite(PIN_PWM_R[index], 0); analogWrite(PIN_PWM_L[index], 0); 
//       } 
//       else {
//         if (pwm > 0) { analogWrite(PIN_PWM_R[index], pwm); analogWrite(PIN_PWM_L[index], 0); }
//         else if (pwm < 0) { analogWrite(PIN_PWM_R[index], 0); analogWrite(PIN_PWM_L[index], -pwm); }
//       }
//     }
//     else {
//       if (pwm > 0) { analogWrite(PIN_PWM_R[index], pwm); analogWrite(PIN_PWM_L[index], 0); arah_awal_1 = 1; }
//       else if (pwm < 0) { analogWrite(PIN_PWM_R[index], 0); analogWrite(PIN_PWM_L[index], -pwm); arah_awal_1 = -1; }
//       else { analogWrite(PIN_PWM_R[index], 0); analogWrite(PIN_PWM_L[index], 0); arah_awal_1 = 0; }
//     }
//   }
    
//   // === UNTUK MOTOR LAINNYA (Index 2-5) BEBAS ===
//   else {
//     if (pwm > 0) { analogWrite(PIN_PWM_R[index], pwm); analogWrite(PIN_PWM_L[index], 0); }
//     else if (pwm < 0) { analogWrite(PIN_PWM_R[index], 0); analogWrite(PIN_PWM_L[index], -pwm); }
//     else { analogWrite(PIN_PWM_R[index], 0); analogWrite(PIN_PWM_L[index], 0); }
//   }
// }

// void sendTelemetry() {
//    byte pkt[7] = {0xBB, 0x66, 0x0D, 0x04, 0x00, 0x0D, 0x0A}; // Dummy 1245
//    Serial.write(pkt, 7);
// }