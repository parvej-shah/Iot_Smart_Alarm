#!/usr/bin/env python3
"""
Blynk Communication Test Script
===============================
Tests all aspects of Blynk communication to verify V5 pin functionality
"""

import requests
import time
import json
from datetime import datetime

# Configuration
BLYNK_TOKEN = "mhwBpFwWvcRB3z9DexrimUS7YJay4lBU"
BLYNK_SERVER = "blynk.cloud"

def test_blynk_connection():
    """Test basic Blynk connectivity"""
    print("🧪 Testing Blynk Connection...")
    
    try:
        # Test basic connection with a simple GET
        url = f"https://{BLYNK_SERVER}/external/api/get?token={BLYNK_TOKEN}&V0"
        response = requests.get(url, timeout=10)
        
        print(f"📡 Server: {BLYNK_SERVER}")
        print(f"🔗 Status Code: {response.status_code}")
        print(f"📝 Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Blynk connection successful!")
            return True
        else:
            print("❌ Blynk connection failed!")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def read_pin(pin):
    """Read value from Blynk pin with detailed debugging"""
    try:
        url = f"https://{BLYNK_SERVER}/external/api/get?token={BLYNK_TOKEN}&{pin}"
        print(f"📤 GET: {url}")
        
        response = requests.get(url, timeout=10)
        print(f"📥 Response Code: {response.status_code}")
        print(f"📄 Raw Response: '{response.text}'")
        
        if response.status_code == 200:
            # Handle different response formats
            raw_value = response.text.strip()
            if raw_value.startswith('["') and raw_value.endswith('"]'):
                # JSON array format: ["value"]
                value = raw_value[2:-2]  # Remove [""]
            elif raw_value.startswith('[') and raw_value.endswith(']'):
                # JSON array format: [value]
                value = raw_value[1:-1]  # Remove []
            else:
                # Plain text
                value = raw_value
                
            print(f"✅ Parsed value: '{value}'")
            return value
        else:
            print(f"❌ Failed to read {pin}")
            return None
    except Exception as e:
        print(f"❌ Exception reading {pin}: {e}")
        return None

def write_pin(pin, value):
    """Write value to Blynk pin with detailed debugging"""
    try:
        url = f"https://{BLYNK_SERVER}/external/api/update?token={BLYNK_TOKEN}&{pin}={value}"
        print(f"📤 PUT: {url}")
        
        response = requests.get(url, timeout=10)
        print(f"📥 Response Code: {response.status_code}")
        print(f"📄 Response: '{response.text}'")
        
        if response.status_code == 200:
            print(f"✅ Successfully wrote {value} to {pin}")
            return True
        else:
            print(f"❌ Failed to write to {pin}")
            return False
    except Exception as e:
        print(f"❌ Exception writing to {pin}: {e}")
        return False

def test_v5_specifically():
    """Comprehensive V5 pin testing"""
    print("\n" + "="*50)
    print("🎯 COMPREHENSIVE V5 PIN TEST")
    print("="*50)
    
    # Step 1: Read initial value
    print("\n1️⃣ Reading initial V5 value...")
    initial_value = read_pin("V5")
    
    # Step 2: Test write functionality
    print("\n2️⃣ Testing V5 write functionality...")
    print("Setting V5 = 1...")
    if write_pin("V5", 1):
        time.sleep(2)
        print("Reading V5 after write...")
        value_after_write = read_pin("V5")
        if value_after_write == "1":
            print("✅ V5 write test PASSED")
        else:
            print(f"❌ V5 write test FAILED. Expected '1', got '{value_after_write}'")
    
    # Step 3: Test reset functionality
    print("\n3️⃣ Testing V5 reset functionality...")
    print("Setting V5 = 0...")
    if write_pin("V5", 0):
        time.sleep(2)
        print("Reading V5 after reset...")
        value_after_reset = read_pin("V5")
        if value_after_reset == "0":
            print("✅ V5 reset test PASSED")
        else:
            print(f"❌ V5 reset test FAILED. Expected '0', got '{value_after_reset}'")
    
    # Step 4: Simulate ESP32 alarm trigger
    print("\n4️⃣ Simulating ESP32 alarm trigger...")
    print("This simulates what the ESP32 does when alarm triggers")
    write_pin("V5", 1)
    time.sleep(1)
    status = read_pin("V5")
    print(f"V5 status after simulated ESP32 trigger: {status}")
    
    # Step 5: Simulate face detection (ESP32 stops alarm)
    print("\n5️⃣ Simulating face detection (alarm stop)...")
    print("This simulates what the ESP32 does when face is detected")
    write_pin("V5", 0)
    time.sleep(1)
    status = read_pin("V5")
    print(f"V5 status after simulated face detection: {status}")

def monitor_v5_changes(duration=60):
    """Monitor V5 for changes over a specific duration"""
    print(f"\n📡 Monitoring V5 for {duration} seconds...")
    print("You can trigger alarms from the Blynk app during this time.")
    print("Press Ctrl+C to stop early")
    
    last_value = None
    start_time = time.time()
    
    try:
        while (time.time() - start_time) < duration:
            current_value = read_pin("V5")
            current_time = datetime.now().strftime("%H:%M:%S")
            
            if current_value != last_value:
                print(f"🔄 [{current_time}] V5 CHANGED: {last_value} → {current_value}")
                
                if current_value == "1":
                    print("🚨 ALARM TRIGGER detected!")
                elif current_value == "0":
                    print("✅ ALARM STOP detected!")
                
                last_value = current_value
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Monitoring stopped by user")
    
    final_value = read_pin("V5")
    print(f"🏁 Final V5 value: {final_value}")

def main():
    print("🚀 BLYNK V5 PIN COMPREHENSIVE TEST")
    print("="*60)
    
    # Test 1: Basic connection
    if not test_blynk_connection():
        print("❌ Cannot proceed - Blynk connection failed!")
        return
    
    # Test 2: V5 specific tests
    test_v5_specifically()
    
    # Test 3: Monitor for real changes
    print("\n" + "="*50)
    print("🔍 LIVE MONITORING")
    print("="*50)
    print("Now you can:")
    print("1. Set an alarm in the Blynk app")
    print("2. Wait for it to trigger")
    print("3. Use face detection to stop it")
    print("4. Watch V5 pin changes in real-time")
    
    monitor_v5_changes(120)  # Monitor for 2 minutes
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    main()
