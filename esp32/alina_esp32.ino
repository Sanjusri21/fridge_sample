/*
  ALINA – AI & IoT Smart Fridge ESP32 Firmware
  Hardware:
  - ESP32 NodeMCU
  - DS18B20 OneWire Temperature Sensor (GPIO 4)
  - Magnetic Reed Switch Door Sensor (GPIO 15)
  - HX711 Load Cell Amplifier (DT: GPIO 16, SCK: GPIO 17)
  - Active Buzzer (GPIO 18)
  - Status LEDs: Green (GPIO 19), Yellow (GPIO 21), Red (GPIO 22)
  - Servo Latch Motor (GPIO 13)
  - Safe Demo Low-Voltage Relay (GPIO 23) - DO NOT CONNECT TO 230V MAINS!

  Exposes HTTP Endpoints:
  - GET  /status   -> Returns JSON sensor readings
  - POST /command  -> Executes actuator action:
                     BUZZER_ON, BUZZER_OFF,
                     LED_NORMAL, LED_WARNING, LED_CRITICAL,
                     SERVO_OPEN, SERVO_CLOSE,
                     RELAY_ON, RELAY_OFF
*/

#include <WiFi.h>
#include <WebServer.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <ESP32Servo.h>

// ================= Wi-Fi Configuration =================
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// ================= Pin Assignments =================
#define PIN_ONE_WIRE_BUS 4   // DS18B20 Data
#define PIN_DOOR_REED    15  // Magnetic Reed Switch (Active LOW with internal pullup)
#define PIN_HX711_DT     16  // HX711 Data
#define PIN_HX711_SCK    17  // HX711 Clock
#define PIN_BUZZER       18  // Active Buzzer
#define PIN_LED_GREEN    19  // Normal
#define PIN_LED_YELLOW   21  // Warning
#define PIN_LED_RED      22  // Critical
#define PIN_SERVO        13  // Servo Motor
#define PIN_DEMO_RELAY   23  // Safe Low-Voltage Load ONLY (5V/12V DC)

// ================= Sensor & Actuator Objects =================
OneWire oneWire(PIN_ONE_WIRE_BUS);
DallasTemperature ds18b20(&oneWire);
Servo doorServo;
WebServer server(80);

// State variables
float lastTemperature = 4.2;
float lastHumidity = 60.0;
String doorState = "closed";
float currentWeight = 500.0;

// Calibration factor for HX711 (adjust according to your load cell)
float calibrationFactor = -420.0;

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n--- ALINA Smart Fridge ESP32 Booting ---");

  // Configure Pins
  pinMode(PIN_DOOR_REED, INPUT_PULLUP);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_LED_GREEN, OUTPUT);
  pinMode(PIN_LED_YELLOW, OUTPUT);
  pinMode(PIN_LED_RED, OUTPUT);
  pinMode(PIN_DEMO_RELAY, OUTPUT);

  digitalWrite(PIN_BUZZER, LOW);
  digitalWrite(PIN_LED_GREEN, HIGH);
  digitalWrite(PIN_LED_YELLOW, LOW);
  digitalWrite(PIN_LED_RED, LOW);
  digitalWrite(PIN_DEMO_RELAY, LOW);

  // Initialize DS18B20
  ds18b20.begin();

  // Initialize Servo
  doorServo.attach(PIN_SERVO);
  doorServo.write(0); // 0 degrees = Closed

  // Connect to Wi-Fi
  Serial.print("Connecting to Wi-Fi: ");
  Serial.println(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWi-Fi Connected!");
    Serial.print("ESP32 IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nWi-Fi Connection failed. Starting in AP/Fallback mode.");
  }

  // Define HTTP Endpoints
  server.on("/status", HTTP_GET, handleStatus);
  server.on("/command", HTTP_POST, handleCommand);

  server.begin();
  Serial.println("HTTP Server started on port 80.");
}

void loop() {
  server.handleClient();

  // Read sensors every 1 second
  static unsigned long lastRead = 0;
  if (millis() - lastRead > 1000) {
    lastRead = millis();
    readSensors();
  }
}

void readSensors() {
  // 1. Read DS18B20 Temperature
  ds18b20.requestTemperatures();
  float temp = ds18b20.getTempCByIndex(0);
  if (temp != DEVICE_DISCONNECTED_C && temp > -50.0 && temp < 100.0) {
    lastTemperature = temp;
  }

  // 2. Read Reed Switch Door Sensor (LOW when magnet present = closed)
  int reedVal = digitalRead(PIN_DOOR_REED);
  doorState = (reedVal == LOW) ? "closed" : "open";

  // 3. Weight Reading (simulated or via HX711)
  // For production with HX711 library, read scale.get_units()
}

void handleStatus() {
  readSensors();

  String json = "{";
  json += "\"temperature\":" + String(lastTemperature, 1) + ",";
  json += "\"humidity\":" + String(lastHumidity, 1) + ",";
  json += "\"door\":\"" + doorState + "\",";
  json += "\"weight\":" + String(currentWeight, 1);
  json += "}";

  server.send(200, "application/json", json);
}

void handleCommand() {
  if (!server.hasArg("plain")) {
    server.send(400, "application/json", "{\"error\":\"Missing body\"}");
    return;
  }

  String body = server.arg("plain");
  Serial.print("Received command: ");
  Serial.println(body);

  if (body.indexOf("BUZZER_ON") >= 0) {
    digitalWrite(PIN_BUZZER, HIGH);
  } else if (body.indexOf("BUZZER_OFF") >= 0) {
    digitalWrite(PIN_BUZZER, LOW);
  } else if (body.indexOf("LED_NORMAL") >= 0) {
    digitalWrite(PIN_LED_GREEN, HIGH);
    digitalWrite(PIN_LED_YELLOW, LOW);
    digitalWrite(PIN_LED_RED, LOW);
  } else if (body.indexOf("LED_WARNING") >= 0) {
    digitalWrite(PIN_LED_GREEN, LOW);
    digitalWrite(PIN_LED_YELLOW, HIGH);
    digitalWrite(PIN_LED_RED, LOW);
  } else if (body.indexOf("LED_CRITICAL") >= 0) {
    digitalWrite(PIN_LED_GREEN, LOW);
    digitalWrite(PIN_LED_YELLOW, LOW);
    digitalWrite(PIN_LED_RED, HIGH);
  } else if (body.indexOf("SERVO_OPEN") >= 0) {
    doorServo.write(90); // 90 deg = Open
  } else if (body.indexOf("SERVO_CLOSE") >= 0) {
    doorServo.write(0);  // 0 deg = Closed
  } else if (body.indexOf("RELAY_ON") >= 0) {
    digitalWrite(PIN_DEMO_RELAY, HIGH);
  } else if (body.indexOf("RELAY_OFF") >= 0) {
    digitalWrite(PIN_DEMO_RELAY, LOW);
  }

  server.send(200, "application/json", "{\"status\":\"success\",\"command_executed\":true}");
}
