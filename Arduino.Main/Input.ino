// #include <Wire.h>
// #include <VL53L1X.h>
// VL53L1X sensor2;

// #define TCAADDR 0x70 
// #define CMPS12_ADDRESS 0x60

// #define FILTER_SIZE 3
// int history[3][FILTER_SIZE]; 

// int getFiltered(uint8_t idx, int newVal) {
//   static uint8_t pos[3] = {0};
//   history[idx][pos[idx]] = newVal;
//   pos[idx] = (pos[idx] + 1) % FILTER_SIZE;

//   int temp[FILTER_SIZE];
//   for (int i = 0; i < FILTER_SIZE; i++) temp[i] = history[idx][i];

//   for (int i = 0; i < FILTER_SIZE - 1; i++) {
//     for (int j = i + 1; j < FILTER_SIZE; j++) {
//       if (temp[j] < temp[i]) {
//         int t = temp[i];
//         temp[i] = temp[j];
//         temp[j] = t;
//       }
//     }
//   }
//   return temp[FILTER_SIZE / 2]; 
// }

// // UKURAN ARRAY DISESUAIKAN MENJADI 17
// // Index Mapping:
// // [0]: Heading, [1]: VL53L1X, [2]: Kanan, [3]: Kiri, [4]: Belakang
// // [5]: Proxi Blkg, [6]: Limit 0, [7]: Limit 1, [8]: Limit 2, [9]: Limit 3, [10]: Proxi Dpn
// // [11]: Pitch, [12]: Rata Kiri (ProxiKfs 0), [13]: Rata Kanan (1), [14]: Dpn (2), [15]: Kanan (3), [16]: Kiri (4)
// int16_t data_masuk[17] = {0}; 
// unsigned long lastS2 = 0, lastComm = 0;

// const int pinT[3] = {42, 38, 36};
// const int pinE[3] = {44, 46, 34};
// const long timeout[3] = {25000, 10000, 8000}; 

// const int ProxiBelakang = 40;
// const int ProxiDepan = 28;
// const int limitcapit [4] = {30, 32, 31, 33};
// const int ProxiKfsCapit [5] = {A0, A1, 45, 43, 41};

// void tcaselect(uint8_t i) {
//   Wire.beginTransmission(TCAADDR);
//   Wire.write(1 << i);
//   Wire.endTransmission();
// }

// void updateCompassData() {
//   tcaselect(7);
//   Wire.beginTransmission(CMPS12_ADDRESS);
//   Wire.write(2); 
//   Wire.endTransmission();
  
//   Wire.requestFrom(CMPS12_ADDRESS, 6); 
//   if (Wire.available() >= 6) {
//     data_masuk[0]  = ((Wire.read() << 8) | Wire.read()) / 10; // Heading
//     data_masuk[11] = (int8_t)Wire.read();                    // Pitch
//     // data_masuk[17] (Roll) bisa ditambahkan jika array diperbesar lagi
//   }
// }

// void setup() {
//   Serial.begin(115200);
//   Wire.begin();
//   Wire.setClock(400000); 

//   pinMode(ProxiBelakang, INPUT_PULLUP);
//   pinMode(ProxiDepan, INPUT_PULLUP);
  
//   for (int i = 0; i < 4; i++) pinMode(limitcapit[i], INPUT_PULLUP);
//   for (int i = 0; i < 5; i++) pinMode(ProxiKfsCapit[i], INPUT_PULLUP);

//   tcaselect(6);
//   sensor2.init();
//   sensor2.setDistanceMode(VL53L1X::Long);
//   sensor2.startContinuous(50);

//   for (int i = 0; i < 3; i++) {
//     pinMode(pinT[i], OUTPUT);
//     pinMode(pinE[i], INPUT);
//   }
// }

// void loop() {
//   unsigned long currentMillis = millis();

//   // Memasukkan data digital ke index 12-16
//   data_masuk[16] = digitalRead(ProxiKfsCapit[4]); // kiri
//   data_masuk[15] = digitalRead(ProxiKfsCapit[3]); // kanan
//   data_masuk[14] = digitalRead(ProxiKfsCapit[2]); // dpn 
//   data_masuk[13] = digitalRead(ProxiKfsCapit[1]); // rata kanan
//   data_masuk[12] = digitalRead(ProxiKfsCapit[0]); // rata kiri

//   // Memasukkan data digital ke index 5-10
//   data_masuk[10] = digitalRead(ProxiDepan);
//   data_masuk[9] = digitalRead(limitcapit[3]);
//   data_masuk[8] = digitalRead(limitcapit[2]);
//   data_masuk[7] = digitalRead(limitcapit[1]);
//   data_masuk[6] = digitalRead(limitcapit[0]);
//   data_masuk[5] = digitalRead(ProxiBelakang);

//   // 1. Baca Ultrasonik (Index 2, 3, 4)
//   for (int i = 0; i < 3; i++) {
//     digitalWrite(pinT[i], LOW);
//     delayMicroseconds(2);
//     digitalWrite(pinT[i], HIGH);
//     delayMicroseconds(10);
//     digitalWrite(pinT[i], LOW);

//     long duration = pulseIn(pinE[i], HIGH, timeout[i]); 

//     if(i == 2){
//       data_masuk[i + 2] = (duration == 0) ? -1 : (duration * 0.0343 / 2);
//     } else {
//       int jarak = duration * 0.0343 / 2;
//       data_masuk[i + 2] = getFiltered(i, jarak);
//     }
//   }

//   // 2. Baca Sensor VL53L1X (Index 1)
//   if (currentMillis - lastS2 >= 50) {
//     lastS2 = currentMillis;
//     tcaselect(6);
//     int16_t d = sensor2.read(false);
//     data_masuk[1] = (d > 0 && d < 4000) ? d : -1;
//   }

//   // 3. Kirim Data (Setiap 50ms)
//   if (currentMillis - lastComm >= 50) {
//     lastComm = currentMillis;
    
//     updateCompassData();
    
//     byte calc_crc = 0;
//     byte* data_bytes = (byte*) data_masuk; 
    
//     // 17 int16_t = 34 byte payload
//     int payloadSize = 17 * sizeof(int16_t); 
    
//     for (int i = 0; i < payloadSize; i++) calc_crc ^= data_bytes[i];
    
//     Serial.write(0xAA);             // Header 1
//     Serial.write(0x55);             // Header 2
//     Serial.write(data_bytes, payloadSize); // Kirim 34 byte
//     Serial.write(calc_crc);         // Checksum
//     Serial.write(0x0D);             // Trailer
//     Serial.write(0x0A);             // Trailer
//   }
// }