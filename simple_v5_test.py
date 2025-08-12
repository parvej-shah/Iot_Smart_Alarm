#!/usr/bin/env python3
"""
Simple V5 Pin Test
==================
Quick test to verify V5 pin read/write functionality
"""

import requests
import time

# Configuration
BLYNK_TOKEN = "mhwBpFwWvcRB3z9DexrimUS7YJay4lBU"
BLYNK_SERVER = "blynk.cloud"

def read_v5():
    """Read V5 pin value"""
    try:
        url = f"https://{BLYNK_SERVER}/external/api/get?token={BLYNK_TOKEN}&V5"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            value = response.text.strip('[""]')
            return value
        elif response.status_code == 400:
            print("V5 pin has no value yet")
            return None
        else:
            print(f"Error reading V5: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception reading V5: {e}")
        return None

def write_v5(value):
    """Write value to V5 pin"""
    try:
        url = f"https://{BLYNK_SERVER}/external/api/update?token={BLYNK_TOKEN}&V5={value}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            print(f"✅ Successfully wrote {value} to V5")
            return True
        else:
            print(f"❌ Error writing to V5: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exception writing to V5: {e}")
        return False

def main():
    print("🔍 SIMPLE V5 PIN TEST")
    print("="*30)
    
    # Step 1: Check initial state
    print("1. Reading initial V5 value...")
    initial = read_v5()
    print(f"   Initial V5: {initial}")
    
    # Step 2: Test write 1
    print("\n2. Testing V5 = 1 (alarm trigger)...")
    if write_v5(1):
        time.sleep(2)
        value = read_v5()
        print(f"   V5 after write 1: {value}")
        if value == "1":
            print("   ✅ V5 write 1 works!")
        else:
            print("   ❌ V5 write 1 failed!")
    
    # Step 3: Test write 0
    print("\n3. Testing V5 = 0 (alarm stop)...")
    if write_v5(0):
        time.sleep(2)
        value = read_v5()
        print(f"   V5 after write 0: {value}")
        if value == "0":
            print("   ✅ V5 write 0 works!")
        else:
            print("   ❌ V5 write 0 failed!")
    
    # Step 4: Monitor for ESP32 changes
    print("\n4. Monitoring for ESP32 changes (30 seconds)...")
    print("   Set an alarm in Blynk app to test!")
    
    last_value = read_v5()
    for i in range(30):
        current_value = read_v5()
        if current_value != last_value:
            print(f"   🔄 V5 changed: {last_value} → {current_value}")
            if current_value == "1":
                print("   🚨 ALARM DETECTED!")
            elif current_value == "0":
                print("   ✅ ALARM STOPPED!")
            last_value = current_value
        
        time.sleep(1)
    
    print(f"\n🏁 Final V5 value: {read_v5()}")
    print("✅ Test completed!")

if __name__ == "__main__":
    main()
