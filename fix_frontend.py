#!/usr/bin/env python3
"""
Frontend Fix - Diagnose and fix frontend issues
"""
import requests
import re

BASE_URL = "http://localhost:8000"

def diagnose_frontend():
    print("🔍 Diagnosing Frontend Issues")
    print("=" * 40)
    
    # Get the main page
    try:
        response = requests.get(BASE_URL, timeout=10)
        if response.status_code != 200:
            print(f"❌ Main page not loading: {response.status_code}")
            return False
        
        html = response.text
        print("✅ Main page loads")
        
        # Check for essential elements
        elements_to_check = [
            ('message-input', r'id=["\']message-input["\']'),
            ('send-button', r'id=["\']send-button["\']'),
            ('char-counter', r'id=["\']char-counter["\']'),
            ('chat-form', r'id=["\']chat-form["\']'),
            ('messages-container', r'id=["\']messages-container["\']')
        ]
        
        missing_elements = []
        for name, pattern in elements_to_check:
            if re.search(pattern, html):
                print(f"✅ Found: {name}")
            else:
                print(f"❌ Missing: {name}")
                missing_elements.append(name)
        
        if missing_elements:
            print(f"\n⚠️  Missing elements: {missing_elements}")
            return False
        
        # Check JavaScript files
        js_files = ['/static/script.js', '/static/sessions.js']
        for js_file in js_files:
            try:
                js_response = requests.get(f"{BASE_URL}{js_file}", timeout=5)
                if js_response.status_code == 200:
                    print(f"✅ {js_file} loads ({len(js_response.text)} chars)")
                    
                    # Check for syntax errors (basic)
                    js_content = js_response.text
                    if 'class ChatApp' in js_content:
                        print(f"   ✅ ChatApp class found")
                    if 'addEventListener' in js_content:
                        print(f"   ✅ Event listeners found")
                else:
                    print(f"❌ {js_file} failed: {js_response.status_code}")
            except Exception as e:
                print(f"❌ {js_file} error: {e}")
        
        print("\n📋 Recommendations:")
        print("1. Open browser console (F12) and check for JavaScript errors")
        print("2. Try the minimal test: open test_minimal.html in browser")
        print("3. Check if character counter updates when typing")
        print("4. Verify send button enables/disables with text input")
        
        return True
        
    except Exception as e:
        print(f"❌ Error diagnosing frontend: {e}")
        return False

def create_simple_fix():
    print("\n🔧 Creating Simple Fix")
    print("=" * 40)
    
    # Create a simple JavaScript fix
    fix_js = """
// Simple fix for frontend issues
console.log('Loading frontend fix...');

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM ready, applying fixes...');
    
    // Find elements
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const charCounter = document.getElementById('char-counter');
    const chatForm = document.getElementById('chat-form');
    
    if (!messageInput) {
        console.error('Message input not found!');
        return;
    }
    
    console.log('✅ Elements found, binding events...');
    
    // Update character counter
    function updateCounter() {
        if (charCounter && messageInput) {
            const length = messageInput.value.length;
            charCounter.textContent = length + ' / 4000';
        }
    }
    
    // Update send button
    function updateButton() {
        if (sendButton && messageInput) {
            sendButton.disabled = messageInput.value.trim().length === 0;
        }
    }
    
    // Bind input events
    messageInput.addEventListener('input', function() {
        updateCounter();
        updateButton();
    });
    
    // Initial update
    updateCounter();
    updateButton();
    
    console.log('✅ Frontend fix applied successfully');
});
"""
    
    with open('frontend_fix.js', 'w') as f:
        f.write(fix_js)
    
    print("✅ Created frontend_fix.js")
    print("   Add this to your HTML: <script src='frontend_fix.js'></script>")

if __name__ == "__main__":
    if diagnose_frontend():
        create_simple_fix()
        print("\n🎯 Next Steps:")
        print("1. Open test_minimal.html to test basic functionality")
        print("2. Check browser console for errors")
        print("3. Try typing in the input field")
        print("4. Verify character counter updates")
    else:
        print("\n❌ Frontend diagnosis failed")