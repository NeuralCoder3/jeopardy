void setup() {
  Serial.begin(9600);
}

void loop() {
  float voltages[4];
  for (int i = 0; i < 4; i++) {
    int sensorValue = analogRead(A0 + i); 
    float value = sensorValue * (5.0 / 1023.0);
    if(value >= 2.5) {
      Serial.println(i);
    }
  }
}