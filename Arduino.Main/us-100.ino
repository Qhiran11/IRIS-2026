// const int trigPin = 10;
// const int echoPin = 11;

// long durasi;
// float jarakCM;

// void setup() {
//   pinMode(trigPin, OUTPUT); 
//   pinMode(echoPin, INPUT);  
//   Serial.begin(9600); // Serial Monitor
//   Serial.println("US-100 Mode Trigger/Echo Siap.");
// }

// void loop() {
//   // Bersihkan pin trigger
//   digitalWrite(trigPin, LOW);
//   delayMicroseconds(2);
  
//   // Aktifkan trigger selama 10 mikrodetik
//   digitalWrite(trigPin, HIGH);
//   delayMicroseconds(10);
//   digitalWrite(trigPin, LOW);
  
//   // Baca durasi pantulan pulsa (dalam mikrodetik)
//   durasi = pulseIn(echoPin, HIGH);
  
//   // Menghitung jarak (Kecepatan suara = 0.034 cm/µs)
//   jarakCM = (durasi * 0.034) / 2;
  
//   // Tampilkan hasil ke Serial Monitor
//   Serial.print("Jarak: ");
//   Serial.print(jarakCM);
//   Serial.println(" cm");
  
//   delay(500); // Jeda antar pembacaan
// }