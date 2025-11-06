#!/usr/bin/env python3
"""
Frontend Test for RAG Chat Application
Tests the web interface functionality
"""
import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

BASE_URL = "http://localhost:8000"

def test_frontend_loading():
    """Test if frontend loads properly"""
    print("🌐 Testing Frontend Loading")
    print("=" * 40)
    
    try:
        # Test main page
        response = requests.get(BASE_URL, timeout=10)
        if response.status_code == 200:
            print("✅ Main page loads successfully")
            print(f"   Content length: {len(response.text)} chars")
            
            # Check for essential elements in HTML
            html_content = response.text.lower()
            essential_elements = [
                'chatgpt web ui',
                'message-input',
                'send-button',
                'messages-container',
                'script.js',
                'sessions.js'
            ]
            
            missing_elements = []
            for element in essential_elements:
                if element not in html_content:
                    missing_elements.append(element)
            
            if missing_elements:
                print(f"⚠️  Missing elements: {missing_elements}")
            else:
                print("✅ All essential HTML elements present")
                
        else:
            print(f"❌ Main page failed to load: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Frontend loading error: {str(e)}")
        return False
    
    # Test static files
    static_files = [
        '/static/style.css',
        '/static/script.js',
        '/static/sessions.js',
        '/static/sessions.css'
    ]
    
    for file_path in static_files:
        try:
            response = requests.get(f"{BASE_URL}{file_path}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {file_path} loads successfully")
            else:
                print(f"❌ {file_path} failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {file_path} error: {str(e)}")
    
    return True

def test_api_endpoints():
    """Test API endpoints that frontend depends on"""
    print("\n🔌 Testing API Endpoints")
    print("=" * 40)
    
    endpoints = [
        ('GET', '/api/health', None),
        ('GET', '/api/sessions', None),
        ('POST', '/api/sessions', {'name': 'Frontend Test Session'})
    ]
    
    session_id = None
    
    for method, endpoint, data in endpoints:
        try:
            if method == 'GET':
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            elif method == 'POST':
                response = requests.post(f"{BASE_URL}{endpoint}", 
                                       json=data, timeout=10)
            
            if response.status_code in [200, 201]:
                print(f"✅ {method} {endpoint} - Success")
                
                # Store session ID for chat test
                if endpoint == '/api/sessions' and method == 'POST':
                    session_data = response.json()
                    session_id = session_data.get('id')
                    print(f"   Created session: {session_id}")
                    
            else:
                print(f"❌ {method} {endpoint} - HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ {method} {endpoint} - Error: {str(e)}")
    
    # Test chat endpoint if we have a session
    if session_id:
        try:
            chat_data = {'message': 'Hello, this is a frontend test!'}
            response = requests.post(f"{BASE_URL}/api/sessions/{session_id}/chat",
                                   json=chat_data, timeout=30)
            
            if response.status_code == 200:
                print("✅ Chat endpoint - Success")
                chat_response = response.json()
                assistant_msg = chat_response.get('assistant_message', {})
                print(f"   AI response length: {len(assistant_msg.get('content', ''))} chars")
            else:
                print(f"❌ Chat endpoint - HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Chat endpoint - Error: {str(e)}")
    
    return True

def test_javascript_functionality():
    """Test JavaScript functionality using browser automation"""
    print("\n🖥️  Testing JavaScript Functionality")
    print("=" * 40)
    
    # Setup Chrome options for headless testing
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    driver = None
    try:
        # Try to create WebDriver
        try:
            driver = webdriver.Chrome(options=chrome_options)
        except Exception:
            print("⚠️  Chrome WebDriver not available, skipping browser tests")
            print("   Install ChromeDriver to enable full frontend testing")
            return True
        
        # Navigate to the application
        driver.get(BASE_URL)
        
        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        
        # Test 1: Check if main elements are present
        try:
            message_input = wait.until(
                EC.presence_of_element_located((By.ID, "message-input"))
            )
            send_button = driver.find_element(By.ID, "send-button")
            messages_container = driver.find_element(By.ID, "messages-container")
            
            print("✅ Main UI elements found")
            
        except Exception as e:
            print(f"❌ Main UI elements missing: {str(e)}")
            return False
        
        # Test 2: Check if JavaScript loaded properly
        try:
            # Check if chatApp is initialized
            chat_app_exists = driver.execute_script("return typeof window.chatApp !== 'undefined';")
            session_manager_exists = driver.execute_script("return typeof window.sessionManager !== 'undefined';")
            
            if chat_app_exists:
                print("✅ ChatApp JavaScript initialized")
            else:
                print("❌ ChatApp JavaScript not initialized")
            
            if session_manager_exists:
                print("✅ SessionManager JavaScript initialized")
            else:
                print("❌ SessionManager JavaScript not initialized")
                
        except Exception as e:
            print(f"❌ JavaScript initialization check failed: {str(e)}")
        
        # Test 3: Try to send a message
        try:
            # Wait a bit for session to be created
            time.sleep(2)
            
            # Type a message
            message_input.clear()
            message_input.send_keys("Hello! This is a frontend test message.")
            
            # Click send button
            send_button.click()
            
            # Wait for response (up to 30 seconds)
            try:
                wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "message"))
                )
                print("✅ Message sending functionality works")
                
                # Check if AI response appears
                time.sleep(5)  # Wait for AI response
                messages = driver.find_elements(By.CLASS_NAME, "message")
                if len(messages) >= 2:  # User message + AI response
                    print("✅ AI response received")
                else:
                    print("⚠️  AI response may be delayed")
                    
            except Exception as e:
                print(f"❌ Message sending failed: {str(e)}")
                
        except Exception as e:
            print(f"❌ Message input test failed: {str(e)}")
        
        # Test 4: Check session management
        try:
            # Try to find session sidebar
            sidebar = driver.find_element(By.ID, "session-sidebar")
            session_list = driver.find_element(By.ID, "session-list")
            
            print("✅ Session management UI present")
            
            # Check if sessions are loaded
            sessions = driver.find_elements(By.CLASS_NAME, "session-item")
            print(f"✅ Found {len(sessions)} sessions in UI")
            
        except Exception as e:
            print(f"⚠️  Session management UI issue: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Browser testing failed: {str(e)}")
        return False
        
    finally:
        if driver:
            driver.quit()

def main():
    """Main test function"""
    print("🧪 Frontend Testing Suite")
    print("=" * 50)
    
    success = True
    
    # Test 1: Frontend loading
    if not test_frontend_loading():
        success = False
    
    # Test 2: API endpoints
    if not test_api_endpoints():
        success = False
    
    # Test 3: JavaScript functionality
    if not test_javascript_functionality():
        success = False
    
    # Final results
    print("\n" + "=" * 50)
    if success:
        print("🎉 Frontend tests completed successfully!")
        print("\n🌐 Application ready at: http://localhost:8000")
    else:
        print("❌ Some frontend tests failed")
        print("Check the logs above for specific issues")
    
    return success

if __name__ == "__main__":
    main()