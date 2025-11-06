#!/usr/bin/env python3
"""
Final Docker Test - Simple and Complete
"""
import requests
import time

BASE_URL = "http://localhost:8000"

def run_final_tests():
    print("🎯 Final Docker Test Suite")
    print("=" * 50)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Health Check
    tests_total += 1
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health Check - PASSED")
            tests_passed += 1
        else:
            print(f"❌ Health Check - FAILED (HTTP {response.status_code})")
    except Exception as e:
        print(f"❌ Health Check - FAILED ({str(e)})")
    
    # Test 2: Session Creation
    tests_total += 1
    session_id = None
    try:
        response = requests.post(f"{BASE_URL}/api/sessions", 
                               json={"name": "Final Test Session"})
        if response.status_code == 200:
            session_id = response.json()["id"]
            print("✅ Session Creation - PASSED")
            tests_passed += 1
        else:
            print(f"❌ Session Creation - FAILED (HTTP {response.status_code})")
    except Exception as e:
        print(f"❌ Session Creation - FAILED ({str(e)})")
    
    # Test 3: Chat Functionality
    tests_total += 1
    if session_id:
        try:
            response = requests.post(f"{BASE_URL}/api/sessions/{session_id}/chat",
                                   json={"message": "Hello! Test message."})
            if response.status_code == 200:
                data = response.json()
                if data.get("assistant_message", {}).get("content"):
                    print("✅ Chat Functionality - PASSED")
                    tests_passed += 1
                else:
                    print("❌ Chat Functionality - FAILED (No AI response)")
            else:
                print(f"❌ Chat Functionality - FAILED (HTTP {response.status_code})")
        except Exception as e:
            print(f"❌ Chat Functionality - FAILED ({str(e)})")
    else:
        print("❌ Chat Functionality - SKIPPED (No session)")
    
    # Test 4: Session Listing
    tests_total += 1
    try:
        response = requests.get(f"{BASE_URL}/api/sessions")
        if response.status_code == 200:
            sessions = response.json().get("sessions", [])
            print(f"✅ Session Listing - PASSED ({len(sessions)} sessions)")
            tests_passed += 1
        else:
            print(f"❌ Session Listing - FAILED (HTTP {response.status_code})")
    except Exception as e:
        print(f"❌ Session Listing - FAILED ({str(e)})")
    
    # Test 5: Database Integration
    tests_total += 1
    if session_id:
        try:
            response = requests.get(f"{BASE_URL}/api/sessions/{session_id}/history")
            if response.status_code == 200:
                messages = response.json().get("messages", [])
                print(f"✅ Database Integration - PASSED ({len(messages)} messages stored)")
                tests_passed += 1
            else:
                print(f"❌ Database Integration - FAILED (HTTP {response.status_code})")
        except Exception as e:
            print(f"❌ Database Integration - FAILED ({str(e)})")
    else:
        print("❌ Database Integration - SKIPPED (No session)")
    
    # Final Results
    print("\n" + "=" * 50)
    print(f"📊 FINAL RESULTS: {tests_passed}/{tests_total} tests passed")
    
    if tests_passed == tests_total:
        print("🎉 ALL TESTS PASSED! Docker setup is working perfectly.")
        print("\n🌐 Application is ready at: http://localhost:8000")
        return True
    else:
        print(f"⚠️  {tests_total - tests_passed} tests failed. Check the logs above.")
        return False

if __name__ == "__main__":
    success = run_final_tests()
    exit(0 if success else 1)