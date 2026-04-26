// #include <Wire.h>
// #include <LiquidCrystal_I2C.h>
// #include <VL53L1X.h>

// VL53L1X sensor;

// #define TCAADDR 0x70 
// #define CMPS12_ADDRESS 0x60

// LiquidCrystal_I2C lcd(0x27, 20, 4); 


// int offsetAngle = 0; // Variabel untuk menyimpan selisih sudut
// int16_t data_masuk[12];

// unsigned long lastSentTime = 0;
// const int sendInterval = 100; // Kirim data setiap 50 milidetik (20 Hz)
// const word ResetCMPS = 52;


// void tcaselect(uint8_t i) {
//   if (i > 7) return;
//   Wire.beginTransmission(TCAADDR);
//   Wire.write(1 << i);
//   Wire.endTransmission();
// }

// void setup() {
//   Serial.begin(115200);
//   Wire.begin();
//   randomSeed(analogRead(A0));
//   pinMode(ResetCMPS, INPUT_PULLUP);


//   // Inisialisasi LCD
//   lcd.init();
//   lcd.backlight();
//   lcd.setCursor(0, 0);
//   lcd.print("NANOPA READY");

//   // Inisialisasi Sensor VL53L1X di Channel 6
//   tcaselect(6);
//   if (!sensor.init()) {
//   }
//   sensor.setTimeout(100);
//   sensor.setDistanceMode(VL53L1X::Long);
//   sensor.setMeasurementTimingBudget(50000);
//   sensor.startContinuous(50);

  

// }

// void loop() {

//   unsigned long currentTime = millis();
//   if (currentTime - lastSentTime >= sendInterval) {
//     lastSentTime = currentTime;

//     //////////////////////////////////////
//     data_masuk[0] = getRawBearing(); // 1 => Nilai X CMPS12 untuk arah depan belakang kanan kiri
//     //////////////////////////////////////
//     tcaselect(6);
//     if (sensor.dataReady()) {    
//       sensor.read();                    
//       data_masuk[1] = sensor.ranging_data.range_mm; // 2 => nilai jarak depan
//     }
//     //////////////////////////
    
    
    
//     byte calc_crc = 0;
//     byte* data_bytes = (byte*) data_masuk; 
    
//     for (int i = 0; i < 24; i++) { // 12 data * 2 byte = 24 byte
//       calc_crc ^= data_bytes[i];
//     }
//     Serial.write(0xAA);
//     Serial.write(0x55);
//     Serial.write(data_bytes, 24);
//     Serial.write(calc_crc);
//     Serial.write(0x0D); // CR
//     Serial.write(0x0A); // LF
//   }
// }

// // Fungsi khusus untuk mengambil data bearing asli dari CMPS12
// int getRawBearing() {
//   tcaselect(7);
//   byte highByte, lowByte;
//   Wire.beginTransmission(CMPS12_ADDRESS);
//   Wire.write(2); 
//   Wire.endTransmission();

//   Wire.requestFrom(CMPS12_ADDRESS, 2);
//   if (Wire.available() >= 2) {
//     highByte = Wire.read();
//     lowByte = Wire.read();
//     return ((highByte << 8) + lowByte) / 10;
//   }
//   return 0;
// }