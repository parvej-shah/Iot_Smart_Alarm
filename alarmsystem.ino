// ================== ESP32 SMART ALARM SYSTEM ==================
// Features: Time-based alarm, Face detection, Room controls, Audio alerts
// Hardware: ESP32, MAX98357A I2S Amplifier, LEDs, Motor
// IoT: Blynk app integration, WiFi connectivity, NTP time sync
// ================================================================

#define BLYNK_TEMPLATE_ID "TMPL6PGhOeE2W"
#define BLYNK_TEMPLATE_NAME "Smart Alarm"
#define BLYNK_AUTH_TOKEN "mhwBpFwWvcRB3z9DexrimUS7YJay4lBU"

#include <WiFi.h>
#include <WiFiClient.h>
#include <BlynkSimpleEsp32.h>
#include <TimeLib.h>
#include <WiFiUdp.h>
#include <NTPClient.h>

// ================== NETWORK CONFIGURATION ==================
char ssid[] = "Chowdhury_Pathagar";  // WiFi network name
char pass[] = "azim@2025";           // WiFi password
/* Alternative WiFi (uncomment to use):
char ssid[] = "Realme GT Master Edition";
char pass[] = "@salam104dwd@"; */

// ================== HARDWARE PIN CONFIGURATION ==================
#define ledPin 18        // Alarm LED - blinks when alarm is active
#define statusLedPin 19  // Status LED - for notifications and updates
#define builtInLedPin 2  // Built-in LED (room light simulation)
#define fanMotorPin 4    // Motor pin (fan simulation)

// ================== SYSTEM VARIABLES ==================
// NTP and Time Management
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "pool.ntp.org", 6 * 3600, 60000); // BD timezone (UTC+6)

// Alarm Configuration
int alarmHour = -1;           // Set via Blynk app
int alarmMinute = -1;         // Set via Blynk app
bool alarmTriggered = false;
bool alarmHandledForCurrentTime = false;  // Prevent re-triggering for same time
int lastMinute = -1;

// Face Detection
bool faceDetected = false;
unsigned long lastFaceDetectionTime = 0;

// Room Control Status
bool roomLightOn = false;
bool fanRunning = false;

// LED Timing Control
unsigned long lastAlarmBlinkTime = 0;
bool alarmLedState = false;
const unsigned long alarmBlinkInterval = 500; // Blink every 500ms when alarm is active

// ================== FUNCTION DECLARATIONS ==================
// System Initialization
void initializeSystem();
bool connectToWiFi();
void initializeNTP();
bool connectToBlynk();

// Time and Alarm Management
void handleTimeUpdates();
void checkAlarmTrigger();
void handleAlarmLogic();
void printCurrentTime();
String formatTime(int hour, int minute);

// Connection Management
void handleReconnections();

// LED Control
void ledBlink(int times, int delayMs);
void statusLedBlink(int times, int delayMs);
void handleAlarmLedBlink();

// Room Controls
void turnOnRoomControls();
void turnOffRoomControls();

// ================== BLYNK CALLBACK FUNCTIONS ==================
BLYNK_WRITE(V0) {
  int value = param.asInt();
  Serial.print("Received command from Blynk - Status LED: ");
  Serial.println(value ? "ON" : "OFF");
  digitalWrite(statusLedPin, value);
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
    alarmHandledForCurrentTime = false; // Reset handling flag for new alarm
    
    // Reset V5 pin when setting new alarm
    Blynk.virtualWrite(V5, 0);
    Serial.println("🔄 [RESET] V5 pin reset to 0 for new alarm");
    
    // Send confirmation to app
    Blynk.virtualWrite(V2, "Alarm set for " + formatTime(alarmHour, alarmMinute));
  } else {
    Serial.println("No time selected!");
    alarmHour = -1;
    alarmMinute = -1;
    alarmHandledForCurrentTime = false; // Reset flag when alarm is cleared
    
    // Clear V5 pin when alarm is cleared
    Blynk.virtualWrite(V5, 0);
    Serial.println("🔄 [CLEAR] V5 pin cleared");
    
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
    // Send face detection message to Blynk app
    Blynk.virtualWrite(V2, "👤 Face Detected!");
    
    // Stop alarm if it's currently triggered
    if (alarmTriggered) {
      digitalWrite(ledPin, LOW);  // Turn off alarm LED
      turnOffRoomControls();      // Turn off room light, fan, and speaker
      Serial.println("🔕 Alarm stopped - Face detected!");
      Serial.println("💡 Room light OFF, 🌀 Fan OFF, 🔇 Speaker OFF");
      
      // Send stop signal to laptop
      Blynk.virtualWrite(V5, 0);  // Signal laptop to stop alarm sound
      
      Blynk.virtualWrite(V2, "🔕 Alarm stopped - Face detected! All controls OFF");
      alarmTriggered = false; // Reset for next alarm
      alarmHandledForCurrentTime = true; // Prevent re-triggering for this time
      Serial.println("Alarm handling completed for current time - will not trigger again until next alarm");
    }
    
    // Blink status LED to indicate face detection
    statusLedBlink(3, 150);
  } else {
    // Face no longer detected
    Blynk.virtualWrite(V2, "No face detected");
  }
}

BLYNK_CONNECTED() {
  Serial.println("Connected to Blynk server!");
  statusLedBlink(3, 200);  // Use status LED for connection indication
  Serial.println("Status LED blink sequence completed - Blynk ready!");
  
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
// This loop runs continuously and handles all system operations
void loop() {
  if (WiFi.status() == WL_CONNECTED && Blynk.connected()) {
    Blynk.run();              // Process Blynk communication
    handleTimeUpdates();      // Update system time
    handleAlarmLogic();       // Check and handle alarm triggers
    handleAlarmLedBlink();    // Manage alarm LED blinking
  } else {
    handleReconnections();    // Reconnect WiFi/Blynk if needed
  }
  
  delay(100); // Small delay for system responsiveness
}

// ================== SYSTEM INITIALIZATION FUNCTIONS ==================
void initializeSystem() {
  pinMode(ledPin, OUTPUT);        // Alarm LED
  pinMode(statusLedPin, OUTPUT);  // Status LED
  pinMode(builtInLedPin, OUTPUT); // Built-in LED (room light)
  pinMode(fanMotorPin, OUTPUT);   // Motor (fan)
  
  // Initialize all outputs to OFF
  digitalWrite(ledPin, LOW);
  digitalWrite(statusLedPin, LOW);
  digitalWrite(builtInLedPin, LOW);
  digitalWrite(fanMotorPin, LOW);
  
  roomLightOn = false;
  fanRunning = false;
  
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
  
  // Keep alarm running until face is detected (no auto-stop based on time)
  // The alarm LED blinking is handled by handleAlarmLedBlink()
  if (alarmTriggered && !faceDetected) {
    // Send periodic reminder every 30 seconds
    static unsigned long lastReminder = 0;
    if (millis() - lastReminder > 30000) { // 30 seconds
      Blynk.virtualWrite(V2, "🚨 ALARM ACTIVE - Show your face to stop!");
      Serial.println("🚨 Alarm still active - waiting for face detection");
      lastReminder = millis();
    }
  }
}

void checkAlarmTrigger() {
  if (alarmHour != -1 && alarmMinute != -1 && !alarmTriggered && !alarmHandledForCurrentTime) {
    int currentHour = timeClient.getHours();
    int currentMinute = timeClient.getMinutes();
    
    // Debug: Print current time vs alarm time every 30 seconds
    static unsigned long lastDebugPrint = 0;
    if (millis() - lastDebugPrint > 30000) { // Every 30 seconds
      Serial.printf("⏰ [DEBUG] Current: %02d:%02d, Alarm set: %02d:%02d\n", 
                    currentHour, currentMinute, alarmHour, alarmMinute);
      lastDebugPrint = millis();
    }
    
    if (currentHour == alarmHour && currentMinute == alarmMinute) {
      Serial.println("🎯 [ALARM] Time match detected - triggering alarm!");
      triggerAlarm();
    }
  }
  
  // Reset the flag when we move to a different minute
  int currentHour = timeClient.getHours();
  int currentMinute = timeClient.getMinutes();
  if (!(currentHour == alarmHour && currentMinute == alarmMinute)) {
    alarmHandledForCurrentTime = false;
  }
}

void triggerAlarm() {
  Serial.println("🚨 ALARM TRIGGERED! 🚨");
  // Don't set LED here - it will be handled by the blinking function
  
  // Turn on room controls (light, fan, and speaker)
  turnOnRoomControls();
  Serial.println("💡 Room light ON, 🌀 Fan ON, 🔊 Speaker ON");
  
  // Send alarm status to V5 for laptop monitoring
  Blynk.virtualWrite(V5, 1);  // Signal laptop that alarm is active
  
  // Send notification to Blynk app
  Blynk.logEvent("alarm_triggered", "Wake up! Show your face to stop the alarm!");
  Blynk.virtualWrite(V2, "🚨 ALARM TRIGGERED! Room controls & sound ON! Show your face to stop!");
  
  alarmTriggered = true;
  faceDetected = false; // Reset face detection status
  
  Serial.println("Alarm will continue until face is detected!");
  Serial.println("Alarm LED (Pin 18) will keep blinking until stopped");
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

// Status LED blink function (for notifications and updates)
void statusLedBlink(int times, int delayMs) {
  for (int i = 0; i < times; i++) {
    digitalWrite(statusLedPin, HIGH);
    delay(delayMs);
    digitalWrite(statusLedPin, LOW);
    if (i < times - 1) {
      delay(delayMs);
    }
  }
}

// Handle alarm LED continuous blinking when alarm is active
void handleAlarmLedBlink() {
  if (alarmTriggered) {
    unsigned long currentTime = millis();
    if (currentTime - lastAlarmBlinkTime >= alarmBlinkInterval) {
      alarmLedState = !alarmLedState;
      digitalWrite(ledPin, alarmLedState);
      lastAlarmBlinkTime = currentTime;
    }
  } else {
    // Make sure alarm LED is off when alarm is not active
    digitalWrite(ledPin, LOW);
    alarmLedState = false;
  }
}

// ================== ROOM CONTROL FUNCTIONS ==================
// Turn on room light and fan when alarm triggers (audio handled by laptop)
void turnOnRoomControls() {
  digitalWrite(builtInLedPin, HIGH);  // Turn on built-in LED (room light)
  digitalWrite(fanMotorPin, HIGH);    // Turn on motor (fan)
  roomLightOn = true;
  fanRunning = true;
  Serial.println("✅ Room controls activated - Light and Fan ON (Audio via laptop)");
}

// Turn off room light and fan when face is detected (audio handled by laptop)
void turnOffRoomControls() {
  digitalWrite(builtInLedPin, LOW);   // Turn off built-in LED (room light)
  digitalWrite(fanMotorPin, LOW);     // Turn off motor (fan)
  roomLightOn = false;
  fanRunning = false;
  Serial.println("❌ Room controls deactivated - Light and Fan OFF (Audio via laptop)");
}

// ================== END OF PROGRAM ==================
// All audio functionality handled by laptop Python script
// ESP32 handles: LED control, room controls, Blynk communication
