// FrameSync_INT_v1 + power-meter readout
// ---------------------------------------------------------------------------
// Frame-clock synchronisation (on/off/ping/FRAME_DONE via D2 interrupt) is
// unchanged. The "pol" command from the original polArduino.ino is restored
// verbatim: read A0, average 10 samples, scale 0-1023 counts to 0-10 V. A0 is
// free (frame sync uses D2/D12/D13 only), and analogRead does not disable
// interrupts, so a frame event during a pol read is still captured and the
// FRAME_DONE is emitted on the next loop pass.
// ---------------------------------------------------------------------------

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
  // Trigger interrupt on FALLING edge (HIGH -> LOW = frame done)
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

    // ----- restored power-meter readout (from polArduino.ino) -----
    if (InBytes == "pol") {
      // Average 10 reads on A0; original 0-10 V scaling preserved so values
      // stay comparable with previous polarisation measurements.
      int average = 0;
      for (int i = 0; i < 10; i++) {
        average = average + analogRead(A0);
      }
      average = average / 10;

      float voltage = average * (10.0 / 1023.0);

      Serial.println(voltage);
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
