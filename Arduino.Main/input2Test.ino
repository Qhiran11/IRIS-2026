// #include <avr/wdt.h>
// #include <Wire.h>

// #define CMPS12_ADDRESS 0x60
// #define NUM_SENSORS 4      // Jumlah sensor ultrasonik
// #define FILTER_SIZE 5
// #define MAX_DELTA_CM 15    
// #define MAX_REJECT_COUNT 3 

// int history[NUM_SENSORS][FILTER_SIZE]; 

// int getFiltered(uint8_t idx, int newVal) {
//   static uint8_t pos[NUM_SENSORS] = {0};
//   history[idx][pos[idx]] = newVal;
//   pos[idx] = (pos[idx] + 1) % FILTER_SIZE;

//   int temp[FILTER_SIZE];
//   for (int i = 0; i < FILTER_SIZE; i++) temp[i] = history[idx][i];

//   // Algoritma Bubble Sort
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

// int getRobustDistance(uint8_t idx, int newVal) {
//   static int lastValid[NUM_SENSORS] = {0};
//   static int rejectCount[NUM_SENSORS] = {0};

//   // 1. Jika ini pembacaan pertama atau data gagal (0 / -1)
//   if (lastValid[idx] == 0 || newVal <= 0) {
//     lastValid[idx] = newVal > 0 ? newVal : lastValid[idx];
//     return getFiltered(idx, newVal); 
//   }

//   // 2. Evaluasi noise dari jarak yang terukur
//   if (abs(newVal - lastValid[idx]) > MAX_DELTA_CM) {
//     rejectCount[idx]++;
//     if (rejectCount[idx] < MAX_REJECT_COUNT) {
//       // ABAIKAN NOISE: Pertahankan data valid sebelumnya
//       return getFiltered(idx, lastValid[idx]);
//     }
//   }

//   // 3. Data terverifikasi valid (bukan noise, atau benda baru sudah konsisten 3x terbaca)
//   rejectCount[idx] = 0;
//   lastValid[idx] = newVal;
//   return getFiltered(idx, newVal);
// }

// int16_t data_masuk[17] = {0}; 
// unsigned long lastComm = 0;
// unsigned long lastUltra = 0;
// uint8_t current_sensor = 0; // Penanda giliran sensor ultrasonik

// const int pinT[NUM_SENSORS] = {28, 38, 42, 36}; 
// const int pinE[NUM_SENSORS] = {30, 46, 44, 34}; 
// const long timeout[NUM_SENSORS] = {17000, 25000, 25000, 15000}; 

// const int proxiBelakang = 31;
// const int proxiDepan = 31;

// const int tombol_start = 40;
// const int tombol_reset = 54;

// void updateCompassData() {
//   Wire.beginTransmission(CMPS12_ADDRESS);
//   Wire.write(2); 
//   Wire.endTransmission();
  
//   Wire.requestFrom(CMPS12_ADDRESS, 6); 
//   if (Wire.available() >= 6) {
//     data_masuk[0]  = ((Wire.read() << 8) | Wire.read()) / 10; 
//     data_masuk[9] = (int8_t)Wire.read();                    
//   }
// }

// void setup() {
//   Serial.begin(115200);
//   Serial2.begin(115200);
  
//   wdt_disable();
//   Wire.begin();
//   Wire.setClock(400000); 

//   pinMode(tombol_start, INPUT_PULLUP);
//   pinMode(tombol_reset, INPUT_PULLUP);
//   pinMode(proxiBelakang, INPUT);
//   pinMode(proxiDepan, INPUT);

//   for (int i = 0; i < NUM_SENSORS; i++) {
//     pinMode(pinT[i], OUTPUT);
//     pinMode(pinE[i], INPUT);
//   }
// }

// void loop() {
//   unsigned long currentMillis = millis();

//   // =======================================================
//   // SISTEM ANTI-FREEZE / HARDWARE RESET
//   // =======================================================
//   if (Serial.available() > 0) {
//     if (Serial.read() == 'R') {
//       wdt_enable(WDTO_15MS); 
//       while (1) {}          
//     }
//   }

//   // Update Data Digital (Sesuai urutan index)
//   data_masuk[7] = digitalRead(proxiBelakang);
//   data_masuk[8] = digitalRead(proxiDepan); 
//   data_masuk[6] = digitalRead(tombol_reset); 
//   data_masuk[5] = digitalRead(tombol_start); 

//   // =======================================================
//   // BACA ULTRASONIK (SISTEM GILIRAN NON-BLOCKING)
//   // =======================================================
//   // Tembak 1 sensor setiap 15ms. Jeda ini otomatis bertindak 
//   // sebagai waktu agar pantulan suara hilang untuk sensor berikutnya.
//   if (currentMillis - lastUltra >= 15) {
//     lastUltra = currentMillis;

//     digitalWrite(pinT[current_sensor], LOW);
//     delayMicroseconds(2);
//     digitalWrite(pinT[current_sensor], HIGH);
//     delayMicroseconds(10);
//     digitalWrite(pinT[current_sensor], LOW);

//     long duration = pulseIn(pinE[current_sensor], HIGH, timeout[current_sensor]);
//     int jarak = duration * 0.0343 / 2;
    
//     // Simpan ke array, urutan tetap dipertahankan
//     data_masuk[current_sensor + 1] = getRobustDistance(current_sensor, jarak);

//     // Geser antrean ke sensor selanjutnya (0 -> 1 -> 2 -> 3 -> kembali ke 0)
//     current_sensor = (current_sensor + 1) % NUM_SENSORS; 
//   }

//   // =======================================================
//   // KIRIM DATA SERIAL KE JETSON NANO (SETIAP 50MS)
//   // =======================================================
//   if (currentMillis - lastComm >= 50) {
//     lastComm = currentMillis;
    
//     updateCompassData();
    
//     byte calc_crc = 0;
//     byte* data_bytes = (byte*) data_masuk; 
//     int payloadSize = 17 * sizeof(int16_t); 
    
//     for (int i = 0; i < payloadSize; i++) {
//       calc_crc ^= data_bytes[i];
//     }
    
//     Serial.write(0xAA); 
//     Serial.write(0x55); 
//     Serial.write(data_bytes, payloadSize); 
//     Serial.write(calc_crc); 
//     Serial.write(0x0D); 
//     Serial.write(0x0A); 
//   }
// }