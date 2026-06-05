#include <avr/wdt.h> // [WAJIB] Library untuk fitur Auto-Reset
#include <Wire.h>
#include <VL53L1X.h>
VL53L1X sensor2;

#define TCAADDR 0x70 
#define CMPS12_ADDRESS 0x60

#define FILTER_SIZE 5
int history[3][FILTER_SIZE]; 

int getFiltered(uint8_t idx, int newVal) {
  static uint8_t pos[3] = {0};
  history[idx][pos[idx]] = newVal;
  pos[idx] = (pos[idx] + 1) % FILTER_SIZE;

  int temp[FILTER_SIZE];
  for (int i = 0; i < FILTER_SIZE; i++) temp[i] = history[idx][i];

  for (int i = 0; i < FILTER_SIZE - 1; i++) {
    for (int j = i + 1; j < FILTER_SIZE; j++) {
      if (temp[j] < temp[i]) {
        int t = temp[i];
        temp[i] = temp[j];
        temp[j] = t;
      }
    }
  }
  return temp[FILTER_SIZE / 2]; 
}

#define MAX_DELTA_CM 15    // Toleransi perubahan maksimal (cm) dalam 40ms. Sesuaikan dengan top speed robot!
#define MAX_REJECT_COUNT 3 // Jika 3x berturut-turut datanya aneh, anggap itu benda nyata yang baru muncul

int getRobustDistance(uint8_t idx, int newVal) {
  static int lastValid[3] = {0, 0, 0};
  static int rejectCount[3] = {0, 0, 0};

  // 1. Jika ini pembacaan pertama atau error dari sensor (misal timeout/-1)
  if (lastValid[idx] == 0 || newVal <= 0) {
    lastValid[idx] = newVal > 0 ? newVal : lastValid[idx];
    return getFiltered(idx, newVal); 
  }

  // 2. Hitung seberapa drastis perubahannya
  int delta = abs(newVal - lastValid[idx]);

  // 3. Logika pengecekan noise (Rate of Change)
  if (delta > MAX_DELTA_CM) {
    rejectCount[idx]++;
    
    if (rejectCount[idx] < MAX_REJECT_COUNT) {
      // ABAIKAN NOISE: Gunakan jarak valid terakhir untuk dimasukkan ke Median Filter
      return getFiltered(idx, lastValid[idx]);
    } else {
      // GAGAL SENSOR / BENDA BARU MUNCUL TIBA-TIBA: Mulai percayai data ini
      rejectCount[idx] = 0;
      lastValid[idx] = newVal;
      return getFiltered(idx, newVal);
    }
  } else {
    // Data normal & masuk akal
    rejectCount[idx] = 0;
    lastValid[idx] = newVal;
    return getFiltered(idx, newVal);
  }
}

// UKURAN ARRAY DISESUAIKAN MENJADI 17
// Index Mapping:
// [0]: Heading, [1]: VL53L1X, [2]: Kanan, [3]: Kiri, [4]: Belakang
// [5]: Proxi Blkg, [6]: Limit 0, [7]: Limit 1, [8]: Limit 2, [9]: Limit 3, [10]: Proxi Dpn
// [11]: Pitch, [12]: Rata Kiri (ProxiKfs 0), [13]: Rata Kanan (1), [14]: Dpn (2), [15]: Kanan (3), [16]: Kiri (4)
int16_t data_masuk[17] = {0}; 
unsigned long lastS2 = 0, lastComm = 0;

// const int pinT[3] = {42, 38, 36};
// const int pinE[3] = {44, 46, 34};
const int pinT[3] = {38, 42, 36};
const int pinE[3] = {46, 44, 34};

const long timeout[3] = {20000, 17000, 15000}; 

const int ProxiBelakang = -1;
const int ProxiDepan = 28;
const int limitcapit [4] = {30, 32, 31, 33};
const int ProxiKfsCapit [5] = {-1, A1, 45, 43, 41};
const int tombol_start = 40;
const int tombol_reset = 54;
unsigned long lastUltra = 0;
int16_t sudut_x_dari_esp32 = 0;

void tcaselect(uint8_t i) {
  Wire.beginTransmission(TCAADDR);
  Wire.write(1 << i);
  Wire.endTransmission();
}

void updateCompassData() {
  tcaselect(7);
  Wire.beginTransmission(CMPS12_ADDRESS);
  Wire.write(2); 
  Wire.endTransmission();
  
  Wire.requestFrom(CMPS12_ADDRESS, 6); 
  if (Wire.available() >= 6) {
    data_masuk[0]  = ((Wire.read() << 8) | Wire.read()) / 10; // Heading
    data_masuk[11] = (int8_t)Wire.read();                    // Pitch
    // data_masuk[17] (Roll) bisa ditambahkan jika array diperbesar lagi
  }
}

void setup() {
  Serial.begin(115200);
  Serial2.begin(115200);
  // [WAJIB] Matikan Watchdog saat booting agar tidak boot-loop
  wdt_disable();
  Wire.begin();
  Wire.setClock(400000); 

  pinMode(ProxiBelakang, INPUT_PULLUP);
  pinMode(ProxiDepan, INPUT_PULLUP);
  pinMode(tombol_start, INPUT_PULLUP);
  pinMode(tombol_reset, INPUT_PULLUP);
  
  for (int i = 0; i < 4; i++) pinMode(limitcapit[i], INPUT_PULLUP);
  for (int i = 0; i < 5; i++) pinMode(ProxiKfsCapit[i], INPUT_PULLUP);

  tcaselect(6);
  sensor2.init();
  sensor2.setDistanceMode(VL53L1X::Long);
  sensor2.startContinuous(50);

  for (int i = 0; i < 3; i++) {
    pinMode(pinT[i], OUTPUT);
    pinMode(pinE[i], INPUT);
  }
}

void loop() {
  unsigned long currentMillis = millis();

  // =======================================================
  // [SISTEM ANTI-FREEZE] DETEKSI TRIGGER DARI JETSON NANO
  // =======================================================
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    if (cmd == 'R') {
      wdt_enable(WDTO_15MS); // Aktifkan timer kematian 15ms
      while (1) {}           // Jebak program selamanya agar memicu Hardware Reset
    }
  }


  // Membaca data binary mentah dari ESP32 (Harus tersedia 2 byte)
  while (Serial2.available() >= 2) {
    uint8_t byte_rendah = Serial2.read(); // LSB dibaca pertama
    uint8_t byte_tinggi = Serial2.read(); // MSB dibaca kedua
    
    // Menggabungkan kembali 2 byte menjadi 1 variabel int16_t
    sudut_x_dari_esp32 = (byte_tinggi << 8) | byte_rendah; 
  }

  // Jika buffer menumpuk tak wajar (mencegah out-of-sync ganjil)
  if (Serial2.available() > 10) { 
    while(Serial2.available()) Serial2.read(); // Kuras buffer (flush)
  }


  // Memasukkan data digital ke index 12-16
  data_masuk[16] = digitalRead(tombol_reset); // kiri
  data_masuk[15] = digitalRead(tombol_start); // kanan
  data_masuk[14] = digitalRead(ProxiKfsCapit[2]); // dpn 
  data_masuk[13] = digitalRead(ProxiKfsCapit[1]); // rata kanan
  data_masuk[12] = digitalRead(ProxiKfsCapit[0]); // rata kiri

  // Memasukkan data digital ke index 5-10
  data_masuk[10] = digitalRead(ProxiDepan);
  data_masuk[9] = digitalRead(limitcapit[3]);
  data_masuk[8] = digitalRead(limitcapit[2]);
  data_masuk[7] = digitalRead(limitcapit[1]);
  data_masuk[6]  = sudut_x_dari_esp32;
  data_masuk[5] = digitalRead(ProxiBelakang);

  // 1. Baca Ultrasonik (Setiap 40ms agar pantulan suara hilang dulu)
  if (currentMillis - lastUltra >= 40) {
    lastUltra = currentMillis;
    for (int i = 0; i < 3; i++) {
      digitalWrite(pinT[i], LOW);
      delayMicroseconds(2);
      digitalWrite(pinT[i], HIGH);
      delayMicroseconds(10);
      digitalWrite(pinT[i], LOW);

      long duration = pulseIn(pinE[i], HIGH, timeout[i]);

      // data_masuk[i + 2] = (duration == 0) ? -1 : (duration * 0.0343 / 2);

      if(i == 2){ // Sensor belakang tanpa filter
        data_masuk[i + 2] = (duration == 0) ? -1 : (duration * 0.0343 / 2);
      } else { // Sensor kiri & kanan pakai filter
        int jarak = duration * 0.0343 / 2;
        data_masuk[i + 2] = getRobustDistance(i, jarak);
      }
      
      // JEDA SANGAT PENTING: Mencegah sensor 1 mengganggu sensor 2
      delay(5); 
    }
  }

  // 2. Baca Sensor VL53L1X (Index 1)
  if (currentMillis - lastS2 >= 50) {
    lastS2 = currentMillis;
    tcaselect(6);
    int16_t d = sensor2.read(false);
    data_masuk[1] = (d > 0 && d < 4000) ? d : -1;
  }

  // 3. Kirim Data (Setiap 50ms)
  if (currentMillis - lastComm >= 50) {
    lastComm = currentMillis;
    
    updateCompassData();
    
    byte calc_crc = 0;
    byte* data_bytes = (byte*) data_masuk; 
    
    // 17 int16_t = 34 byte payload
    int payloadSize = 17 * sizeof(int16_t); 
    
    for (int i = 0; i < payloadSize; i++) calc_crc ^= data_bytes[i];
    
    Serial.write(0xAA);             // Header 1
    Serial.write(0x55);             // Header 2
    Serial.write(data_bytes, payloadSize); // Kirim 34 byte
    Serial.write(calc_crc);         // Checksum
    Serial.write(0x0D);             // Trailer
    Serial.write(0x0A);             // Trailer
  }
}