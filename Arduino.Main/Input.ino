#include <Wire.h>
#include <avr/wdt.h>

#define CMPS12_ADDRESS 0x60
#define NUM_TARGET_SENSORS 4   // Diubah menjadi 4 sensor (Depan, Belakang, Kanan, Kiri)
#define FILTER_SIZE 5
#define MAX_DELTA_CM 15    
#define MAX_REJECT_COUNT 3 

// =======================================================
// VARIABEL & PIN SENSOR
// =======================================================
// Pemetaan Index Array: 0=Depan, 1=Belakang, 2=Kanan, 3=Kiri
const int trigPins[NUM_TARGET_SENSORS] = {36, 37, 32, 18}; 
const int echoPins[NUM_TARGET_SENSORS] = {38, 35, 34, 19}; 

// Variabel untuk Filter Ultrasonik
int history[NUM_TARGET_SENSORS][FILTER_SIZE];
int16_t jarak_filter[NUM_TARGET_SENSORS] = {0}; 
unsigned long lastUltra = 0;
unsigned long lastComm = 0;
uint8_t current_sensor = 0;
int proxi = 43; 

// Variabel Data Eksternal
int nanoDataA = 1;
int nanoDataB = 1;
int cmpsHeading = 0;
int8_t cmpsPitch = 0; 

// Array Data Pengiriman (17 int16_t -> 34 bytes)
int16_t data_kirim[17] = {0};

// =======================================================
// FUNGSI CMPS12 (I2C)
// =======================================================
int readCMPS12() {
  Wire.beginTransmission(CMPS12_ADDRESS);
  Wire.write(2); // Mulai dari register 2 (Bearing High) 
  if (Wire.endTransmission() != 0) {
    return cmpsHeading; // Proteksi jika koneksi I2C terputus sesaat
  }
  
  Wire.requestFrom(CMPS12_ADDRESS, 6);
  if (Wire.available() >= 6) { 
    cmpsHeading = ((Wire.read() << 8) | Wire.read()) / 10; 
    cmpsPitch   = (int8_t)Wire.read(); 
    
    while(Wire.available()) {
      Wire.read(); // Kuras sisa buffer
    }
  }
  return cmpsHeading;
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
  
  // Median Filter Sorting
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
// FUNGSI NON-BLOCKING PARSER DATA DARI NANO
// =======================================================
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
        rxIdx = 0; // Reset buffer jika overflow 
      }
    }
  }
}

// =======================================================
// SETUP AWAL
// =======================================================
void setup() {
  Serial.begin(115200); // Komunikasi ke PC / Jetson 
  Serial2.begin(9600);  // Komunikasi ke Nano 
  
  wdt_disable();

  // Setup I2C untuk CMPS12
  Wire.begin();
  Wire.setClock(400000); // I2C Fast Mode 
  readCMPS12();
  
  pinMode(proxi, INPUT); 

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
      while(1) {} // Memicu Watchdog reset 
    }
  }

  // 2. Cek pesan masuk dari Nano secara kontinyu
  readDataFromNano(); 
  unsigned long currentMillis = millis(); 

  // --- 3. PEMBACAAN KOMPAS (Super Cepat: Setiap 10ms secara Terpisah) ---
  static unsigned long lastCmps = 0;
  if (currentMillis - lastCmps >= 10) {
    lastCmps = currentMillis;
    readCMPS12(); 
  }

  // --- 4. PEMBACAAN ULTRASONIK (Sistem Giliran 15ms) ---
  if (currentMillis - lastUltra >= 15) { 
    lastUltra = currentMillis; 
    
    int activeTrig = trigPins[current_sensor]; 
    int activeEcho = echoPins[current_sensor]; 

    digitalWrite(activeTrig, LOW); 
    delayMicroseconds(2); 
    digitalWrite(activeTrig, HIGH); 
    delayMicroseconds(10); 
    digitalWrite(activeTrig, LOW); 
    
    // Timeout dipangkas ke 20000 us (~3.4 meter) agar tidak memblokir loop jika area kosong
    long duration = pulseIn(activeEcho, HIGH, 20000); 
    int jarak = duration * 0.0343 / 2; 
    
    jarak_filter[current_sensor] = getRobustDistance(current_sensor, jarak); 
    
    current_sensor = (current_sensor + 1) % NUM_TARGET_SENSORS; 
  }

  // --- 5. KIRIM DATA PAKET BINER (Dipercepat dari 50ms ke 20ms / 50Hz) ---
  if (currentMillis - lastComm >= 20) {
    lastComm = currentMillis;
    
    // Pemetaan indeks array diselaraskan secara presisi dengan script Python robot_data.py
    data_kirim[0] = cmpsHeading;      // arr[0] -> Kompas Relatif
    data_kirim[1] = jarak_filter[0];  // arr[1] -> Ultrasonic Depan
    data_kirim[2] = jarak_filter[3];  // arr[2] -> Ultrasonic Kiri
    data_kirim[3] = jarak_filter[2];  // arr[3] -> Ultrasonic Kanan
    data_kirim[4] = jarak_filter[1];  // arr[4] -> Ultrasonic Belakang
    
    data_kirim[5] = nanoDataA;        // arr[5] -> Tombol Start
    data_kirim[6] = nanoDataB;        // arr[6] -> Tombol Reset
    
    // Mengosongkan data sensor yang tidak terpakai agar panjang payload paket tetap biner 34 bytes
    data_kirim[7] = 0; 
    data_kirim[8] = 0; 
    data_kirim[9] = 0; 
    data_kirim[10] = 0;               // Pitch (Diabaikan)
    data_kirim[11] = digitalRead(proxi); // arr[11] -> Proximity / Limit Capit
    data_kirim[12] = 0;
    data_kirim[13] = 0;
    data_kirim[14] = 0;
    data_kirim[15] = 0;
    data_kirim[16] = 0;

    // Hitung CRC Paket Data
    byte calc_crc = 0;
    byte* data_bytes = (byte*)data_kirim; 
    int payloadSize = 17 * sizeof(int16_t); // 34 bytes 

    for (int i = 0; i < payloadSize; i++) {
      calc_crc ^= data_bytes[i]; 
    }

    // Pengiriman Protokol Paket ke Serial Jetson
    Serial.write(0xAA);
    Serial.write(0x55);
    Serial.write(data_bytes, payloadSize);
    Serial.write(calc_crc);
    Serial.write(0x0D);
    Serial.write(0x0A);
  }
}