#include <Servo.h>

#define echoPin 10
#define trigPin 9
const int buzzer = 8;
const int servoPin = 6;

// Servo positions
const int SERVO_LOCKED_POS = 0;    // Position when door is locked
const int SERVO_HALFLOCKED_POS = 90;
const int SERVO_UNLOCKED_POS = 180; // Default/unlocked position
const int SERVO_IDLE_AWAY_POS = 180; // Position when no object is near and door is unlocked

// Distance thresholds
const int NEAR_DISTANCE = 30;     // Near distance threshold (cm)
const int MID_DISTANCE = 60;      // Mid distance threshold (cm)
const int FAR_DISTANCE = 100;     // Far distance threshold (cm)

// Buzzer frequencies for different distances
const int NEAR_FREQ = 1000;
const int MID_FREQ = 500;
const int FAR_FREQ = 200;

long duration;
int distance;
Servo myServo;
boolean systemActive = true;  // System starts in active state

void setup() {
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(buzzer, OUTPUT);

  myServo.attach(servoPin);
  myServo.write(SERVO_UNLOCKED_POS);

  Serial.begin(9600);
  Serial.println("Smart Door Security System Initialized");
  Serial.println("System current state: ACTIVE");
}

void loop() {
  // Check for serial commands
  if (Serial.available() > 0) {
    char command = Serial.read();
    if (command == 'D') {  // Deactivate
      systemActive = false;
      myServo.write(SERVO_UNLOCKED_POS);
      noTone(buzzer);
      Serial.println("System DEACTIVATED - Face detected");
    }
    else if (command == 'A') {  // Activate
      systemActive = true;
      Serial.println("System ACTIVATED - No face detected");
    }
  }

  // Only process distance and activate servo/buzzer if system is active
  if (systemActive) {
    // Measure distance
    digitalWrite(trigPin, LOW);
    delayMicroseconds(2);
    digitalWrite(trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(trigPin, LOW);

    duration = pulseIn(echoPin, HIGH);
    distance = duration * 0.034 / 2;

    // Debug distance (uncomment if needed)
    // Serial.print("Distance: ");
    // Serial.print(distance);
    // Serial.println(" cm");

    // Handle different distance ranges with variable buzzer frequencies
    if (distance <= NEAR_DISTANCE) {
      tone(buzzer, NEAR_FREQ, 100);
      myServo.write(SERVO_LOCKED_POS);
      Serial.println("Object very close - High frequency alert");
    }
    else if (distance <= MID_DISTANCE) {
      tone(buzzer, MID_FREQ, 100);
      myServo.write(SERVO_HALFLOCKED_POS);
      Serial.println("Object at medium range - Medium frequency alert");
    }
    else if (distance <= FAR_DISTANCE) {
      tone(buzzer, FAR_FREQ, 100);
      myServo.write(SERVO_UNLOCKED_POS);
      Serial.println("Object at far range - Low frequency alert");
    }
    else {
      noTone(buzzer);
      myServo.write(SERVO_IDLE_AWAY_POS);
    }
  }

  delay(100);  // Small delay for stability
}