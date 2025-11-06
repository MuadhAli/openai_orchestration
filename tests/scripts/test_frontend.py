#!/usr/bin/env python3
"""
Frontend Test - Simple Version
"""
import requests

BASE_URL = "http://localhost:8000"

def test_frontend():
    print("🌐 Testing Frontend")
    print("=" * 30)
    
    # Test main page
    try:
        response = requests.get(BASE_URL, timeout=10)
        print(f"Main page: HTTP {response.status_code}")
        
        if response.status_code == 200:
            html = response.text
            print(f"HTML length: {len(html)} chars")
            
            # Check key elements
            checks = [
                ('message-input', 'message-input' in html),
                ('send-button', 'send-button' in html),
                ('script.js', 'script.js' in html),
                ('sessions.js', 'sessions.js' in html)
            ]
            
            for name, found in checks:
                status = "✅" if found else "❌"
                print(f"{status} {name}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test static files
    files = ['/static/script.js', '/static/sessions.js', '/static/style.css']
    for file_path in files:
        try:
            response = requests.get(f"{BASE_URL}{file_path}", timeout=5)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} {file_path}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {file_path}: Error")

if __name__ == "__main__":
    test_frontend()