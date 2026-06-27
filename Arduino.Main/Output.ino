// // arduino_20_motor_v5_krai.ino (IRIS 2026 KRAI Standard)
// #include <Wire.h>
// #include <Adafruit_PWMServoDriver.h>

// // Inisialisasi PCA9685 (Alamat default 0x40)
// Adafruit_PWMServoDriver pca = Adafruit_PWMServoDriver(0x40);

// // Pin M0-M5: 6 DC Motor Driver L298 (4 Utama + 2 Power Window)
// const int PIN_ENB[]   = {30, 26, 24, 28, 32, 34};
// const int PIN_PWM_R[] = {7,  11, 13,  9,  3,  5};
// const int PIN_PWM_L[] = {6,  10, 12,  8,  2,  4};

// // Pin 3 Buah Relay (Active LOW)
// const int relay1 = 40; 
// const int relay2 = 42;
// const int relay3 = 36; 

// // Pin Limit Switch (Mungkin untuk keamanan Power Window)
// const int limit1 = 46;
// const int limit2 = 45;

// // Array Kecepatan (Kita pertahankan total = 15 agar Python tidak error)
// const word total = 15;
// int16_t targetSpeeds[total] = {0}; 

// // Ramping untuk 6 motor driver (Utama + PW)
// float currentSpeeds[6] = {0.0};
// const float RAMP_TIME_MS = 200.0; 
// const float MAX_SPEED_DELTA = 255.0; 
// const float ACCEL_RATE = MAX_SPEED_DELTA / RAMP_TIME_MS; 

// unsigned long lastRampTime = 0;
// unsigned long lastSerialTime = 0;
// unsigned long lastTelemetryTime = 0;

// // Buffer serial
// byte rxBuffer[50];
// int rxIndex = 0;
// enum SerialState { HEADER1, HEADER2, DATA, CHECKSUM, END1, END2 };
// SerialState rxState = HEADER1;

// void setup() {
//   Serial.begin(115200);

//   // Setup 6 DC driver channels (M0-M5)
//   for (int i = 0; i < 6; i++) {
//     pinMode(PIN_ENB[i], OUTPUT); 
//     digitalWrite(PIN_ENB[i], HIGH);
//     pinMode(PIN_PWM_R[i], OUTPUT); 
//     pinMode(PIN_PWM_L[i], OUTPUT);
//   }

//   // Setup 3 Relay
//   pinMode(relay1, OUTPUT); digitalWrite(relay1, HIGH);
//   pinMode(relay2, OUTPUT); digitalWrite(relay2, HIGH);
//   pinMode(relay3, OUTPUT); digitalWrite(relay3, HIGH);
  
//   pinMode(limit1, INPUT_PULLUP);
//   pinMode(limit2, INPUT_PULLUP);

//   Wire.begin();
  
//   // Setup PCA9685
//   pca.begin();
//   pca.setOscillatorFrequency(27000000);
//   pca.setPWMFreq(1600);  // Frekuensi PWM maksimal untuk motor DC (1.6 kHz)
// }

// void loop() {
//   processSerial();

//   // Failsafe: Jika tidak ada data serial masuk selama 300ms, matikan semua motor
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
      
//       // Data payload (total * 2 byte)
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
//      // Ramping untuk 4 Motor Utama + 2 Power Window (indeks 0-5)
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
//   // 1. Update 4 Motor Utama & 2 Power Window via L298 (Dengan Ramping)
//   for (int i = 0; i < 6; i++) {
//     setL298(i, constrain((int)currentSpeeds[i], -255, 255));
//   }

//   // 2. Update Motor via PCA9685 (Index ke-6 pada Python Anda)
//   setPCAMotor(constrain(targetSpeeds[6], -4095, 4095));

//   // 3. Update 3 Relay (Index 7, 8, 9) -> Active LOW
//   digitalWrite(relay1, targetSpeeds[7] == 1 ? LOW : HIGH);
//   digitalWrite(relay2, targetSpeeds[8] == 1 ? LOW : HIGH);
//   digitalWrite(relay3, targetSpeeds[9] == 1 ? LOW : HIGH);
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

// void setPCAMotor(int pwm) {
//   // Asumsi PCA9685 Pin 0 (Maju) dan Pin 1 (Mundur) untuk driver motor eksternal
//   if (pwm > 0) {
//     pca.setPin(0, pwm, false);
//     pca.setPin(1, 0, false);
//   } else if (pwm < 0) {
//     pca.setPin(0, 0, false);
//     pca.setPin(1, -pwm, false);
//   } else {
//     pca.setPin(0, 0, false);
//     pca.setPin(1, 0, false);
//   }
// }

// void sendTelemetry() {
//    byte pkt[7] = {0xBB, 0x66, 0x0D, 0x04, 0x00, 0x0D, 0x0A}; 
//    Serial.write(pkt, 7);
// }