/*
  Ultrasonic Sensor Characterization 
  ---------------------------------------------------------
  Reads distance from HC-SR04 ultrasonic sensor and streams timestamped
  readings over Serial as CSV so a computer can log and analyze
  noise, accuracy, drift.

  Hardware:
  - Arduino Uno R3
  - HC-SR04 ultrasonic sensor

*/

const int TRIG_PIN = 6;
const int ECHO_PIN = 5;

unsigned long lastReadTime = 0;
const unsigned long READ_INTERVAL_MS = 100; // 10 readings/sec

void setup() {
  Serial.begin(9600);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  // CSV header for the log file
  Serial.println("millis,distance_cm");
}

float readDistanceCM() {
  // Send a 10us pulse to trigger a measurement
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  // Read how long the echo pin stayed high (round-trip time in microseconds)
  // timeout of 30000us (5m range) so it doesn't hang if no echo returns
  long duration = pulseIn(ECHO_PIN, HIGH, 30000);

  if (duration == 0) {
    return -1; // no echo received (out of range or bad reading)
  }

  // Speed of sound - 0.0343 cm/us, divide by 2 for round trip
  float distanceCM = (duration * 0.0343) / 2.0;
  return distanceCM;
}

void loop() {
  unsigned long now = millis();

  if (now - lastReadTime >= READ_INTERVAL_MS) {
    lastReadTime = now;

    float distance = readDistanceCM();

    // Stream CSV over serial: millis,distance_cm
    Serial.print(now);
    Serial.print(",");
    if (distance < 0) {
      Serial.println("NaN");
    } else {
      Serial.println(distance);
    }
  }
}
