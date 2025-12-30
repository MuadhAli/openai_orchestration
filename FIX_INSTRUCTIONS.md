# Fix Instructions for Insurance Database Access

## Problem
The insurance tables exist in `insurance_db` database, but the code was trying to connect to `rag_chat_db`. Also, `chatuser` doesn't have access to `insurance_db`.

## Solution Applied
1. ✅ Updated `app/services/insurance_mcp_client.py` to use `insurance_db`
2. ✅ Updated `mcp_server/insurance_server.py` to use `insurance_db`
3. ⚠️ Need to grant permissions to `chatuser` for `insurance_db`

## Steps to Fix

### Step 1: Grant Access to insurance_db

Run this command to grant `chatuser` access to `insurance_db`:

```bash
docker exec -i rag_chat_mysql mysql -u root -prootpassword <<EOF
GRANT ALL PRIVILEGES ON insurance_db.* TO 'chatuser'@'%';
FLUSH PRIVILEGES;
EOF
```

### Step 2: Verify Access

Test that chatuser can access insurance_db:

```bash
docker exec -it rag_chat_mysql mysql -u chatuser -pchatpassword insurance_db -e "SHOW TABLES;"
```

You should see:
- Agents
- Customers
- Policies
- Claims
- Payments

### Step 3: Verify Data

Check that data exists:

```bash
docker exec -it rag_chat_mysql mysql -u chatuser -pchatpassword insurance_db -e "SELECT COUNT(*) FROM Agents; SELECT COUNT(*) FROM Customers; SELECT COUNT(*) FROM Policies;"
```

### Step 4: Restart Application (if needed)

If the app is running, restart it to pick up the new configuration:

```bash
docker compose restart chatgpt-web-ui
```

### Step 5: Test the Orchestrator

Try an insurance query like:
- "Show me all agents in Bangalore"
- "What policies does customer 101 have?"
- "List all pending claims"

## Alternative: Quick Fix Script

You can also use the provided script:

```bash
chmod +x scripts/setup_insurance_db.sh
./scripts/setup_insurance_db.sh
```

## Configuration

The code now uses environment variable `INSURANCE_DB_NAME` which defaults to `insurance_db`. You can override it in your `.env` file if needed:

```
INSURANCE_DB_NAME=insurance_db
```

