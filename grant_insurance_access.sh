#!/bin/bash
# Script to grant chatuser access to insurance_db

echo "=== Granting access to insurance_db for chatuser ==="
docker exec -i rag_chat_mysql mysql -u root -prootpassword <<EOF
GRANT ALL PRIVILEGES ON insurance_db.* TO 'chatuser'@'%';
FLUSH PRIVILEGES;
SELECT 'Access granted successfully!' AS Status;
EOF

echo ""
echo "=== Verifying access and checking tables ==="
docker exec -i rag_chat_mysql mysql -u chatuser -pchatpassword insurance_db <<EOF
SHOW TABLES;
SELECT '--- Agent Count ---' AS Info;
SELECT COUNT(*) AS AgentCount FROM Agents;
SELECT '--- Customer Count ---' AS Info;
SELECT COUNT(*) AS CustomerCount FROM Customers;
SELECT '--- Policy Count ---' AS Info;
SELECT COUNT(*) AS PolicyCount FROM Policies;
SELECT '--- Claim Count ---' AS Info;
SELECT COUNT(*) AS ClaimCount FROM Claims;
SELECT '--- Payment Count ---' AS Info;
SELECT COUNT(*) AS PaymentCount FROM Payments;
EOF

echo ""
echo "=== Setup complete! ==="
echo "The insurance MCP tools should now work properly."

