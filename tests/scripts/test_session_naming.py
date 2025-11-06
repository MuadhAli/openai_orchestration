#!/usr/bin/env python3
"""
Test Automatic Session Naming Feature
"""
import requests
import time

BASE_URL = "http://localhost:8000"

def test_session_naming():
    print("🏷️  Testing Automatic Session Naming")
    print("=" * 50)
    
    test_cases = [
        {
            "message": "How do I learn Python programming?",
            "expected_name": "Learn Python programming"
        },
        {
            "message": "What is machine learning?",
            "expected_name": "Machine learning"
        },
        {
            "message": "Can you help me with JavaScript arrays?",
            "expected_name": "Help me with JavaScript arrays"
        },
        {
            "message": "I need to understand Docker containers",
            "expected_name": "Understand Docker containers"
        },
        {
            "message": "Hello there!",
            "expected_name": "Hello there"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: '{test_case['message']}'")
        
        # Create new session
        try:
            response = requests.post(f"{BASE_URL}/api/sessions", 
                                   json={"name": "New Chat"})
            if response.status_code != 200:
                print(f"   ❌ Failed to create session")
                continue
            
            session_id = response.json()["id"]
            print(f"   ✅ Session created: {session_id[:8]}...")
            
            # Send first message
            response = requests.post(f"{BASE_URL}/api/sessions/{session_id}/chat",
                                   json={"message": test_case["message"]})
            
            if response.status_code != 200:
                print(f"   ❌ Failed to send message")
                continue
            
            print(f"   ✅ Message sent successfully")
            
            # Wait a moment for name update
            time.sleep(2)
            
            # Check updated session name
            response = requests.get(f"{BASE_URL}/api/sessions/{session_id}")
            if response.status_code == 200:
                session_data = response.json()
                actual_name = session_data["name"]
                print(f"   📝 Session name updated to: '{actual_name}'")
                
                # Check if it's no longer "New Chat"
                if actual_name != "New Chat":
                    print(f"   ✅ Name automatically generated!")
                else:
                    print(f"   ⚠️  Name not updated (still 'New Chat')")
            else:
                print(f"   ❌ Failed to get updated session")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print(f"\n🎯 How Session Naming Works:")
    print("1. Create session with default name 'New Chat'")
    print("2. Send first user message")
    print("3. System automatically generates name from message")
    print("4. Removes common words like 'how do i', 'what is', etc.")
    print("5. Capitalizes and truncates to 50 characters")
    print("6. Updates session name in database")
    
    print(f"\n📋 Examples of Name Generation:")
    print("• 'How do I learn Python?' → 'Learn Python'")
    print("• 'What is machine learning?' → 'Machine learning'")
    print("• 'Can you help me code?' → 'Help me code'")
    print("• 'I need help with Docker' → 'Help with Docker'")
    
    print(f"\n🌐 Test it yourself at: {BASE_URL}")
    print("Create a new chat and watch the name change after your first message!")

if __name__ == "__main__":
    test_session_naming()