#include <Servo.h>

#define echoPin 10
#define trigPin 9
const int buzzer = 8;
const int servoPin = 6;

// Servo positions
const int SERVO_LOCKED_POS = 0;    // Position when door is locked
const int SERVO_UNLOCKED_POS = 90; // Default/unlocked position
const int SERVO_IDLE_AWAY_POS = 180; // Position when no object is near and door is unlocked

long duration;
int distance;
Servo myServo;
boolean doorLocked = false; // State variable to track if the door is locked

void setup() {
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(buzzer, OUTPUT);

  myServo.attach(servoPin);
  myServo.write(SERVO_UNLOCKED_POS); // Start with door unlocked

  Serial.begin(9600); // Baud rate for communication
  Serial.println("Smart Door Lock System Initialized");
  Serial.println("Door current state: UNLOCKED");
}

void loop() {
  // --- Ultrasonic Sensor Reading ---
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  duration = pulseIn(echoPin, HIGH);
  distance = duration * 0.034 / 2;

  // Serial.print("Jarak: "); // Optional: uncomment for debugging distance
  // Serial.print(distance);
  // Serial.print(" cm. Door Locked: ");
  // Serial.println(doorLocked ? "YES" : "NO");

  // --- Locking Logic ---
  if (distance <= 5 && !doorLocked) {
    Serial.println("Object detected close! Locking door.");
    for (int i = 0; i < 3; i++) {
      tone(buzzer, 1000); // Sharp beep for locking
      delay(100);
      noTone(buzzer);
      delay(100);
    }
    myServo.write(SERVO_LOCKED_POS);
    doorLocked = true;
    Serial.println("Door current state: LOCKED");
  }
  // --- Behavior when door is NOT locked ---
  else if (!doorLocked) {
    if (distance < 15) {
      myServo.write(SERVO_UNLOCKED_POS);
    } else {
      myServo.write(SERVO_IDLE_AWAY_POS);
      noTone(buzzer);
    }
  }

  // --- Serial Command Handling for Unlocking ---
  if (Serial.available() > 0) {
    char command = Serial.read();
    if (command == 'U' && doorLocked) {
      Serial.println("Unlock command ('U') received via Serial!");
      myServo.write(SERVO_UNLOCKED_POS);
      doorLocked = false;
      tone(buzzer, 1500, 200); // Higher pitch, short beep for unlock
      Serial.println("Door current state: UNLOCKED by face recognition");
    } else if (command == 'U' && !doorLocked) {
      Serial.println("Unlock command ('U') received, but door is already unlocked.");
    }
  }

  delay(200); // General delay for the loop
}