// arduino_20_motor_v4_non_blocking.ino (IRIS 2026 KRAI Standard)
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

int lajuawal = 0;

Adafruit_PWMServoDriver pca = Adafruit_PWMServoDriver(0x40);

// Pin M0-M5: 2 PW, 4 DC
const int PIN_ENB[]   = {30, 26, 24, 28, 32, 34};
const int PIN_PWM_R[] = {7,  11, 13,  9,  3,  5};
const int PIN_PWM_L[] = {6,  10, 12,  8,  2,  4};

// Pin Relay PW
const int relayPin1 = 10; // kiri (Naik)
const int relayPin2 = 11; // kiri (Turun)
const int relayPin3 = 6;  // kanan (Naik)
const int relayPin4 = 7;  // kanan (Turun)

// Pin Relay Tambahan
const int relayTambahan1 = 40; 
const int relayTambahan2 = 42;

// Pin Stepper
const int STP1_ENA = 37; const int STP1_DIR = 39; const int STP1_PULL = 41;
const int STP2_ENA = 43; const int STP2_DIR = 47; const int STP2_PULL = 49;

// --- STEPPER TIMING ---
unsigned long lastStepMicros1 = 0;
unsigned long lastStepMicros2 = 0;
const unsigned long stepInterval = 400; // Microseconds
bool pullState1 = false;
bool pullState2 = false;

// --- STATE TRACKER PCA & RAMPING ---
int lastPcaVal[5] = {0, 0, 0, 0, 0};
int pcaEnPins[5] = {22, 23, 27, 25, 31};
int pcaChRight[5] = {6, 12, 11, 14, 2};
int pcaChLeft[5]  = {7, 13, 10, 15, 3};

// UBAH: Ukuran array menjadi 20
int16_t targetSpeeds[20] = {0}; 
float currentSpeeds[20] = {0.0};
const float RAMP_TIME_MS = 200.0; 
const float MAX_SPEED_DELTA = 255.0; 
const float ACCEL_RATE = MAX_SPEED_DELTA / RAMP_TIME_MS; 

unsigned long lastRampTime = 0;
unsigned long lastSerialTime = 0;
unsigned long lastTelemetryTime = 0;

const int limit1 = 46;
const int limit2 = 45;

// UBAH: Perbesar ukuran rxBuffer minimal 45 (40 data byte + 1 checksum + 2 header + 2 end)
byte rxBuffer[50];
int rxIndex = 0;
enum SerialState { HEADER1, HEADER2, DATA, CHECKSUM, END1, END2 };
SerialState rxState = HEADER1;

// Variabel Stepper & Limit
long remainingSteps = 0;
bool readyToAccept = true; 
int arah_awal_0 = 0; // 1 (Kanan), -1 (Kiri), 0 (Berhenti)
int arah_awal_1 = 0; 

void setup() {
  SerialUSB.begin(115200);

  // Roda DC adalah index 2 sampai 5 (M2-M5)
  for (int i = 2; i < 6; i++) {
    pinMode(PIN_ENB[i], OUTPUT); digitalWrite(PIN_ENB[i], HIGH);
    pinMode(PIN_PWM_R[i], OUTPUT); pinMode(PIN_PWM_L[i], OUTPUT);
  }

  // Setup Relay PW & Tambahan
  pinMode(relayPin1, OUTPUT);
  pinMode(relayPin2, OUTPUT);
  pinMode(relayPin3, OUTPUT);
  pinMode(relayPin4, OUTPUT);
  pinMode(relayTambahan1, OUTPUT);
  pinMode(relayTambahan2, OUTPUT);

  // Inisialisasi Relay OFF (Active Low -> HIGH)
  digitalWrite(relayPin1, HIGH);
  digitalWrite(relayPin2, HIGH);
  digitalWrite(relayPin3, HIGH);
  digitalWrite(relayPin4, HIGH);
  digitalWrite(relayTambahan1, HIGH);
  digitalWrite(relayTambahan2, HIGH);

  pinMode(STP1_ENA, OUTPUT); digitalWrite(STP1_ENA, LOW); 
  pinMode(STP1_DIR, OUTPUT); pinMode(STP1_PULL, OUTPUT);
  pinMode(STP2_ENA, OUTPUT); digitalWrite(STP2_ENA, LOW); 
  pinMode(STP2_DIR, OUTPUT); pinMode(STP2_PULL, OUTPUT);

  pinMode(limit1, INPUT_PULLUP);
  pinMode(limit2, INPUT_PULLUP);

  Wire.begin();
  pca.begin();
  pca.setPWMFreq(2000);
  for(int i = 0; i < 5; i++){
    pinMode(pcaEnPins[i], OUTPUT); digitalWrite(pcaEnPins[i], HIGH);
  }
}

void loop() {
  processSerial();

  if (millis() - lastSerialTime > 300) {
    // UBAH: Loop reset batasnya menjadi 20
    for (int i = 0; i < 20; i++) targetSpeeds[i] = 0;
  }

  applyRamping();
  updateMotors();
  updateSteppersNonBlocking();
  
  if (millis() - lastTelemetryTime >= 100) {
     sendTelemetry();
     lastTelemetryTime = millis();
  }
}

void updateSteppersNonBlocking() {
  unsigned long currentMicros = micros();
  // Catatan: Pastikan indeks ke-11 tetap yang ingin digunakan, atau sesuaikan jika mapping Python berubah
  int incomingData = targetSpeeds[11]; /// stepper

  if (incomingData != 0 && readyToAccept) {
    remainingSteps = incomingData; 
    readyToAccept = false; 
  } 
  else if (incomingData == 0) {
    readyToAccept = true;
  }

  if (remainingSteps != 0) {
    if (remainingSteps > 0) {
      digitalWrite(STP1_DIR, LOW);
      digitalWrite(STP2_DIR, HIGH);
    } else {
      digitalWrite(STP1_DIR, HIGH);
      digitalWrite(STP2_DIR, LOW);
    }

    if (currentMicros - lastStepMicros1 >= stepInterval) {
      lastStepMicros1 = currentMicros;
      pullState1 = !pullState1;
      
      digitalWrite(STP1_PULL, pullState1);
      digitalWrite(STP2_PULL, pullState1); 

      if (pullState1 == LOW) {
        if (remainingSteps > 0) remainingSteps--;
        else remainingSteps++;
      }
    }
  }
}

void processSerial() {
  while (SerialUSB.available()) {
    byte b = SerialUSB.read();
    switch (rxState) {
      case HEADER1: if (b == 0xAA) rxState = HEADER2; break;
      case HEADER2: if (b == 0x55) rxState = DATA; rxIndex = 0; break;
      
      // UBAH: 20 data * 2 byte = 40 byte. Checksum ada di indeks ke-40
      case DATA: rxBuffer[rxIndex++] = b; if (rxIndex >= 40) rxState = CHECKSUM; break;
      case CHECKSUM: rxBuffer[40] = b; rxState = END1; break;
      
      case END1: if (b == 0x0D) rxState = END2; else rxState = HEADER1; break;
      case END2:
        if (b == 0x0A) {
          byte calcXor = 0;
          // UBAH: Loop kalkulasi XOR sampai byte ke-40
          for (int i = 0; i < 40; i++) calcXor ^= rxBuffer[i];
          
          if (calcXor == rxBuffer[40]) {
             // UBAH: Konversi array memproses 20 data
             for(int i = 0; i < 20; i++) targetSpeeds[i] = rxBuffer[i*2] | (rxBuffer[(i*2)+1] << 8);
             lastSerialTime = millis();
          }
        }
        rxState = HEADER1; break;
    }
  }
}

void applyRamping() {
  unsigned long now = millis();
  unsigned long dt = now - lastRampTime;
  if (dt > 0) {
     float maxChange = ACCEL_RATE * dt; 
     // UBAH: Ramping diterapkan ke 20 array kecepatan
     for(int i = 0; i < 20; i++) {
         float diff = targetSpeeds[i] - currentSpeeds[i];
         if (abs(diff) <= maxChange) currentSpeeds[i] = targetSpeeds[i]; 
         else if (diff > 0) currentSpeeds[i] += maxChange; 
         else currentSpeeds[i] -= maxChange; 
     }
     lastRampTime = now;
  }
}

void updateMotors() {
  // Index 0 and 1 are relays, use targetSpeeds directly
  for (int i = 0; i < 2; i++) {
    setL298(i, targetSpeeds[i]);
  }
  // Index 2 to 5 are DC motors, use currentSpeeds
  for (int i = 2; i < 6; i++) {
    setL298(i, constrain((int)currentSpeeds[i], -255, 255));
  }

  // Control tambahan relay 1 (pin 40)
  if (targetSpeeds[13] == 1) {
    digitalWrite(relayTambahan1, LOW); // Active Low
  } else {
    digitalWrite(relayTambahan1, HIGH); // Inactive
  }

  // Control tambahan relay 2 (pin 42)
  if (targetSpeeds[14] == 1) {
    digitalWrite(relayTambahan2, LOW); // Active Low
  } else {
    digitalWrite(relayTambahan2, HIGH); // Inactive
  }
  
  for (int i = 0; i < 5; i++) {
    int rawSpeed = (int)currentSpeeds[i+6];
    int val = constrain((abs(rawSpeed) < 3 ? 0 : rawSpeed), -255, 255);
    int mappedVal = map(val, -255, 255, -4095, 4095);

    if (mappedVal != lastPcaVal[i]) {
      if (mappedVal > 0) { pca.setPWM(pcaChLeft[i], 0, 0); pca.setPWM(pcaChRight[i], 0, mappedVal); }
      else if (mappedVal < 0) { pca.setPWM(pcaChRight[i], 0, 0); pca.setPWM(pcaChLeft[i], 0, -mappedVal); }
      else { pca.setPWM(pcaChRight[i], 0, 0); pca.setPWM(pcaChLeft[i], 0, 0); }
      lastPcaVal[i] = mappedVal;
    }
  }
}

void setL298(int index, int pwm) {
  if (index == 0) {
    int direction = 0; // 0: stop, -1: naik, 1: turun
    if (pwm < 0) direction = -1;
    else if (pwm > 0) direction = 1;

    // Safety limit check
    if (targetSpeeds[12] == 0) { // pwLogic is 0, check limit
      if (digitalRead(limit1) == 0) { // limit switch is triggered (active low)
        // If trying to move in the same direction as arah_awal_0, stop!
        if ((direction < 0 && arah_awal_0 < 0) || (direction > 0 && arah_awal_0 > 0) || direction == 0) {
          direction = 0;
        }
      } else {
        // limit switch is not triggered, update arah_awal_0
        arah_awal_0 = direction;
      }
    }

    // Apply relay state for kanan
    if (direction < 0) { // Naik
      digitalWrite(relayPin4, HIGH); // Turn off Turun
      digitalWrite(relayPin3, LOW);  // Turn on Naik
    }
    else if (direction > 0) { // Turun
      digitalWrite(relayPin3, HIGH); // Turn off Naik
      digitalWrite(relayPin4, LOW);  // Turn on Turun
    }
    else { // Stop
      digitalWrite(relayPin3, HIGH); // Turn off Naik
      digitalWrite(relayPin4, HIGH); // Turn off Turun
    }
  }

  else if (index == 1) {
    int direction = 0; // 0: stop, -1: naik, 1: turun
    if (pwm < 0) direction = -1;
    else if (pwm > 0) direction = 1;

    // Safety limit check
    if (targetSpeeds[12] == 0) { // pwLogic is 0, check limit
      if (digitalRead(limit2) == 0) { // limit switch is triggered (active low)
        // If trying to move in the same direction as arah_awal_1, stop!
        if ((direction < 0 && arah_awal_1 < 0) || (direction > 0 && arah_awal_1 > 0) || direction == 0) {
          direction = 0;
        }
      } else {
        // limit switch is not triggered, update arah_awal_1
        arah_awal_1 = direction;
      }
    }

    // Apply relay state for kiri
    if (direction < 0) { // Naik
      digitalWrite(relayPin2, HIGH); // Turn off Turun
      digitalWrite(relayPin1, LOW);  // Turn on Naik
    }
    else if (direction > 0) { // Turun
      digitalWrite(relayPin1, HIGH); // Turn off Naik
      digitalWrite(relayPin2, LOW);  // Turn on Turun
    }
    else { // Stop
      digitalWrite(relayPin1, HIGH); // Turn off Naik
      digitalWrite(relayPin2, HIGH); // Turn off Turun
    }
  }
    
  else {
    if (pwm > 0) { analogWrite(PIN_PWM_R[index], pwm); analogWrite(PIN_PWM_L[index], 0); }
    else if (pwm < 0) { analogWrite(PIN_PWM_R[index], 0); analogWrite(PIN_PWM_L[index], -pwm); }
    else { analogWrite(PIN_PWM_R[index], 0); analogWrite(PIN_PWM_L[index], 0); }
  }
}

void sendTelemetry() {
   byte pkt[7] = {0xBB, 0x66, 0x0D, 0x04, 0x00, 0x0D, 0x0A}; 
   SerialUSB.write(pkt, 7);
}