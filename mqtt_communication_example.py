"""
Alternative Method: MQTT Communication
Both Python script and ESP32 connect to an MQTT broker
"""

import cv2
import paho.mqtt.client as mqtt
import time
import json

# MQTT Configuration
MQTT_BROKER = "broker.hivemq.com"  # Free public broker (or use your own)
MQTT_PORT = 1883
MQTT_TOPIC = "iot_alarm/face_detection"

# Face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker with result code {rc}")

def send_face_status_mqtt(client, detected):
    message = {
        "face_detected": detected,
        "timestamp": time.time()
    }
    client.publish(MQTT_TOPIC, json.dumps(message))
    print(f"📡 MQTT: Sent face_detected={detected}")

# Setup MQTT client
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect

print("MQTT method example - requires MQTT library on ESP32")
print("Install PubSubClient library in Arduino IDE for ESP32 MQTT support")
print("For immediate use, stick with the Blynk method!")
