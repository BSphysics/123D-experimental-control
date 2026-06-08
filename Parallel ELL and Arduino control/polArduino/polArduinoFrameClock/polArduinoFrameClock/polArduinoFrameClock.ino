String InBytes;

const int FRAME_PIN = 2;   // MUST be interrupt-capable pin (D2 = INT0)
const int DO12 = 12;

volatile bool frameEvent = false;

void frameISR() {
  frameEvent = true;
}

void setup() {
  Serial.begin(9600);

  pinMode(FRAME_PIN, INPUT);
  pinMode(DO12, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);

  // Trigger interrupt on FALLING edge (HIGH → LOW = frame done)
  attachInterrupt(digitalPinToInterrupt(FRAME_PIN), frameISR, FALLING);

  Serial.println("FW:FrameSync_INT_v1_READY");
}

void loop() {

  // =========================
  // SERIAL COMMAND HANDLER
  // =========================
  if (Serial.available() > 0) {
    InBytes = Serial.readStringUntil('\n');

    if (InBytes == "on") {
      digitalWrite(DO12, HIGH);
      digitalWrite(LED_BUILTIN, HIGH);
      Serial.println("TRIGGERED");
    }

    if (InBytes == "off") {
      digitalWrite(DO12, LOW);
      digitalWrite(LED_BUILTIN, LOW);
      Serial.println("ARMED");
    }

    if (InBytes == "ping") {
      Serial.println("pong");
    }
  }

  // =========================
  // FRAME EVENT HANDLER
  // =========================
  if (frameEvent) {
    Serial.println("FRAME_DONE");
    frameEvent = false;
  }
}
