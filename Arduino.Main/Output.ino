// // arduino_20_motor_v4_non_blocking.ino (IRIS 2026 KRAI Standard)
// #include <Wire.h>

// int lajuawal = 0;

// // Pin M0-M5: 6 DC Motor Driver L298
// const int PIN_ENB[]   = {30, 26, 24, 28, 32, 34};
// const int PIN_PWM_R[] = {7,  11, 13,  9,  3,  5};
// const int PIN_PWM_L[] = {6,  10, 12,  8,  2,  4};

// // Pin Relay PW (diubah sementara ke 0)
// const int relayPin1 = 43; // kiri (Naik)
// const int relayPin2 = 47; // kiri (Turun)

// const int relayPin3 = 39; // kanan (Naik)
// const int relayPin4 = 37; // kanan (Turun)

// // Pin Relay Tambahan
// const int relayTambahan1 = 40; 
// const int relayTambahan2 = 42;

// // Pin Relay Tambahan
// const int relayCapit1 = 36; 
// const int relayCapit2 = 38;



// // Array Kecepatan (11 channels)
// const word total = 15;
// int16_t targetSpeeds[total] = {0}; 
// // Hanya 6 motor driver yang menggunakan ramping
// float currentSpeeds[6] = {0.0};
// const float RAMP_TIME_MS = 200.0; 
// const float MAX_SPEED_DELTA = 255.0; 
// const float ACCEL_RATE = MAX_SPEED_DELTA / RAMP_TIME_MS; 

// unsigned long lastRampTime = 0;
// unsigned long lastSerialTime = 0;
// unsigned long lastTelemetryTime = 0;

// const int limit1 = 46;
// const int limit2 = 45;

// // Buffer serial: 11 data * 2 byte = 22 byte data payload
// byte rxBuffer[50];
// int rxIndex = 0;
// enum SerialState { HEADER1, HEADER2, DATA, CHECKSUM, END1, END2 };
// SerialState rxState = HEADER1;

// // Variabel Limit State
// int arah_awal_0 = 0; // 1 (Kanan/Turun), -1 (Kiri/Naik), 0 (Berhenti)
// int arah_awal_1 = 0; 

// void setup() {
//   Serial.begin(115200);

//   // Setup all 6 DC driver channels (M0-M5)
//   for (int i = 0; i < 6; i++) {
//     pinMode(PIN_ENB[i], OUTPUT); 
//     digitalWrite(PIN_ENB[i], HIGH);
//     pinMode(PIN_PWM_R[i], OUTPUT); 
//     pinMode(PIN_PWM_L[i], OUTPUT);
//   }

//   // Setup Relay PW (hanya jika pin bukan 0)
//   if (relayPin1 != 0) { pinMode(relayPin1, OUTPUT); digitalWrite(relayPin1, HIGH); }
//   if (relayPin2 != 0) { pinMode(relayPin2, OUTPUT); digitalWrite(relayPin2, HIGH); }
//   if (relayPin3 != 0) { pinMode(relayPin3, OUTPUT); digitalWrite(relayPin3, HIGH); }
//   if (relayPin4 != 0) { pinMode(relayPin4, OUTPUT); digitalWrite(relayPin4, HIGH); }

//   // Setup Relay Tambahan
//   pinMode(relayTambahan1, OUTPUT); digitalWrite(relayTambahan1, HIGH);
//   pinMode(relayTambahan2, OUTPUT); digitalWrite(relayTambahan2, HIGH);
//   pinMode(relayCapit1, OUTPUT); digitalWrite(relayCapit1, HIGH);
//   pinMode(relayCapit2, OUTPUT); digitalWrite(relayCapit2, HIGH);
  
//   pinMode(limit1, INPUT_PULLUP);
//   pinMode(limit2, INPUT_PULLUP);

//   Wire.begin();
// }

// void loop() {
//   processSerial();

//   if (millis() - lastSerialTime > 300) {
//     for (int i = 0; i < total; i++) targetSpeeds[i] = 0;
//   }

//   applyRamping();
//   updateMotors();
  
//   if (millis() - lastTelemetryTime >= 100) {
//      sendTelemetry();
//      lastTelemetryTime = millis();
//   }
// }

// void processSerial() {
//   while (Serial.available()) {
//     byte b = Serial.read();
//     switch (rxState) {
//       case HEADER1: if (b == 0xAA) rxState = HEADER2; break;
//       case HEADER2: if (b == 0x55) rxState = DATA; rxIndex = 0; break;
      
//       // 11 data * 2 byte = 22 byte. Checksum ada di indeks ke-22
//       case DATA: rxBuffer[rxIndex++] = b; if (rxIndex >= (total*2)) rxState = CHECKSUM; break;
//       case CHECKSUM: rxBuffer[total*2] = b; rxState = END1; break;
      
//       case END1: if (b == 0x0D) rxState = END2; else rxState = HEADER1; break;
//       case END2:
//         if (b == 0x0A) {
//           byte calcXor = 0;
//           for (int i = 0; i < (total*2); i++) calcXor ^= rxBuffer[i];
          
//           if (calcXor == rxBuffer[total*2]) {
//              for(int i = 0; i < total; i++) targetSpeeds[i] = rxBuffer[i*2] | (rxBuffer[(i*2)+1] << 8);
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
//      // Ramping hanya untuk 6 motor driver pertama (indeks 0-5)
//      for(int i = 0; i < 6; i++) {
//          float diff = targetSpeeds[i] - currentSpeeds[i];
//          if (abs(diff) <= maxChange) currentSpeeds[i] = targetSpeeds[i]; 
//          else if (diff > 0) currentSpeeds[i] += maxChange; 
//          else currentSpeeds[i] -= maxChange; 
//      }
//      lastRampTime = now;
//   }
// }

// void updateMotors() {
//   // 6 Driver-controlled DC motors (menggunakan ramping)
//   for (int i = 0; i < 6; i++) {
//     setL298(i, constrain((int)currentSpeeds[i], -255, 255));
//   }

//   // 2 Relay-controlled PW motors (mDorong1 dan mDorong2 pada index 6 dan 7)
//   setRelayPW(targetSpeeds[6], targetSpeeds[7]);

//   // Control tambahan relay 1 (pin 40)
//   if (targetSpeeds[9] == 1) {
//     digitalWrite(relayTambahan1, LOW); // Active Low
//   } else {
//     digitalWrite(relayTambahan1, HIGH); // Inactive
//   }

//   // Control tambahan relay 2 (pin 42)
//   if (targetSpeeds[10] == 1) {
//     digitalWrite(relayTambahan2, LOW); // Active Low
//   } else {
//     digitalWrite(relayTambahan2, HIGH); // Inactive
//   }

//     // Control tambahan relay 1 (pin 40)
//   if (targetSpeeds[11] == 1) {
//     digitalWrite(relayCapit1, LOW); // Active Low
//   } else {
//     digitalWrite(relayCapit1, HIGH); // Inactive
//   }

//   // Control tambahan relay 2 (pin 42)
//   if (targetSpeeds[12] == 1) {
//     digitalWrite(relayCapit2, LOW); // Active Low
//   } else {
//     digitalWrite(relayCapit2, HIGH); // Inactive
//   }
// }

// void setL298(int index, int pwm) {
//   if (index >= 0 && index < 6) {
//     if (pwm > 0) { 
//       analogWrite(PIN_PWM_R[index], pwm); 
//       analogWrite(PIN_PWM_L[index], 0); 
//     }
//     else if (pwm < 0) { 
//       analogWrite(PIN_PWM_R[index], 0); 
//       analogWrite(PIN_PWM_L[index], -pwm); 
//     }
//     else { 
//       analogWrite(PIN_PWM_R[index], 0); 
//       analogWrite(PIN_PWM_L[index], 0); 
//     }
//   }
// }

// void setRelayPW(int speed1, int speed2) {
//   // speed1: mDorong1 (PW Kanan), speed2: mDorong2 (PW Kiri)
  
//   // PW Kanan (Relay 3 & 4)
//   int dir1 = 0; // 0: stop, -1: naik, 1: turun
//   if (speed1 < 0) dir1 = -1;
//   else if (speed1 > 0) dir1 = 1;

//   if (targetSpeeds[8] == 0) { // pwLogic is 0, check limit1
//     if (digitalRead(limit1) == 0) { // limit switch triggered (active low)
//       if ((dir1 < 0 && arah_awal_0 < 0) || (dir1 > 0 && arah_awal_0 > 0) || dir1 == 0) {
//         dir1 = 0;
//       }
//     } else {
//       arah_awal_0 = dir1;
//     }
//   }

//   if (relayPin3 != 0 && relayPin4 != 0) {
//     if (dir1 < 0) { // Naik
//       digitalWrite(relayPin4, HIGH);
//       digitalWrite(relayPin3, LOW);
//     } else if (dir1 > 0) { // Turun
//       digitalWrite(relayPin3, HIGH);
//       digitalWrite(relayPin4, LOW);
//     } else { // Stop
//       digitalWrite(relayPin3, HIGH);
//       digitalWrite(relayPin4, HIGH);
//     }
//   }

//   // PW Kiri (Relay 1 & 2)
//   int dir2 = 0;
//   if (speed2 < 0) dir2 = -1;
//   else if (speed2 > 0) dir2 = 1;

//   if (targetSpeeds[8] == 0) { // pwLogic is 0, check limit2
//     if (digitalRead(limit2) == 0) { // limit switch triggered (active low)
//       if ((dir2 < 0 && arah_awal_1 < 0) || (dir2 > 0 && arah_awal_1 > 0) || dir2 == 0) {
//         dir2 = 0;
//       }
//     } else {
//       arah_awal_1 = dir2;
//     }
//   }

//   if (relayPin1 != 0 && relayPin2 != 0) {
//     if (dir2 < 0) { // Naik
//       digitalWrite(relayPin2, HIGH);
//       digitalWrite(relayPin1, LOW);
//     } else if (dir2 > 0) { // Turun
//       digitalWrite(relayPin1, HIGH);
//       digitalWrite(relayPin2, LOW);
//     } else { // Stop
//       digitalWrite(relayPin1, HIGH);
//       digitalWrite(relayPin2, HIGH);
//     }
//   }
// }

// void sendTelemetry() {
//    byte pkt[7] = {0xBB, 0x66, 0x0D, 0x04, 0x00, 0x0D, 0x0A}; 
//    Serial.write(pkt, 7);
// }