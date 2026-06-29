#include <Wire.h>
#include <avr/wdt.h>

#define CMPS12_ADDRESS 0x60
#define NUM_TARGET_SENSORS 6
#define FILTER_SIZE 5
#define MAX_DELTA_CM 15    
#define MAX_REJECT_COUNT 3 

// =======================================================
// VARIABEL & PIN
// =======================================================
// S1(Bwh Tgh), S2(Kanan), S3(Bwh Dpn), S4(Depan), S5(Blkg), S6(Bwh Blkg)
const int trigPins[NUM_TARGET_SENSORS] = {28, 32, 33, 36, 37, 41};
const int echoPins[NUM_TARGET_SENSORS] = {30, 34, 31, 38, 35, 39};

// Variabel untuk Filter Ultrasonik
int history[NUM_TARGET_SENSORS][FILTER_SIZE]; 
int16_t jarak_filter[NUM_TARGET_SENSORS] = {0};
unsigned long lastUltra = 0;
unsigned long lastComm = 0;
uint8_t current_sensor = 0;

// Variabel Data Eksternal
int nanoDataA = 1;
int nanoDataB = 1;
int cmpsHeading = 0;
int8_t cmpsPitch = 0;

// Array Data Pengiriman (17 int16_t -> 34 bytes)
int16_t data_kirim[17] = {0};

// S7 UART Jarak (kiri)
float jarakS7 = -1.0;

// =======================================================
// FUNGSI CMPS12 (I2C)
// =======================================================
int readCMPS12() {
  Wire.beginTransmission(CMPS12_ADDRESS);
  Wire.write(2); // Mulai dari register 2 (Bearing High)
  Wire.endTransmission();
  
  Wire.requestFrom(CMPS12_ADDRESS, 6); 
  if (Wire.available() >= 6) {
    cmpsHeading = ((Wire.read() << 8) | Wire.read()) / 10; 
    cmpsPitch   = (int8_t)Wire.read(); 
    
    while(Wire.available()) {
      Wire.read();
    }
    return cmpsHeading;
  }
}

// =======================================================
// FUNGSI FILTER (Ultrasonik)
// =======================================================
int getFiltered(uint8_t idx, int newVal) {
  static uint8_t pos[NUM_TARGET_SENSORS] = {0};
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

int getRobustDistance(uint8_t idx, int newVal) {
  static int lastValid[NUM_TARGET_SENSORS] = {0};
  static int rejectCount[NUM_TARGET_SENSORS] = {0};

  if (lastValid[idx] == 0 || newVal <= 0) {
    lastValid[idx] = newVal > 0 ? newVal : lastValid[idx];
    return getFiltered(idx, newVal); 
  }

  if (abs(newVal - lastValid[idx]) > MAX_DELTA_CM) {
    rejectCount[idx]++;
    if (rejectCount[idx] < MAX_REJECT_COUNT) {
      return getFiltered(idx, lastValid[idx]);
    }
  }

  rejectCount[idx] = 0;
  lastValid[idx] = newVal;
  return getFiltered(idx, newVal);
}

// =======================================================
// FUNGSI SENSOR UART & KOMUNIKASI NANO
// =======================================================
float readSensorS7_UART() {
  while(Serial1.available()) Serial1.read();
  
  Serial1.write(0x55); 
  
  unsigned long startWait = millis();
  while(Serial1.available() < 2 && millis() - startWait < 30) {}
  
  if (Serial1.available() >= 2) {
    byte highByte = Serial1.read();
    byte lowByte  = Serial1.read();
    int jarak_mm = (highByte * 256) + lowByte;
    return jarak_mm / 10.0; 
  }
  return -1.0; 
}

// FUNGSI NON-BLOCKING PARSER DATA DARI NANO
void readDataFromNano() {
  static char rxBuf[32];
  static int rxIdx = 0;
  
  while (Serial2.available() > 0) {
    char c = Serial2.read();
    if (c == '\n' || c == '\r') {
      if (rxIdx > 0) {
        rxBuf[rxIdx] = '\0'; // Null-terminate string
        char* comma = strchr(rxBuf, ',');
        if (comma != NULL) {
          *comma = '\0'; // Membagi string di posisi koma
          nanoDataA = atoi(rxBuf);
          nanoDataB = atoi(comma + 1);
        }
        rxIdx = 0; // Reset index buffer
      }
    } else {
      if (rxIdx < 30) {
        rxBuf[rxIdx++] = c;
      } else {
        rxIdx = 0; // Reset buffer jika overflow (data tidak valid)
      }
    }
  }
}

// =======================================================
// SETUP AWAL
// =======================================================
void setup() {
  Serial.begin(115200); // Komunikasi ke PC / Jetson
  Serial1.begin(9600);  // US-100 UART (S7 Kiri)
  Serial2.begin(9600);  // Komunikasi Nano
  
  wdt_disable();

  // Setup I2C untuk CMPS12
  Wire.begin();
  Wire.setClock(400000); // I2C Fast Mode
  readCMPS12();

  for (int k = 0; k < NUM_TARGET_SENSORS; k++) {
    pinMode(trigPins[k], OUTPUT);
    pinMode(echoPins[k], INPUT);
  }
}

// =======================================================
// LOOP UTAMA
// =======================================================
void loop() {
  // 1. Cek reset 'R' dari Jetson
  if (Serial.available() > 0) {
    if (Serial.read() == 'R') {
      wdt_enable(WDTO_15MS);
      while(1) {}
    }
  }

  // 2. Cek pesan masuk dari Nano secara kontinyu
  readDataFromNano();

  unsigned long currentMillis = millis();

  // 3. Baca Ultrasonik S1-S6 (Sistem Giliran 15ms)
  if (currentMillis - lastUltra >= 15) {
    lastUltra = currentMillis;

    int activeTrig = trigPins[current_sensor];
    int activeEcho = echoPins[current_sensor];

    digitalWrite(activeTrig, LOW);
    delayMicroseconds(2);
    digitalWrite(activeTrig, HIGH);
    delayMicroseconds(10);
    digitalWrite(activeTrig, LOW);

    long duration = pulseIn(activeEcho, HIGH, 150000); // Batasi timeout agar tidak memblokir lama
    int jarak = duration * 0.0343 / 2;
    
    int jarakValid = getRobustDistance(current_sensor, jarak);
    jarak_filter[current_sensor] = jarakValid;
    
    current_sensor = (current_sensor + 1) % NUM_TARGET_SENSORS; 
    
    // 4. Jika 1 siklus ultrasonik selesai, panggil CMPS12 & sensor lainnya
    if (current_sensor == 0) {
      readCMPS12();
      jarakS7 = readSensorS7_UART(); // S7 Kiri (UART)
    }
  }

  // 5. Kirim data paket biner setiap 50ms
  if (currentMillis - lastComm >= 50) {
    lastComm = currentMillis;

    // Masukkan data ke array untuk dikirim (17 elemen)
    data_kirim[0] = readCMPS12();
    data_kirim[1] = jarak_filter[3]; // S4 (Depan)
    data_kirim[2] = (int16_t)jarakS7; // S7 (Kiri) - UART
    data_kirim[3] = jarak_filter[1]; // S2 (Kanan)
    data_kirim[4] = jarak_filter[4]; // S5 (Belakang)
    data_kirim[5] = nanoDataA;       // tombol_start (Nano_A)
    data_kirim[6] = nanoDataB;       // tombol_reset (Nano_B)
    data_kirim[7] = jarak_filter[2]; // S3 (Bawah Depan)
    data_kirim[8] = jarak_filter[0]; // S1 (Bawah Tengah)
    data_kirim[9] = jarak_filter[5]; // S6 (Bawah Belakang)
    data_kirim[10] = cmpsPitch;      // Pitch
    data_kirim[11] = 0;
    data_kirim[12] = 0;
    data_kirim[13] = 0;
    data_kirim[14] = 0;
    data_kirim[15] = 0;
    data_kirim[16] = 0;

    // Hitung CRC
    byte calc_crc = 0;
    byte* data_bytes = (byte*)data_kirim;
    int payloadSize = 17 * sizeof(int16_t); // 34 byte

    for (int i = 0; i < payloadSize; i++) {
      calc_crc ^= data_bytes[i];
    }

    // Kirim paket
    Serial.write(0xAA);
    Serial.write(0x55);
    Serial.write(data_bytes, payloadSize);
    Serial.write(calc_crc);
    Serial.write(0x0D);
    Serial.write(0x0A);
  }
}