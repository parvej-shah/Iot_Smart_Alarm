import requests
import time

# Blynk configuration
BLYNK_TOKEN = "mhwBpFwWvcRB3z9DexrimUS7YJay4lBU"
BLYNK_SERVER = "blynk.cloud"
FACE_DETECTED_PIN = "V4"

def send_to_blynk(pin, value):
    try:
        url = f"https://{BLYNK_SERVER}/external/api/update?token={BLYNK_TOKEN}&{pin}={value}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ Successfully sent {pin}={value} to ESP32")
            return True
        else:
            print(f"❌ Failed: Status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_communication():
    print("Testing Blynk communication with ESP32...")
    print("Make sure your ESP32 is connected and running the alarm system code.")
    print()
    
    # Test sending face detected signal
    print("1. Sending 'Face Detected' signal...")
    send_to_blynk(FACE_DETECTED_PIN, 1)
    time.sleep(3)
    
    # Test sending no face signal
    print("2. Sending 'No Face' signal...")
    send_to_blynk(FACE_DETECTED_PIN, 0)
    time.sleep(3)
    
    print("Test completed! Check your ESP32 serial monitor for messages.")

if __name__ == "__main__":
    test_communication()
