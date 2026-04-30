// #include <Wire.h>
// #include <VL53L1X.h>

// VL53L1X sensor2;
// #define TCAADDR 0x70 
// #define CMPS12_ADDRESS 0x60

// // Indeks data_masuk: 
// // [0]: Kompas, [1]: VL53L1X, [2]: Kiri, [3]: Kanan, [4]: Belakang, [5]: Depan
// int16_t data_masuk[12] = {0}; 
// unsigned long lastS2 = 0, lastComm = 0;

// // Pin:        Kanan (1), kiri (2), belakang (3) 
// const int pinT[3] = {42, 54, 34};
// const int pinE[3] = {44, 46, 36};
// const int timeout[3] = {25000, 25000, 8000}; // dalam microsecond

// void tcaselect(uint8_t i) {
//   Wire.beginTransmission(TCAADDR);
//   Wire.write(1 << i);
//   Wire.endTransmission();
// }

// int getRawBearing() {
//   tcaselect(7);
//   Wire.beginTransmission(CMPS12_ADDRESS);
//   Wire.write(2); 
//   Wire.endTransmission();
//   Wire.requestFrom(CMPS12_ADDRESS, 2);
//   if (Wire.available() >= 2) {
//     return ((Wire.read() << 8) | Wire.read()) / 10;
//   }
//   return 0;
// }

// void setup() {
//   Serial.begin(115200);
//   Wire.begin();
//   Wire.setClock(400000); // Naikkan ke 400kHz untuk performa I2C lebih baik

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

//   // 1. Baca Ultrasonik (Non-Blocking)
//   for (int i = 0; i < 3; i++) {
//     digitalWrite(pinT[i], LOW);
//     delayMicroseconds(2);
//     digitalWrite(pinT[i], HIGH);
//     delayMicroseconds(10);
//     digitalWrite(pinT[i], LOW);

//     long duration = pulseIn(pinE[i], HIGH, timeout[i]); 
//     data_masuk[i + 2] = (duration == 0) ? -1 : (duration * 0.0343 / 2);
//   }

//   // 2. Baca Sensor I2C (Setiap 50ms)
//   if (currentMillis - lastS2 >= 50) {
//     lastS2 = currentMillis;
//     tcaselect(6);
//     int16_t d = sensor2.read(false);
//     data_masuk[1] = (d > 0 && d < 4000) ? d : -1;
//   }

//   // 3. Kirim Data (Setiap 50ms)
//   if (currentMillis - lastComm >= 50) {
//     lastComm = currentMillis;
//     data_masuk[0] = getRawBearing();
    
//     byte calc_crc = 0;
//     byte* data_bytes = (byte*) data_masuk; 
//     for (int i = 0; i < 24; i++) calc_crc ^= data_bytes[i];
    
//     Serial.write(0xAA);
//     Serial.write(0x55);
//     Serial.write(data_bytes, 24);
//     Serial.write(calc_crc);
//     Serial.write(0x0D);
//     Serial.write(0x0A);
//   }
// }