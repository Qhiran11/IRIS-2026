#include <Wire.h>
#include <VL53L1X.h>

VL53L1X sensor1; 
VL53L1X sensor2;

#define TCAADDR 0x70 
#define CMPS12_ADDRESS 0x60

int16_t data_masuk[12];
unsigned long lastS1 = 0, lastS2 = 0, lastComm = 0;


const int pinList[] = {
  28, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, A0, A1
//0    1   2  3    4   5   6   7   8   9  10  11  12  13  14  15  16  17  18  19
};



void tcaselect(uint8_t i) {
  Wire.beginTransmission(TCAADDR);
  Wire.write(1 << i);
  Wire.endTransmission();
}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  Wire.setClock(100000);
  delay(500);

  // Inisialisasi Sensor 1
  tcaselect(5);
  sensor1.init();
  sensor1.setDistanceMode(VL53L1X::Long);
  sensor1.startContinuous(50);

  // Inisialisasi Sensor 2
  tcaselect(6);
  sensor2.init();
  sensor2.setDistanceMode(VL53L1X::Long);
  sensor2.startContinuous(50);
  for (int i = 0; i < 20; i++) {
    pinMode(pinList[i], INPUT_PULLUP); 
    // Gunakan INPUT_PULLUP jika pin tidak terhubung ke resistor eksternal
  }
}

void loop() {
  unsigned long currentMillis = millis();

  data_masuk[3] = digitalRead(pinList[1]);

  // Task 1: Baca Sensor 1 (Tiap 50ms) - Non-Blocking
  if (currentMillis - lastS1 >= 50) {
    lastS1 = currentMillis;
    tcaselect(5);
    // Menggunakan fungsi read() tanpa memblokir
    uint16_t c = sensor1.read(false) - 2320; 
    if (c > 0 && c < 4000) data_masuk[2] = c;
    else data_masuk[2] = -1;
  }

  // Task 2: Baca Sensor 2 (Tiap 50ms) - Offset sedikit
  if (currentMillis - lastS2 >= 80) { // Sedikit delay agar I2C tidak tabrakan
    lastS2 = currentMillis;
    tcaselect(6);
    uint16_t d = sensor2.read(false) - 2320;
    if (d > 0 && d < 4000) data_masuk[1] = d;
    else data_masuk[1] = -1;
  }

  // Task 3: Baca Kompas & Kirim Data (Tiap 100ms)
  if (currentMillis - lastComm >= 100) {
    lastComm = currentMillis;
    data_masuk[0] = getRawBearing();
  }
    // Output Serial
    Serial.print(data_masuk[0]);Serial.print(" ");Serial.print(data_masuk[1]);Serial.print(" ");Serial.println(data_masuk[2]);

  // BACA SENSOR PROXIMITY
  


  // if (currentMillis - lastComm >= 50) {
  //   lastComm = currentMillis;
  //   data_masuk[0] = getRawBearing();
    
  //   // Perhitungan CRC
  //   byte calc_crc = 0;
  //   byte* data_bytes = (byte*) data_masuk; 
  //   for (int i = 0; i < 24; i++) {
  //     calc_crc ^= data_bytes[i];
  //   }
    
  //   // Pengiriman Data ke Python
  //   Serial.write(0xAA);
  //   Serial.write(0x55);
  //   Serial.write(data_bytes, 24);
  //   Serial.write(calc_crc);
  //   Serial.write(0x0D);
  //   Serial.write(0x0A);
  // }


  
}

int getRawBearing() {
  tcaselect(7);
  Wire.beginTransmission(CMPS12_ADDRESS);
  Wire.write(2); 
  Wire.endTransmission();
  Wire.requestFrom(CMPS12_ADDRESS, 2);
  if (Wire.available() >= 2) {
    int16_t bearing = (Wire.read() << 8) | Wire.read();
    return bearing / 10;
  }
  return 0;
}