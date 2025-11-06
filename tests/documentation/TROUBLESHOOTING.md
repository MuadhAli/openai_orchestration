# Troubleshooting Guide

## 🔧 If You Can't Test the Application

### Step 1: Check Docker Containers
```bash
wsl docker compose ps
```
**Expected:** Both containers should show "healthy" status

If containers are not running:
```bash
wsl docker compose up --build -d
```

### Step 2: Test Backend API
```bash
python quick_test.py
```
**Expected:** All 3 tests should pass

### Step 3: Test Frontend in Browser

#### Option A: Use Test Page
1. Open `browser_test.html` in your browser
2. Click the test buttons
3. All tests should show ✅

#### Option B: Direct Browser Test
1. Open http://localhost:8000 in your browser
2. You should see the ChatGPT Web UI
3. Try typing a message and sending it

### Step 4: Check Browser Console
1. Press F12 in your browser
2. Go to Console tab
3. Look for errors (red text)
4. Should see: "Session management script loaded"

## 🚨 Common Issues & Solutions

### Issue: "Cannot reach app"
**Solution:**
```bash
# Check if containers are running
wsl docker compose ps

# If not running, start them
wsl docker compose up --build -d

# Wait 30 seconds for startup
```

### Issue: "Chat failed" or "Session creation failed"
**Solution:**
```bash
# Check container logs
wsl docker compose logs chatgpt_web_ui

# Look for errors in the logs
```

### Issue: Frontend loads but doesn't work
**Solution:**
1. Check browser console (F12)
2. Look for JavaScript errors
3. Try refreshing the page
4. Clear browser cache

### Issue: "New Chat" button doesn't work
**Solution:**
- Both "New Chat" buttons now do the same thing
- They create a new chat session
- Check browser console for errors

## 📋 Quick Verification Checklist

- [ ] Docker containers are running and healthy
- [ ] `python quick_test.py` passes all tests
- [ ] http://localhost:8000 loads in browser
- [ ] Can type and send messages
- [ ] Can create new chats
- [ ] Can switch between chats
- [ ] Browser console shows no errors

## 🆘 If Nothing Works

1. **Restart everything:**
   ```bash
   wsl docker compose down
   wsl docker compose up --build -d
   ```

2. **Wait 1-2 minutes** for full startup

3. **Run quick test:**
   ```bash
   python quick_test.py
   ```

4. **Open browser test:**
   - Open `browser_test.html` in browser
   - All tests should pass

## ✅ What Should Work Now

### Frontend Changes Made:
- ✅ "New Chat" and "New Session" are now the same thing
- ✅ Both buttons create a new chat
- ✅ Sidebar now says "Chats" instead of "Sessions"
- ✅ Simplified terminology throughout
- ✅ Fixed JavaScript integration

### Expected Behavior:
- ✅ Click "New Chat" → Creates new chat
- ✅ Click "+" in sidebar → Creates new chat  
- ✅ Both buttons do exactly the same thing
- ✅ Chat history persists when switching
- ✅ Can delete chats with "×" button

## 🌐 Access Points

- **Main App:** http://localhost:8000
- **API Health:** http://localhost:8000/api/health
- **Test Page:** Open `browser_test.html` in browser