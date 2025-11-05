#!/usr/bin/env python3
"""
Quick Test - Simple verification
"""
import requests
import time

BASE_URL = "http://localhost:8000"

def quick_test():
    print("🚀 Quick Test")
    print("=" * 20)
    
    # Test 1: Can we reach the app?
    try:
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code == 200:
            print("✅ App is running")
        else:
            print(f"❌ App not responding: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot reach app: {e}")
        return False
    
    # Test 2: Can we create a session?
    try:
        response = requests.post(f"{BASE_URL}/api/sessions", 
                               json={"name": "Quick Test"}, timeout=5)
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data["id"]
            print(f"✅ Created session: {session_id[:8]}...")
        else:
            print(f"❌ Cannot create session: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Session creation failed: {e}")
        return False
    
    # Test 3: Can we send a message?
    try:
        response = requests.post(f"{BASE_URL}/api/sessions/{session_id}/chat",
                               json={"message": "Hello!"}, timeout=15)
        if response.status_code == 200:
            chat_data = response.json()
            ai_response = chat_data.get("assistant_message", {}).get("content", "")
            print(f"✅ Chat works: {ai_response[:30]}...")
        else:
            print(f"❌ Chat failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return False
    
    print("\n🎉 All tests passed!")
    print(f"🌐 Open your browser: {BASE_URL}")
    return True

if __name__ == "__main__":
    quick_test()