#!/usr/bin/env python3
"""
Test New Frontend Design
"""
import requests

BASE_URL = "http://localhost:8000"

def test_new_frontend():
    print("🎨 Testing New Frontend Design")
    print("=" * 40)
    
    # Test main page
    try:
        response = requests.get(BASE_URL, timeout=10)
        if response.status_code == 200:
            html = response.text
            print("✅ Main page loads")
            
            # Check for new elements
            new_elements = [
                'new-style.css',
                'new-script.js',
                'messages-area',
                'chat-form',
                'message-input',
                'send-btn',
                'char-counter'
            ]
            
            for element in new_elements:
                if element in html:
                    print(f"   ✅ {element}")
                else:
                    print(f"   ❌ {element}")
        else:
            print(f"❌ Main page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test CSS file
    try:
        response = requests.get(f"{BASE_URL}/static/new-style.css", timeout=5)
        if response.status_code == 200:
            print(f"✅ CSS file loads ({len(response.text)} chars)")
        else:
            print(f"❌ CSS file failed: {response.status_code}")
    except Exception as e:
        print(f"❌ CSS error: {e}")
    
    # Test JS file
    try:
        response = requests.get(f"{BASE_URL}/static/new-script.js", timeout=5)
        if response.status_code == 200:
            print(f"✅ JavaScript file loads ({len(response.text)} chars)")
        else:
            print(f"❌ JavaScript file failed: {response.status_code}")
    except Exception as e:
        print(f"❌ JavaScript error: {e}")
    
    print("\n🎯 New Frontend Features:")
    print("- Clean, modern ChatGPT-like design")
    print("- Dark sidebar with chat history")
    print("- Message bubbles with avatars")
    print("- Responsive mobile design")
    print("- Typing indicators")
    print("- Auto-resizing input")
    print("- Character counter")
    print("- Smooth animations")
    
    print(f"\n🌐 Open in browser: {BASE_URL}")
    print("\n📱 What to expect:")
    print("- Dark sidebar on the left with chat history")
    print("- Clean white chat area")
    print("- Message bubbles (green for you, gray for AI)")
    print("- Input box at the bottom with send button")
    print("- Character counter updates as you type")
    print("- Messages appear immediately when sent")
    
    return True

if __name__ == "__main__":
    test_new_frontend()