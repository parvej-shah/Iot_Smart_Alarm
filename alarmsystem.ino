#define BLYNK_TEMPLATE_ID "TMPL6PGhOeE2W"
#define BLYNK_TEMPLATE_NAME "Smart Alarm"
#define BLYNK_AUTH_TOKEN "mhwBpFwWvcRB3z9DexrimUS7YJay4lBU"

#include <WiFi.h>
#include <WiFiClient.h>
#include <BlynkSimpleEsp32.h>
#include <TimeLib.h>
#include <WiFiUdp.h>
#include <NTPClient.h>

// Configuration

char ssid[] = "Chowdhury_Pathagar";
char pass[] = "azim@2025";
/* char ssid[] = "Realme GT Master Edition";
char pass[] = "@salam104dwd@"; */
#define ledPin 18

// NTP and Alarm variables
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "pool.ntp.org", 6 * 3600, 60000); // BD timezone (UTC+6)
int alarmHour = -1;
int alarmMinute = -1;
bool alarmTriggered = false;
int lastMinute = -1;
bool faceDetected = false;
unsigned long lastFaceDetectionTime = 0;

// Function Declarations
void initializeSystem();
bool connectToWiFi();
void initializeNTP();
bool connectToBlynk();
void handleTimeUpdates();
void checkAlarmTrigger();
void handleAlarmLogic();
void handleReconnections();
void ledBlink(int times, int delayMs);
void printCurrentTime();
String formatTime(int hour, int minute);

// ================== BLYNK CALLBACK FUNCTIONS ==================
BLYNK_WRITE(V0) {
  int value = param.asInt();
  Serial.print("Received command from Blynk - LED: ");
  Serial.println(value ? "ON" : "OFF");
  digitalWrite(ledPin, value);
}

BLYNK_WRITE(V1) {
  TimeInputParam t(param);
  if (t.hasStartTime()) {
    alarmHour = t.getStartHour();
    alarmMinute = t.getStartMinute();
    Serial.print("Alarm set for: ");
    Serial.print(formatTime(alarmHour, alarmMinute));
    Serial.println();
    alarmTriggered = false; // Reset trigger
    
    // Send confirmation to app
    Blynk.virtualWrite(V2, "Alarm set for " + formatTime(alarmHour, alarmMinute));
  } else {
    Serial.println("No time selected!");
    alarmHour = -1;
    alarmMinute = -1;
    Blynk.virtualWrite(V2, "Alarm cleared");
  }
}

BLYNK_WRITE(V4) {
  int value = param.asInt();
  faceDetected = (value == 1);
  lastFaceDetectionTime = millis();
  
  Serial.print("Face detection status: ");
  Serial.println(faceDetected ? "DETECTED" : "NOT DETECTED");
  
  if (faceDetected) {
    Serial.println("👤 Face detected by camera system!");
    // Optional: Blink LED to indicate face detection
    ledBlink(2, 100);
  }
}

BLYNK_CONNECTED() {
  Serial.println("Connected to Blynk server!");
  ledBlink(3, 200);
  Serial.println("LED blink sequence completed - Blynk ready!");
  
  // Sync time and send current time to app
  timeClient.update();
  String currentTime = formatTime(timeClient.getHours(), timeClient.getMinutes());
  Blynk.virtualWrite(V3, currentTime);
}

// ================== SETUP FUNCTION ==================
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n=== Smart Alarm System Starting ===");
  
  initializeSystem();
}

// ================== MAIN LOOP ==================
void loop() {
  if (WiFi.status() == WL_CONNECTED && Blynk.connected()) {
    Blynk.run();
    handleTimeUpdates();
    handleAlarmLogic();
  } else {
    handleReconnections();
  }
  
  delay(1000); // Check every second for better alarm accuracy
}

// ================== SYSTEM INITIALIZATION FUNCTIONS ==================
void initializeSystem() {
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, LOW);
  
  if (connectToWiFi()) {
    initializeNTP();
    connectToBlynk();
    Serial.println("=== System Ready ===");
  } else {
    Serial.println("=== System initialization failed! ===");
  }
}

bool connectToWiFi() {
  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, pass);
  
  int wifi_attempts = 0;
  while (WiFi.status() != WL_CONNECTED && wifi_attempts < 20) {
    delay(500);
    Serial.print(".");
    wifi_attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    Serial.print("Signal strength (RSSI): ");
    Serial.println(WiFi.RSSI());
    return true;
  } else {
    Serial.println("\nFailed to connect to WiFi!");
    Serial.print("WiFi status: ");
    Serial.println(WiFi.status());
    return false;
  }
}

void initializeNTP() {
  timeClient.begin();
  Serial.println("NTP client started");
  
  // Get initial time
  timeClient.update();
  Serial.print("Initial time: ");
  printCurrentTime();
}

bool connectToBlynk() {
  Blynk.config(BLYNK_AUTH_TOKEN);
  return Blynk.connect();
}

// ================== TIME MANAGEMENT FUNCTIONS ==================
void handleTimeUpdates() {
  timeClient.update();
  
  int currentMinute = timeClient.getMinutes();
  
  // Send current time to app every minute
  if (currentMinute != lastMinute) {
    String currentTime = formatTime(timeClient.getHours(), currentMinute);
    Blynk.virtualWrite(V3, currentTime);
    printCurrentTime();
    lastMinute = currentMinute;
  }
}

void printCurrentTime() {
  int hour = timeClient.getHours();
  int minute = timeClient.getMinutes();
  Serial.print("Current time: ");
  Serial.println(formatTime(hour, minute));
}

String formatTime(int hour, int minute) {
  return String(hour) + ":" + (minute < 10 ? "0" : "") + String(minute);
}

// ================== ALARM MANAGEMENT FUNCTIONS ==================
void handleAlarmLogic() {
  checkAlarmTrigger();
  
  // Auto-turn off LED after alarm minute passes
  if (alarmTriggered) {
    int currentHour = timeClient.getHours();
    int currentMinute = timeClient.getMinutes();
    
    if (!(currentHour == alarmHour && currentMinute == alarmMinute)) {
      digitalWrite(ledPin, LOW);
      Serial.println("Alarm auto-stopped");
      Blynk.virtualWrite(V2, "Alarm stopped");
      alarmTriggered = false; // Reset for next alarm
    }
  }
}

void checkAlarmTrigger() {
  if (alarmHour != -1 && alarmMinute != -1 && !alarmTriggered) {
    int currentHour = timeClient.getHours();
    int currentMinute = timeClient.getMinutes();
    
    if (currentHour == alarmHour && currentMinute == alarmMinute) {
      triggerAlarm();
    }
  }
}

void triggerAlarm() {
  Serial.println("🚨 ALARM TRIGGERED! 🚨");
  digitalWrite(ledPin, HIGH);
  
  // Send notification to Blynk app
  Blynk.logEvent("alarm_triggered", "Wake up! Alarm time reached!");
  Blynk.virtualWrite(V2, "🚨 ALARM TRIGGERED! 🚨");
  
  alarmTriggered = true;
}

// ================== CONNECTION MANAGEMENT FUNCTIONS ==================
void handleReconnections() {
  Serial.println("Connection lost. Attempting to reconnect...");
  
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Reconnecting to WiFi...");
    WiFi.begin(ssid, pass);
  }
  
  if (!Blynk.connected() && WiFi.status() == WL_CONNECTED) {
    Serial.println("Reconnecting to Blynk...");
    Blynk.connect();
  }
  
  delay(5000);
}

// ================== UTILITY FUNCTIONS ==================
void ledBlink(int times, int delayMs) {
  for (int i = 0; i < times; i++) {
    digitalWrite(ledPin, HIGH);
    delay(delayMs);
    digitalWrite(ledPin, LOW);
    if (i < times - 1) {
      delay(delayMs);
    }
  }
}
