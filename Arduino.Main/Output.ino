// // arduino_10_motor.ino (V3 - IRIS 2026 KRAI Standard)
// #include <Wire.h>
// #include <Adafruit_PWMServoDriver.h>

// Adafruit_PWMServoDriver pca = Adafruit_PWMServoDriver(0x40);

// // Pin M0-M5: 2 PW, 4 DC
// const int PIN_ENB[]   = {30, 26, 24, 28, 32, 34};
// const int PIN_PWM_R[] = {7,  11, 13,  9,  3,  5};
// const int PIN_PWM_L[] = {6,  10, 12,  8,  2,  4};

// // Pin M8-M9: Stepper
// const int STP1_ENA  = 37;
// const int STP1_DIR  = 39;
// const int STP1_PULL = 41; 

// const int STP2_ENA  = 43;
// const int STP2_DIR  = 47;
// const int STP2_PULL = 49;
// const int delayWaktu = 400; // Kecepatan (semakin kecil, semakin cepat)

// // --- STATE TRACKER PCA ---
// int lastPcaVal[5] = {0, 0, 0, 0, 0};

// // Pin M6-M10: PCA 
// int pcaEnPins[5] = {22, 23, 27, 25, 31};
// int pcaChRight[5] = {6, 12, 11, 14, 2};
// int pcaChLeft[5]  = {7, 13, 10, 15, 3};

// // --- DATA STRUCTURES (RAMPING) ---
// int16_t targetSpeeds[13] = {0}; 
// float currentSpeeds[13] = {0.0};  // Variabel asimtotik yang mendekati target

// // --- RAMPING CONFIG ---
// // Waktu ramping akselerasi dari 0 ke Maks(255) diset pada 200 milidetik (Halus tapi Responsif)
// const float RAMP_TIME_MS = 200.0; 
// const float MAX_SPEED_DELTA = 255.0; 
// const float ACCEL_RATE = MAX_SPEED_DELTA / RAMP_TIME_MS; // dV/dt (Satuan kecepatan per 1 ms)

// unsigned long lastRampTime = 0;
// unsigned long lastSerialTime = 0;
// unsigned long lastTelemetryTime = 0; // Timer kirim balik ke gui

// // Buffer Serial Parsing State Machine
// byte rxBuffer[30];
// int rxIndex = 0;
// enum SerialState { HEADER1, HEADER2, DATA, CHECKSUM, END1, END2 };
// SerialState rxState = HEADER1;

// // Stepper state
// unsigned long lastStepTime1 = 0;
// unsigned long lastStepTime2 = 0;
// bool stp1State = false;
// bool stp2State = false;

// void setup() {
//   Serial.begin(115200);

//   while (!Serial) {
//     ; // Tunggu sampai port serial terhubung ke PC
//   }

//   for (int i = 0; i < 6; i++) {
//     pinMode(PIN_ENB[i], OUTPUT); digitalWrite(PIN_ENB[i], HIGH);
//     pinMode(PIN_PWM_R[i], OUTPUT); pinMode(PIN_PWM_L[i], OUTPUT);
//     analogWrite(PIN_PWM_R[i], 0); analogWrite(PIN_PWM_L[i], 0);
//   }

//   pinMode(STP1_ENA, OUTPUT);  digitalWrite(STP1_ENA, LOW); 
//   pinMode(STP1_DIR, OUTPUT);  digitalWrite(STP1_DIR, LOW);
//   pinMode(STP1_PULL, OUTPUT); digitalWrite(STP1_PULL, LOW);
//   pinMode(STP2_ENA, OUTPUT);  digitalWrite(STP2_ENA, LOW);
//   pinMode(STP2_DIR, OUTPUT);  digitalWrite(STP2_DIR, LOW);
//   pinMode(STP2_PULL, OUTPUT); digitalWrite(STP2_PULL, LOW);

//   Wire.begin();
//   pca.begin();
//   pca.setPWMFreq(2000);
//   for(int i = 0; i < 5; i++){
//     pinMode(pcaEnPins[i], OUTPUT); digitalWrite(pcaEnPins[i], HIGH);
//     pca.setPWM(pcaChRight[i], 0, 0); pca.setPWM(pcaChLeft[i], 0, 0);
//   }
// }

// void loop() {
//   processSerial();

//   // Failsafe: Jika koneksi PC hilang > 1 detik, mematikan target rotasinya
//   if (millis() - lastSerialTime > 1000) {
//     for (int i = 0; i < 13; i++) targetSpeeds[i] = 0;
//   }

//   // Terapkan Rumus Halus, Lalu Perbarui Pin
//   applyRamping();
//   updateMotors();
//   updateSteppers2();
  
//   // Kirim Telemetry tiap 100ms
//   if (millis() - lastTelemetryTime >= 100) {
//      sendTelemetry();
//      lastTelemetryTime = millis();
//   }
// }

// void processSerial() {
//   while (Serial.available()) {
//     byte b = Serial.read();
    
//     switch (rxState) {
//       case HEADER1:
//         if (b == 0xAA) { rxState = HEADER2; rxIndex = 0; }
//         break;
//       case HEADER2:
//         if (b == 0x55) { rxState = DATA; }
//         else if (b == 0xAA) { rxState = HEADER2; } // Proteksi tambahan agar tidak mis-header
//         else { rxState = HEADER1; }
//         break;
//       case DATA:
//         rxBuffer[rxIndex++] = b;
//         if (rxIndex >= 26) { rxState = CHECKSUM; }
//         break;
//       case CHECKSUM:
//         rxBuffer[26] = b; 
//         rxState = END1;
//         break;
//       case END1:
//         if (b == 0x0D) { rxState = END2; }
//         else { rxState = HEADER1; }
//         break;
//       case END2:
//         if (b == 0x0A) { 
//           // Verifikasi Integritas Data Paket (XOR 8-bit checksum)
//           byte calcXor = 0;
//           for (int i = 0; i < 26; i++) calcXor ^= rxBuffer[i];
          
//           if (calcXor == rxBuffer[26]) {
//              for(int i = 0; i < 13; i++) {
//                 targetSpeeds[i] = rxBuffer[i*2] | (rxBuffer[(i*2)+1] << 8);
//              }
//              lastSerialTime = millis(); 
//           }
//         }
//         rxState = HEADER1; 
//         break;
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
//          if (abs(diff) <= maxChange) {
//              currentSpeeds[i] = targetSpeeds[i]; 
//          } else if (diff > 0) {
//              currentSpeeds[i] += maxChange; 
//          } else {
//              currentSpeeds[i] -= maxChange; 
//          }
//      }
//      lastRampTime = now;
//   }
// }

// void updateMotors() {
//   // M0 - M1: Power Window (Max Limit 100)
//   for (int i = 0; i < 2; i++) {
//     int val = constrain((int)currentSpeeds[i], -255, 255);
//     setL298(i, val);
//   }
//   // M2 - M5: DC Motor (Max Limit 255)
//   for (int i = 2; i < 6; i++) {
//     int val = constrain((int)currentSpeeds[i], -255, 255);
//     setL298(i, val);
//   }
  
//   // M6 - M7: PCA Motor
//   for (int i = 0; i < 5; i++) {
//     // 1. Ambil nilai dan tambahkan Deadband kecil agar 0 benar-benar 0
//     int rawSpeed = (int)currentSpeeds[i+6];
//     if (abs(rawSpeed) < 3) rawSpeed = 0; 

//     int val = constrain(rawSpeed, -255, 255);
//     val = map(val, -255, 255, -4095, 4095);

//     // 2. ANTI-SPAM: Hanya kirim data via I2C JIKA nilai berubah!
//     if (val != lastPcaVal[i]) {
      
//       if (val > 0) {
//         // MATIKAN pin berlawanan TERLEBIH DAHULU (Anti-Tabrakan)
//         pca.setPWM(pcaChLeft[i], 0, 0);
//         pca.setPWM(pcaChRight[i], 0, val);
        
//       } else if (val < 0) {
//         // MATIKAN pin berlawanan TERLEBIH DAHULU
//         pca.setPWM(pcaChRight[i], 0, 0);
//         pca.setPWM(pcaChLeft[i], 0, -val);
        
//       } else {
//         // Stop total
//         pca.setPWM(pcaChRight[i], 0, 0); 
//         pca.setPWM(pcaChLeft[i], 0, 0);
//       }
      
//       // Simpan nilai saat ini agar tidak dikirim ulang di loop berikutnya
//       lastPcaVal[i] = val; 
//     }
//   }
// }

// void setL298(int index, int pwm) {
//   if (pwm > 0) {
//     analogWrite(PIN_PWM_R[index], pwm); analogWrite(PIN_PWM_L[index], 0);
//   } else if (pwm < 0) {
//     analogWrite(PIN_PWM_R[index], 0); analogWrite(PIN_PWM_L[index], -pwm);
//   } else {
//     analogWrite(PIN_PWM_R[index], 0); analogWrite(PIN_PWM_L[index], 0);
//   }
// }

// // Stepper berdasar waktu (interval micros)
// void updateSteppers() {
//   // Gunakan targetSpeeds alih-alih currentSpeeds agar tidak terkena efek ramping (overshoot)
//   int s1 = targetSpeeds[11];
//   int s2 = targetSpeeds[12];

//   bool step1 = (s1 != 0);
//   bool step2 = (s2 != 0);

//   if (!step1 && !step2) return;

//   if (step1) {
//     digitalWrite(STP1_DIR, s1 > 0 ? HIGH : LOW);
//     digitalWrite(STP1_PULL, HIGH);
//   }
//   if (step2) {
//     digitalWrite(STP2_DIR, s2 > 0 ? LOW : HIGH);
//     digitalWrite(STP2_PULL, HIGH);
//   }

//   delayMicroseconds(delayWaktu);

//   if (step1) digitalWrite(STP1_PULL, LOW);
//   if (step2) digitalWrite(STP2_PULL, LOW);

//   delayMicroseconds(delayWaktu);
// }

// int tempStep = 0;
// int stt = 0;
// void updateSteppers2() {
//   // Gunakan targetSpeeds alih-alih currentSpeeds agar tidak terkena efek ramping (overshoot)
//   int s1 = targetSpeeds[11];
//   int s2 = targetSpeeds[12];

//   if (tempStep != s1){
//     tempStep = s1;
//     stt = tempStep;
//   }
//   if (stt != 0){
//     if (stt > 0){
//       digitalWrite(STP1_DIR, HIGH);
//       digitalWrite(STP2_DIR, LOW);
//       stt -= 1;
//     }
//      if (stt < 0){
//       digitalWrite(STP1_DIR, LOW);
//       digitalWrite(STP2_DIR, HIGH);
//       stt += 1;
//     }
//     digitalWrite(STP1_PULL, HIGH);
//     digitalWrite(STP2_PULL, HIGH);
//     delayMicroseconds(delayWaktu);
//     digitalWrite(STP1_PULL, LOW);
//     digitalWrite(STP2_PULL, LOW);
//     delayMicroseconds(delayWaktu);
//   }


// }

// void sendTelemetry() {
//    int battVal = 1245;
//    byte pkt[7];
//    pkt[0] = 0xBB;
//    pkt[1] = 0x66;
//    pkt[2] = battVal & 0xFF;         // Low byte
//    pkt[3] = (battVal >> 8) & 0xFF;  // High byte
//    pkt[4] = pkt[2] ^ pkt[3];        // XOR Checksum 
//    pkt[5] = 0x0D; // \r
//    pkt[6] = 0x0A; // \n
//    Serial.write(pkt, 7);
// }
