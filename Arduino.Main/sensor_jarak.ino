// // kiri 
// // const int trigPin = 42;  // Pin untuk Trigger
// // const int echoPin = 44; // Pin untuk Echo


// // // kanan 
// // const int trigPin = 40;  // Pin untuk Trigger
// // const int echoPin = 38; // Pin untuk Echo

// // belakang 
// // const int trigPin = 36;  // Pin untuk Trigger
// // const int echoPin = 34; // Pin untuk Echo

// // depan 
// // const int trigPin = 32;  // Pin untuk Trigger
// // const int echoPin = 30; // Pin untuk Echo


// const int pinT[4] = {42, 40, 36, 32};
// const int pinE[4] = {44, 38, 34, 30};

// void setup() {
//   Serial.begin(115200);
//   for (int i = 0; i < 4; i++) {
//     pinMode(pinT[i], OUTPUT);
//     pinMode(pinE[i], INPUT);
//   }
// }

// void loop() {
//   for (int i = 0; i < 4; i++) {
//     digitalWrite(pinT[i], LOW);
//     delayMicroseconds(2);
//     digitalWrite(pinT[i], HIGH);
//     delayMicroseconds(10);
//     digitalWrite(pinT[i], LOW);

//     // Timeout 25000us (25ms) agar cukup untuk jarak 4 meter (pp 8m)
//     long duration = pulseIn(pinE[i], HIGH, 25000); 

//     if (duration == 0) {
//       Serial.print("Jarak > 4m | ");
//     } else {
//       int distance = duration * 0.0343 / 2;
//       Serial.print(distance);
//       Serial.print("cm | ");
//     }
//   }
//   Serial.println();
// }