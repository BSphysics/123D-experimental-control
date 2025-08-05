String (InBytes);

int DO12 = 12; // Declare which digital output will be used to create trigger pulse
int DI02 = 2; // Declare digital input (just used for testing)

// Note that on my arduino, DO12 is connected to DI02 by jumper wire (this was just for testing)

int OutBytes; //Serial commands send from Arduino

void setup() {
  // put your setup code here, to run once:
Serial.begin(9600);
Serial.flush();

pinMode(DO12, OUTPUT); // Set pin 12 as digital out
pinMode(DI02, INPUT); // Set pin 02 as digital in
pinMode(LED_BUILTIN,OUTPUT);
}

void loop() {
  // put your main code here, to run repeatedly:

if (Serial.available()>0){
  InBytes = Serial.readStringUntil('\n'); //Serial commands sent from python

  if (InBytes == "on"){
    digitalWrite(LED_BUILTIN,HIGH); //Use internal LED just for testing
    digitalWrite(DO12,HIGH);        // Physically set DO12 to high
    Serial.write("LED on \n");      // Send serial command back to Python (not really needed)
    
    OutBytes = digitalRead(DI02);   //Read voltage on DI02
    Serial.println(OutBytes);       //Send this voltage to python via serial comms
  }

  if (InBytes == "off"){
    digitalWrite(LED_BUILTIN,LOW);
    digitalWrite(DO12,LOW);
    Serial.write("Waveplates ready \n");
    
    OutBytes = digitalRead(DI02);
    Serial.println(OutBytes);
  }

  if (InBytes == "pol"){
    //int sensorValue = analogRead(A0);
    // Convert the analog reading (which goes from 0 - 1023) to a voltage (0 - 2 V):
    //float voltage = sensorValue * (2.0 / 1023.0);

    int average = 0;
    for (int i=0; i < 10; i++) {
     average = average + analogRead(A0);
       }
    average = average/10;  

    float voltage = average * (2.0 / 1023.0);
    
    Serial.println(voltage);
  }
}
}
