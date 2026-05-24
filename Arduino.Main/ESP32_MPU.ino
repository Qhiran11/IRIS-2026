// #include <MPU6050_tockn.h>
// #include <Wire.h>

// MPU6050 mpu6050(Wire);
// long timer = 0;

// // Gunakan int16_t agar ukuran datanya pasti 2 byte
// int16_t x = 0; 

// void setup() {
//   Serial.begin(115200);

//   // Inisialisasi Serial2 (TX2: Pin 17, RX2: Pin 16)
//   Serial2.begin(115200, SERIAL_8N1, 16, 17);
  
//   // Inisialisasi I2C untuk ESP32
//   // Wire.begin(22, 23);
//   Wire.begin(21, 22);
  
//   mpu6050.begin();
  
//   Serial.println("Memulai Kalibrasi... Jangan gerakkan sensor!");
//   mpu6050.calcGyroOffsets(true); 
//   Serial.println("Kalibrasi Selesai!");
// }

// void loop() {
//   mpu6050.update();

//   if(millis() - timer > 10){
//     x = mpu6050.getAngleX();
    
//     // Output ke Serial Monitor (Bentuk teks agar bisa dibaca manusia)
//     Serial.print("Sudut Akhir x: ");
//     Serial.println(x);
    
//     // Output ke Serial2 (Bentuk Binary - 2 Byte)
//     // Mengambil alamat memori dari x, lalu mengirim 2 byte datanya
//     Serial2.write((uint8_t*)&x, sizeof(x)); 
    
//     timer = millis();
//   }
// } 