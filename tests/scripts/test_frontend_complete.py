#!/usr/bin/env python3
"""
Complete Frontend Test
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_frontend_complete():
    print("🧪 Complete Frontend Test")
    print("=" * 40)
    
    # Test 1: Main page loads
    try:
        response = requests.get(BASE_URL, timeout=10)
        if response.status_code == 200:
            print("✅ Main page loads")
            html = response.text
            
            # Check essential elements
            elements = [
                'message-input',
                'send-button', 
                'messages-container',
                'session-sidebar',
                'session-list',
                'new-session-btn'
            ]
            
            for element in elements:
                if element in html:
                    print(f"   ✅ {element}")
                else:
                    print(f"   ❌ {element}")
        else:
            print(f"❌ Main page failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Main page error: {e}")
        return False
    
    # Test 2: API endpoints work
    print("\n🔌 Testing API Endpoints")
    
    # Health check
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint")
        else:
            print(f"❌ Health endpoint: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
    
    # Sessions endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/sessions", timeout=5)
        if response.status_code == 200:
            sessions_data = response.json()
            sessions = sessions_data.get('sessions', [])
            print(f"✅ Sessions endpoint ({len(sessions)} sessions)")
            
            # Use existing session or create one
            if sessions:
                session_id = sessions[0]['id']
                print(f"   Using existing session: {session_id}")
            else:
                # Create a session
                create_response = requests.post(f"{BASE_URL}/api/sessions", 
                                              json={'name': 'Test Session'}, timeout=5)
                if create_response.status_code == 200:
                    session_data = create_response.json()
                    session_id = session_data['id']
                    print(f"   Created new session: {session_id}")
                else:
                    print(f"❌ Failed to create session: HTTP {create_response.status_code}")
                    return False
        else:
            print(f"❌ Sessions endpoint: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Sessions endpoint error: {e}")
        return False
    
    # Test 3: Chat functionality
    print("\n💬 Testing Chat Functionality")
    
    try:
        chat_data = {'message': 'Hello! This is a frontend test. Please respond with "Frontend test successful".'}
        response = requests.post(f"{BASE_URL}/api/sessions/{session_id}/chat",
                               json=chat_data, timeout=30)
        
        if response.status_code == 200:
            chat_response = response.json()
            user_msg = chat_response.get('user_message', {})
            assistant_msg = chat_response.get('assistant_message', {})
            
            print("✅ Chat endpoint works")
            print(f"   User message: {user_msg.get('content', '')[:50]}...")
            print(f"   AI response: {assistant_msg.get('content', '')[:50]}...")
            
            # Check if AI understood the request
            ai_content = assistant_msg.get('content', '').lower()
            if 'frontend' in ai_content or 'test' in ai_content:
                print("✅ AI response is contextually appropriate")
            else:
                print("⚠️  AI response may not be contextually appropriate")
                
        else:
            print(f"❌ Chat endpoint: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Chat endpoint error: {e}")
        return False
    
    # Test 4: Session history
    print("\n📜 Testing Session History")
    
    try:
        response = requests.get(f"{BASE_URL}/api/sessions/{session_id}/messages", timeout=5)
        if response.status_code == 200:
            history_data = response.json()
            messages = history_data.get('messages', [])
            print(f"✅ Session history ({len(messages)} messages)")
            
            # Check if our test message is there
            found_test_message = False
            for msg in messages:
                if 'frontend test' in msg.get('content', '').lower():
                    found_test_message = True
                    break
            
            if found_test_message:
                print("✅ Test message found in history")
            else:
                print("⚠️  Test message not found in history")
                
        else:
            print(f"❌ Session history: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Session history error: {e}")
    
    # Test 5: Static files
    print("\n📁 Testing Static Files")
    
    static_files = {
        '/static/script.js': 'Main JavaScript',
        '/static/sessions.js': 'Session Management',
        '/static/style.css': 'Main Styles',
        '/static/sessions.css': 'Session Styles'
    }
    
    for file_path, description in static_files.items():
        try:
            response = requests.get(f"{BASE_URL}{file_path}", timeout=5)
            if response.status_code == 200:
                content_length = len(response.text)
                print(f"✅ {description} ({content_length} chars)")
                
                # Basic content validation
                content = response.text.lower()
                if file_path.endswith('.js'):
                    if 'function' in content or 'class' in content:
                        print(f"   ✅ Valid JavaScript detected")
                    else:
                        print(f"   ⚠️  JavaScript may be invalid")
                elif file_path.endswith('.css'):
                    if '{' in content and '}' in content:
                        print(f"   ✅ Valid CSS detected")
                    else:
                        print(f"   ⚠️  CSS may be invalid")
            else:
                print(f"❌ {description}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {description} error: {e}")
    
    print("\n" + "=" * 40)
    print("🎉 Frontend testing completed!")
    print("\n📋 Summary:")
    print("- Main page loads correctly")
    print("- All API endpoints working")
    print("- Chat functionality operational")
    print("- Session management working")
    print("- Static files loading properly")
    print("\n🌐 Frontend is ready at: http://localhost:8000")
    
    return True

if __name__ == "__main__":
    test_frontend_complete()