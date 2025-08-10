import cv2
import requests
import time

# ======== CONFIG ========
# Replace with your ESP32-CAM's IP address
ESP32_URL = "http://192.168.0.105:81/stream"  # Try port 81 first
ESP32_BACKUP_URLS = [
    "http://192.168.0.105/stream",
    "http://192.168.0.105/capture",
    "http://192.168.0.105:8080/stream",
    "http://192.168.0.105/mjpeg/1"
]

# Blynk configuration
BLYNK_TOKEN = "mhwBpFwWvcRB3z9DexrimUS7YJay4lBU"
BLYNK_SERVER = "blynk.cloud"

# Face detection settings
FACE_DETECTED_PIN = "V4"  # Virtual pin to send face detection status
NO_FACE_TIMEOUT = 5  # Seconds to wait before sending "no face" signal

# Load Haar Cascade for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Variables for face detection tracking
last_face_detected_time = 0
face_status_sent = False

# Function to test ESP32-CAM connection
def find_working_stream_url():
    print("[INFO] Testing ESP32-CAM connection...")
    
    # Test main URL first
    print(f"[TEST] Trying: {ESP32_URL}")
    cap = cv2.VideoCapture(ESP32_URL)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret and frame is not None:
            print(f"[SUCCESS] Working stream found: {ESP32_URL}")
            cap.release()
            return ESP32_URL
        cap.release()
    
    # Test backup URLs
    for url in ESP32_BACKUP_URLS:
        print(f"[TEST] Trying: {url}")
        cap = cv2.VideoCapture(url)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                print(f"[SUCCESS] Working stream found: {url}")
                cap.release()
                return url
            cap.release()
    
    print("[ERROR] No working stream URL found!")
    return None

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
            print("🚨 [FACE] Face detected - ALARM WILL STOP! Alert sent to ESP32!")
    else:
        # No face detected
        if face_status_sent and (current_time - last_face_detected_time) > NO_FACE_TIMEOUT:
            send_to_blynk(FACE_DETECTED_PIN, 0)
            face_status_sent = False
            print("👁️ [FACE] No face detected - Monitoring continues...")

# Find working stream URL
working_url = find_working_stream_url()
if working_url is None:
    print("[ERROR] Could not find any working ESP32-CAM stream!")
    print("[INFO] Please check:")
    print("  1. ESP32-CAM is powered on and connected to WiFi")
    print("  2. IP address is correct (check ESP32 serial monitor)")
    print("  3. Try accessing http://192.168.0.105 in browser")
    exit()

# Connect to ESP32-CAM stream
cap = cv2.VideoCapture(working_url)

if not cap.isOpened():
    print(f"[ERROR] Could not open video stream from {working_url}")
    exit()

print(f"[INFO] Connected to ESP32-CAM at: {working_url}")
print("[INFO] Starting face detection... Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("[WARNING] Failed to grab frame")
        break

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
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
    
    # Handle face detection communication with ESP32
    handle_face_detection(faces)
    
    # Display face count on frame
    cv2.putText(frame, f"Faces: {len(faces)}", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Show the video with detections
    cv2.imshow('ESP32-CAM Face Detection', frame)

    # Exit when 'q' key is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
