#include "WiFiS3.h"
#include <WiFiUdp.h>
#include <Servo.h>

// --- Configuration ---
char ssid[] = "Note8";        
char pass[] = "Pas12345"; // Must be 8+ characters
unsigned int localPort = 5005;

WiFiUDP Udp;
Servo panServo;
Servo tiltServo;
char packetBuffer[255];

void setup() {
  Serial.begin(115200);
  while (!Serial);

  panServo.attach(9);
  tiltServo.attach(10);

  // Center servos initially
  panServo.write(90);
  tiltServo.write(90);

  Serial.println("\n--- Sentry Cannon: Starting WiFi ---");
  WiFi.end(); // Reset radio
  delay(1000);
  
  WiFi.begin(ssid, pass);

  // Loop 1: Wait for physical connection
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }

  // Loop 2: Wait for DHCP to assign a valid IP (Fixes 0.0.0.0)
  Serial.println("\nHandshake successful. Awaiting IP...");
  while (WiFi.localIP() == IPAddress(0,0,0,0)) {
    delay(500);
    Serial.print("?");
  }

  Serial.println("\n[SYSTEM ONLINE]");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
  
  Udp.begin(localPort);
}

void loop() {
  int packetSize = Udp.parsePacket();
  if (packetSize) {
    int len = Udp.read(packetBuffer, 255);
    if (len > 0) packetBuffer[len] = 0;

    String data = String(packetBuffer);
    int commaIndex = data.indexOf(',');
    
    if (commaIndex > 0) {
      // Parse +94, -83 format (toInt handles signs automatically)
      int rawPan = data.substring(0, commaIndex).toInt();
      int rawTilt = data.substring(commaIndex + 1).toInt();

      // Mapping: Assuming Python sends -90 to +90
      // Adjust these ranges if your Python logic uses different bounds
      int servoPan = map(rawPan, -90, 90, 0, 180);
      int servoTilt = map(rawTilt, -90, 90, 0, 180);

      panServo.write(constrain(servoPan, 0, 180));
      tiltServo.write(constrain(servoTilt, 0, 180));
      
      Serial.print("Input: "); Serial.print(data);
      Serial.print(" | Pan: "); Serial.print(servoPan);
      Serial.print(" | Tilt: "); Serial.println(servoTilt);
    }
  }
}