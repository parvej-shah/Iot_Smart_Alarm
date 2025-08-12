import cv2
import requests
import time
import numpy as np
import threading
import pygame

# ======== CONFIG ========
ESP32_IP = "192.168.0.165"
STREAM_URL = f"http://{ESP32_IP}:81/stream"
CAPTURE_URL = f"http://{ESP32_IP}/capture"

# Blynk settings
BLYNK_TOKEN = "mhwBpFwWvcRB3z9DexrimUS7YJay4lBU"
BLYNK_SERVER = "blynk.cloud"

# Test mode - set to True to focus on audio monitoring without camera
AUDIO_ONLY_MODE = False

# Face detection settings
FACE_DETECTED_PIN = "V4"  # Virtual pin to send face detection status
ALARM_TIME_PIN = "V5"     # Virtual pin to check alarm status from ESP32
NO_FACE_TIMEOUT = 5  # Seconds to wait before sending "no face" signal

# Audio settings
ALARM_AUDIO_FILE = "alarm.wav"  # Audio file to play during alarm
audio_playing = False
audio_thread = None
alarm_sound = None

# State tracking for better synchronization
last_alarm_status = None  # Track previous alarm state
last_status_check_time = 0
STATUS_CHECK_INTERVAL = 1  # Check status every 1 second for better sync

# Camera health tracking
camera_working = False
camera_last_test = 0
CAMERA_TEST_INTERVAL = 60  # Test camera every 60 seconds

# Load Haar Cascade for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Variables for face detection tracking
last_face_detected_time = 0
face_status_sent = False

def test_camera_health():
    """Test if camera is working and can capture frames"""
    global camera_working, camera_last_test
    
    current_time = time.time()
    if current_time - camera_last_test < CAMERA_TEST_INTERVAL:
        return camera_working
    
    camera_last_test = current_time
    print("[CAMERA] Testing camera health...")
    
    try:
        # Try capture first
        response = requests.get(CAPTURE_URL, timeout=3)
        if response.status_code == 200 and len(response.content) > 1000:
            camera_working = True
            print(f"[CAMERA] ✅ Camera is healthy (response: {len(response.content)} bytes)")
            return True
        else:
            print(f"[CAMERA] ❌ Camera response issue: status={response.status_code}, size={len(response.content)}")
    except Exception as e:
        print(f"[CAMERA] ❌ Camera test failed: {e}")
    
    camera_working = False
    print("[CAMERA] ❌ Camera is not working - AUDIO DISABLED for safety")
    return False

# Function to test ESP32-CAM connection
def find_working_stream_url():
    print("[INFO] Testing ESP32-CAM stream connection...")
    
    # Test stream URL first with shorter timeout
    print(f"[TEST] Trying stream: {STREAM_URL}")
    try:
        cap = cv2.VideoCapture(STREAM_URL)
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)  # 5 second timeout
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 3000)  # 3 second read timeout
        
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                print(f"[SUCCESS] Stream working: {STREAM_URL}")
                cap.release()
                return STREAM_URL, "stream"
        cap.release()
    except Exception as e:
        print(f"[ERROR] Stream connection failed: {e}")
    
    print("[INFO] Stream failed, trying capture mode...")
    return CAPTURE_URL, "capture"

# Function to send data to Blynk
def send_to_blynk(pin, value):
    try:
        url = f"https://{BLYNK_SERVER}/external/api/update?token={BLYNK_TOKEN}&{pin}={value}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"[BLYNK] Sent {pin}={value}")
        else:
            print(f"[BLYNK ERROR] Status code: {response.status_code}")
    except Exception as e:
        print(f"[BLYNK ERROR] {e}")

def read_from_blynk(pin):
    """Read value from Blynk virtual pin"""
    try:
        url = f"https://{BLYNK_SERVER}/external/api/get?token={BLYNK_TOKEN}&{pin}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            value = response.text.strip()
            return value
        else:
            print(f"[BLYNK ERROR] Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"[BLYNK ERROR] {e}")
        return None

def monitor_alarm_status():
    """Monitor V5 pin to check if it's alarm time with improved state tracking"""
    global last_alarm_status, audio_playing
    
    try:
        alarm_time_status = read_from_blynk(ALARM_TIME_PIN)
        print(f"[DEBUG] V5 read: {alarm_time_status} (last: {last_alarm_status})")
        
        # Only print debug if status changed to reduce spam
        if alarm_time_status != last_alarm_status:
            print(f"[V5 STATUS CHANGE] {last_alarm_status} → {alarm_time_status}")
        
        if alarm_time_status == "1":
            # Alarm is active - but only start sound if camera is working
            if not audio_playing:
                # Test camera health before playing audio
                if test_camera_health():
                    print("⏰ [ALARM] NEW ALARM TRIGGERED on V5 - Camera OK - Starting laptop sound")
                    play_alarm_sound()
                    reset_face_detection_state()  # Reset face detection for new alarm
                else:
                    print("🚫 [SAFETY] ALARM TRIGGERED but camera not working - AUDIO BLOCKED")
                    print("🔧 [SAFETY] Fix camera connection to enable audio safety stop")
            last_alarm_status = "1"
            return True
            
        elif alarm_time_status == "0":
            # Alarm is inactive - stop sound if playing
            if audio_playing:
                print("✅ [ALARM] ALARM STOPPED on V5 - Stopping laptop sound")
                stop_alarm_sound()
                reset_face_detection_state()  # Reset for next alarm
            last_alarm_status = "0"
            return False
            
        else:
            print(f"⚠️ [ALARM] Unexpected V5 value: {alarm_time_status}")
            last_alarm_status = alarm_time_status
            return False
            
    except Exception as e:
        print(f"❌ [BLYNK ERROR] Failed to check V5 status: {e}")
        return False

def reset_face_detection_state():
    """Reset face detection state for new alarm cycle"""
    global face_status_sent, last_face_detected_time
    face_status_sent = False
    last_face_detected_time = 0
    print("🔄 [RESET] Face detection state reset for new alarm cycle")

# Function to handle face detection status
def handle_face_detection(faces_detected):
    global last_face_detected_time, face_status_sent
    current_time = time.time()
    
    if len(faces_detected) > 0:
        # Face detected
        last_face_detected_time = current_time
        if not face_status_sent:
            send_to_blynk(FACE_DETECTED_PIN, 1)
            face_status_sent = True
            print("🚨 [FACE] Face detected - Sending stop signal to ESP32!")
            print("🔄 [FACE] ESP32 will handle stopping alarm and laptop will follow V5 pin")
    else:
        # No face detected - only send "no face" signal after timeout
        if face_status_sent and (current_time - last_face_detected_time) > NO_FACE_TIMEOUT:
            send_to_blynk(FACE_DETECTED_PIN, 0)
            face_status_sent = False
            print("👁️ [FACE] No face timeout - Ready for next detection...")

# ================== AUDIO CONTROL FUNCTIONS ==================
def initialize_audio():
    """Initialize pygame mixer for audio and load alarm.wav"""
    global alarm_sound
    
    try:
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        
        # Load the alarm.wav file
        alarm_sound = pygame.mixer.Sound(ALARM_AUDIO_FILE)
        print(f"[AUDIO] Loaded alarm sound: {ALARM_AUDIO_FILE}")
        print("[AUDIO] Pygame audio initialized")
        return True
    except Exception as e:
        print(f"[AUDIO ERROR] Failed to initialize: {e}")
        return False

def generate_tone(frequency, duration_ms):
    """Generate a tone using numpy and pygame"""
    sample_rate = 22050
    duration_s = duration_ms / 1000.0
    frames = int(duration_s * sample_rate)
    
    # Generate sine wave
    arr = np.zeros((frames, 2))
    for i in range(frames):
        wave = np.sin(2 * np.pi * frequency * i / sample_rate)
        arr[i] = [wave, wave]
    
    # Convert to 16-bit integers
    arr = (arr * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(arr)

def play_alarm_sound():
    """Start playing the alarm sound in a loop"""
    global audio_playing, audio_thread
    
    if audio_playing:
        return
    
    audio_playing = True
    print("🔊 [LAPTOP] Starting alarm sound")
    
    def audio_loop():
        global audio_playing
        try:
            while audio_playing:
                if alarm_sound:
                    alarm_sound.play()
                    pygame.time.wait(int(alarm_sound.get_length() * 1000))
                else:
                    # Fallback: generate beep tone
                    beep = generate_tone(800, 500)  # 800Hz for 500ms
                    beep.play()
                    pygame.time.wait(500)
                    if audio_playing:  # Check again after beep
                        beep = generate_tone(1000, 500)  # 1000Hz for 500ms
                        beep.play()
                        pygame.time.wait(500)
        except Exception as e:
            print(f"[AUDIO ERROR] {e}")

    audio_thread = threading.Thread(target=audio_loop, daemon=True)
    audio_thread.start()
    print("🔊 [SYNC] ESP32 alarm detected - Starting laptop sound")

def stop_alarm_sound():
    """Stop the alarm sound"""
    global audio_playing
    
    if not audio_playing:
        return
        
    audio_playing = False
    pygame.mixer.stop()
    print("🔇 [LAPTOP] Stopping alarm sound")

# ================== VIDEO FUNCTIONS ==================
def capture_frame():
    """Capture a single frame from ESP32-CAM"""
    try:
        response = requests.get(CAPTURE_URL, timeout=5)
        if response.status_code == 200:
            # Convert bytes to numpy array
            img_array = np.frombuffer(response.content, dtype=np.uint8)
            # Decode image
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            return frame
        else:
            print(f"[ERROR] HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"[ERROR] Failed to capture: {e}")
        return None

def run_stream_mode(stream_url):
    print(f"[INFO] Running in INTEGRATED mode: {stream_url}")
    print("[INFO] 🎵 Audio + 📹 Face detection working together")
    
    # Set up video capture with timeouts
    cap = cv2.VideoCapture(stream_url)
    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 3000)  # 3 second timeout
    cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 1000)  # 1 second read timeout
    
    if not cap.isOpened():
        print(f"[ERROR] Could not open video stream - falling back to capture mode")
        cap.release()
        return False
    
    print("[INFO] Stream connected! Press 'q' to quit.")
    print("[INFO] 📡 Monitoring V5 pin for ESP32 alarms + processing face detection")
    
    last_alarm_check = time.time()
    alarm_check_interval = 1.0  # Check alarm status every second
    frame_timeout_count = 0
    max_timeouts = 5  # Allow 5 timeouts before switching modes
    
    while True:
        # Check alarm status periodically (PRIORITY #1)
        current_time = time.time()
        if current_time - last_alarm_check >= alarm_check_interval:
            print(f"[DEBUG] Checking alarm status at {current_time:.1f}")
            monitor_alarm_status()
            last_alarm_check = current_time

        # Try to read frame (with timeout handling)
        ret, frame = cap.read()
        if not ret:
            frame_timeout_count += 1
            print(f"[WARNING] Frame read failed ({frame_timeout_count}/{max_timeouts})")
            
            # If camera fails while audio is playing, stop audio for safety
            if frame_timeout_count >= 3 and audio_playing:
                print("🚫 [SAFETY] Camera failing while alarm active - STOPPING AUDIO for safety")
                stop_alarm_sound()
                global camera_working
                camera_working = False
            
            if frame_timeout_count >= max_timeouts:
                print("[ERROR] Too many frame timeouts - switching to capture mode")
                break
            continue
        
        # Reset timeout counter on successful frame
        frame_timeout_count = 0

        # Detect and process faces
        frame = process_frame(frame)

        # Show the video with detections
        cv2.imshow('ESP32-CAM Face Detection (Integrated Mode)', frame)

        # Exit when 'q' key is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    return False  # Return False to try capture mode

def run_capture_mode():
    print(f"[INFO] Running in INTEGRATED mode: {CAPTURE_URL}")
    print("[INFO] 🎵 Audio + 📹 Face detection working together")
    print("[INFO] Capturing frames every 1 second. Press 'q' to quit.")
    print("[INFO] 📡 Monitoring V5 pin for ESP32 alarms + processing face detection")
    
    last_alarm_check = time.time()
    alarm_check_interval = 1.0  # Check alarm status every second
    capture_fail_count = 0
    max_capture_fails = 3
    
    while True:
        # Check alarm status periodically (PRIORITY #1)
        current_time = time.time()
        if current_time - last_alarm_check >= alarm_check_interval:
            monitor_alarm_status()
            last_alarm_check = current_time
            
        frame = capture_frame()
        if frame is not None:
            # Reset fail counter on successful capture
            capture_fail_count = 0
            
            # Detect and process faces
            frame = process_frame(frame)
            
            # Show the image with detections
            cv2.imshow('ESP32-CAM Face Detection (Integrated Mode)', frame)
        else:
            capture_fail_count += 1
            print(f"[WARNING] Failed to capture frame ({capture_fail_count}/{max_capture_fails})")
            
            # If camera fails while audio is playing, stop audio for safety
            if capture_fail_count >= max_capture_fails and audio_playing:
                print("🚫 [SAFETY] Camera failing while alarm active - STOPPING AUDIO for safety")
                stop_alarm_sound()
                global camera_working
                camera_working = False
        
        # Exit when 'q' key is pressed or wait 1 second
        if cv2.waitKey(1000) & 0xFF == ord('q'):
            break
    
    cv2.destroyAllWindows()
    return True

# Function to process frame for face detection
def process_frame(frame):
    # Convert to grayscale for face detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,   # Image size reduction between scans
        minNeighbors=5,    # Number of neighbor rectangles needed to confirm a face
        minSize=(30, 30)   # Minimum face size
    )

    # Draw rectangles around faces
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
        cv2.putText(frame, 'Face Detected', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    # Handle face detection status
    handle_face_detection(faces)

    # Add status overlay
    status_text = f"Faces: {len(faces)}"
    cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # Add audio status
    audio_status = "ALARM ON" if audio_playing else "ALARM OFF"
    cv2.putText(frame, audio_status, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255) if audio_playing else (0, 255, 0), 2)

    return frame

# Audio-only mode - monitor V5 pin for alarm triggers
def run_audio_only_mode():
    """Run in audio-only mode, monitoring V5 pin for alarm triggers"""
    global last_status_check_time
    
    print("🎵 Starting enhanced audio-only alarm monitoring...")
    print("📡 Continuous Blynk V5 pin monitoring for instant sync")
    print("🔊 Will play alarm.wav when ESP32 triggers alarm")
    
    # Test audio system
    print("🧪 Testing audio system...")
    play_alarm_sound()
    time.sleep(2)
    stop_alarm_sound()
    print("✅ Audio test complete")
    
    print("🕐 Starting continuous V5 pin monitoring...")
    print(f"⚡ Check interval: {STATUS_CHECK_INTERVAL} second(s)")
    print("Press Ctrl+C to stop")
    
    iteration = 0
    
    try:
        while True:
            current_time = time.time()
            
            # Check alarm status at regular intervals
            if current_time - last_status_check_time >= STATUS_CHECK_INTERVAL:
                iteration += 1
                print(f"[CHECK {iteration}] Monitoring V5 pin...")
                
                try:
                    monitor_alarm_status()
                    last_status_check_time = current_time
                except Exception as e:
                    print(f"❌ Error checking V5: {e}")
            
            # Small sleep to prevent CPU overload
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n🔇 Stopping alarm monitoring...")
        stop_alarm_sound()

# Initialize audio system
print("[AUDIO] Initializing laptop audio system...")
if not initialize_audio():
    print("[WARNING] Audio initialization failed - continuing without laptop sound")

# Main execution
if AUDIO_ONLY_MODE:
    print("[MODE] Running in AUDIO-ONLY mode - monitoring V5 for alarm triggers")
    run_audio_only_mode()
else:
    url, mode = find_working_stream_url()

    if mode == "stream":
        success = run_stream_mode(url)
        if not success:
            print("[INFO] Stream mode failed, falling back to capture mode...")
            run_capture_mode()
    elif mode == "capture":
        run_capture_mode()
    else:
        print("[ERROR] Could not establish any connection to ESP32-CAM!")
        print("[INFO] Please check:")
        print("  1. ESP32-CAM is powered on and connected to WiFi")
        print("  2. IP address is correct (check ESP32 serial monitor)")
        print(f"  3. Try accessing http://{ESP32_IP} in browser")
        exit()

# Cleanup audio on exit
stop_alarm_sound()
pygame.mixer.quit()
