#!/usr/bin/env python3
"""
V5 Pin Monitoring Test Script
=============================
This script specifically tests if the V5 pin is working correctly for alarm monitoring.
It will continuously read the V5 pin value and show real-time changes.
"""

import requests
import time
import json
from datetime import datetime

# Configuration
BLYNK_TOKEN = "mhwBpFwWvcRB3z9DexrimUS7YJay4lBU"
BLYNK_SERVER = "blynk.cloud"
V5_PIN = "V5"

def read_blynk_pin(pin):
    """Read value from Blynk virtual pin"""
    try:
        url = f"https://{BLYNK_SERVER}/external/api/get?token={BLYNK_TOKEN}&{pin}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            value = response.text.strip('[""]')  # Remove JSON formatting
            return value
        else:
            print(f"❌ Error reading {pin}: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Exception reading {pin}: {e}")
        return None

def write_blynk_pin(pin, value):
    """Write value to Blynk virtual pin"""
    try:
        url = f"https://{BLYNK_SERVER}/external/api/update?token={BLYNK_TOKEN}&{pin}={value}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Successfully wrote {value} to {pin}")
            return True
        else:
            print(f"❌ Error writing to {pin}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exception writing to {pin}: {e}")
        return False

def test_v5_monitoring():
    """Test V5 pin monitoring functionality"""
    print("=" * 60)
    print("🔍 V5 PIN MONITORING TEST")
    print("=" * 60)
    print(f"📡 Blynk Server: {BLYNK_SERVER}")
    print(f"🔑 Token: {BLYNK_TOKEN[:10]}...")
    print(f"📍 Monitoring Pin: {V5_PIN}")
    print("=" * 60)
    
    # Test initial connection
    print("\n🧪 Testing initial connection...")
    initial_value = read_blynk_pin(V5_PIN)
    if initial_value is None:
        print("❌ Failed to read initial V5 value. Check connection!")
        return
    
    print(f"✅ Initial V5 value: {initial_value}")
    
    # Test manual write to V5 (simulate ESP32)
    print("\n🔧 Testing manual V5 control...")
    print("Setting V5 = 1 (simulate alarm trigger)...")
    if write_blynk_pin(V5_PIN, 1):
        time.sleep(2)
        test_value = read_blynk_pin(V5_PIN)
        print(f"📖 V5 after write: {test_value}")
        
        time.sleep(2)
        print("Setting V5 = 0 (simulate alarm stop)...")
        write_blynk_pin(V5_PIN, 0)
        time.sleep(2)
        test_value = read_blynk_pin(V5_PIN)
        print(f"📖 V5 after reset: {test_value}")
    
    print("\n👀 Starting continuous monitoring...")
    print("Press Ctrl+C to stop")
    print("-" * 60)
    
    last_value = None
    check_count = 0
    
    try:
        while True:
            check_count += 1
            current_time = datetime.now().strftime("%H:%M:%S")
            current_value = read_blynk_pin(V5_PIN)
            
            if current_value is not None:
                if current_value != last_value:
                    print(f"🔄 [{current_time}] V5 CHANGED: {last_value} → {current_value}")
                    if current_value == "1":
                        print("🚨 ALARM TRIGGERED detected on V5!")
                    elif current_value == "0":
                        print("✅ ALARM STOPPED detected on V5!")
                    last_value = current_value
                else:
                    # Show periodic status every 10 checks
                    if check_count % 10 == 0:
                        print(f"📊 [{current_time}] V5 stable: {current_value} (check #{check_count})")
            else:
                print(f"❌ [{current_time}] Failed to read V5")
            
            time.sleep(1)  # Check every second
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️ Monitoring stopped. Total checks: {check_count}")
        print("Final V5 value:", read_blynk_pin(V5_PIN))

def test_all_pins():
    """Test reading all relevant pins for debugging"""
    print("\n🔍 READING ALL RELEVANT PINS:")
    print("-" * 40)
    
    pins_to_check = ["V0", "V1", "V2", "V3", "V4", "V5"]
    
    for pin in pins_to_check:
        value = read_blynk_pin(pin)
        print(f"{pin}: {value}")

if __name__ == "__main__":
    print("🚀 Starting V5 Monitoring Test...")
    
    # First, check all pins
    test_all_pins()
    
    # Then start V5 specific monitoring
    test_v5_monitoring()
