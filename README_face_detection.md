# ESP32 Face Detection Communication Guide

## Current Implementation: Blynk Method ✅

### How it works:
1. **Python script** detects faces from ESP32-CAM stream
2. **Sends status** to Blynk cloud via HTTP API  
3. **ESP32 receives** the status through Blynk virtual pin V4
4. **ESP32 responds** by printing to serial and optionally blinking LED

### Files Updated:
- `esp32_face_detect.py` - Enhanced with Blynk communication
- `alarmsystem.ino` - Added V4 pin handler for face detection

### Virtual Pin Assignment:
- **V0**: LED control (existing)
- **V1**: Alarm time setting (existing) 
- **V2**: Status messages (existing)
- **V3**: Current time display (existing)
- **V4**: Face detection status (NEW)

## Usage Instructions:

### 1. Upload Arduino Code
Upload the updated `alarmsystem.ino` to your ESP32

### 2. Test Communication
```bash
python test_blynk_communication.py
```

### 3. Run Face Detection
```bash
python esp32_face_detect.py
```

### 4. Monitor ESP32 Serial Output
You should see messages like:
```
Face detection status: DETECTED
👤 Face detected by camera system!
```

## Customization Options:

### Change Detection Sensitivity:
In `esp32_face_detect.py`, modify:
```python
NO_FACE_TIMEOUT = 5  # Seconds before sending "no face" signal
```

### Add Actions on Face Detection:
In `alarmsystem.ino`, in the `BLYNK_WRITE(V4)` function:
```cpp
if (faceDetected) {
    // Add your custom actions here:
    // - Turn on specific LEDs
    // - Send notifications
    // - Trigger other sensors
    // - Log to SD card
}
```

## Alternative Methods (Advanced):

### Method 2: Direct HTTP
- ESP32 runs web server
- Python sends HTTP requests directly
- Requires more ESP32 programming

### Method 3: MQTT
- Both devices connect to MQTT broker  
- Real-time messaging
- Requires MQTT broker setup

## Troubleshooting:

### If Blynk communication fails:
1. Check internet connection
2. Verify Blynk token is correct
3. Ensure ESP32 is connected to Blynk
4. Check Blynk server status

### If face detection is slow:
1. Reduce camera resolution
2. Adjust detection parameters
3. Use faster computer/Pi

### If ESP32-CAM stream fails:
1. Check ESP32-CAM IP address
2. Verify stream endpoint (:81/stream)
3. Test stream in browser first
