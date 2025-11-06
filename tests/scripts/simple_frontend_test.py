#!/usr/bin/env python3
"""
Simple Frontend Test for RAG Chat Application
Tests the web interface without browser automation
"""
import requests
import re

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
            html_content = response.text
            essential_elements = {
                'ChatGPT Web UI': 'title' in html_content.lower() and 'chatgpt' in html_content.lower(),
                'Message Input': 'message-input' in html_content,
                'Send Button': 'send-button' in html_content,
                'Messages Container': 'messages-container' in html_content,
                'Script.js': 'script.js' in html_content,
                'Sessions.js': 'sessions.js' in html_content,
                'CSS Styles': 'style.css' in html_content,
                'Session Sidebar': 'session-sidebar' in html_content
            }
            
            missing_elements = []
            for element, present in essential_elements.items():
                if present:
                    print(f"   ✅ {element}")
                else:
                    print(f"   ❌ {element}")
                    missing_elements.append(element)
            
            if not missing_elements:
                print("✅ All essential HTML elements present")
                return True
            else:
                print(f"⚠️  Missing elements: {missing_elements}")
                return False
   