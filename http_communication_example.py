"""
Alternative Method: Direct HTTP communication to ESP32
This method sends HTTP requests directly to your ESP32 if it runs a web server
"""

import cv2
import requests
import time

# Configuration
ESP32_URL = "http://192.168.0.107:81/stream"  # Camera stream
ESP32_API_URL = "http://192.168.0.107"  # ESP32 web server (you need to implement this)

# Face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def send_face_status_to_esp32(detected):
    try:
        # Send POST request to ESP32
        data = {"face_detected": 1 if detected else 0}
        response = requests.post(f"{ESP32_API_URL}/face_status", json=data, timeout=3)
        if response.status_code == 200:
            print(f"✅ Sent face status to ESP32: {detected}")
        else:
            print(f"❌ Failed to send to ESP32: {response.status_code}")
    except Exception as e:
        print(f"❌ Error communicating with ESP32: {e}")

# This would require adding HTTP server code to your ESP32 Arduino sketch
print("This method requires implementing an HTTP server on your ESP32")
print("For now, use the Blynk method which is already implemented!")
