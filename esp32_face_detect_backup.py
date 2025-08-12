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
AUDIO_ONLY_MODE = True

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

# Load Haar Cascade for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Variables for face detection tracking
last_face_detected_time = 0
face_status_sent = False

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
            # Alarm is active - start sound if not already playing
            if not audio_playing:
                print("⏰ [ALARM] NEW ALARM TRIGGERED on V5 - Starting laptop sound")
                play_alarm_sound()
            last_alarm_status = "1"
            return True
            
        elif alarm_time_status == "0":
            # Alarm is inactive - stop sound if playing
            if audio_playing:
                print("✅ [ALARM] ALARM STOPPED on V5 - Stopping laptop sound")
                stop_alarm_sound()
            last_alarm_status = "0"
            return False
            
        else:
            print(f"⚠️ [ALARM] Unexpected V5 value: {alarm_time_status}")
            last_alarm_status = alarm_time_status
            return False
            
    except Exception as e:
        print(f"❌ [BLYNK ERROR] Failed to check V5 status: {e}")
        return False

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
                    time.sleep(1)
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

# Main execution - Audio-only mode for testing timing
if AUDIO_ONLY_MODE:
    print("[MODE] Running in AUDIO-ONLY mode - monitoring V5 for alarm triggers")
    run_audio_only_mode()

# Cleanup audio on exit
stop_alarm_sound()
pygame.mixer.quit()
