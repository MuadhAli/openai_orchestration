#!/bin/bash
# Setup script to grant permissions for insurance_db to chatuser
# Run this from your host machine

echo "Granting access to insurance_db for chatuser..."
docker exec -i rag_chat_mysql mysql -u root -prootpassword <<EOF
GRANT ALL PRIVILEGES ON insurance_db.* TO 'chatuser'@'%';
FLUSH PRIVILEGES;
SELECT 'Access granted successfully!' AS Status;
EOF

echo ""
echo "Verifying insurance_db tables..."
docker exec -i rag_chat_mysql mysql -u chatuser -pchatpassword insurance_db <<EOF
SHOW TABLES;
SELECT COUNT(*) AS AgentCount FROM Agents;
SELECT COUNT(*) AS CustomerCount FROM Customers;
SELECT COUNT(*) AS PolicyCount FROM Policies;
SELECT COUNT(*) AS ClaimCount FROM Claims;
SELECT COUNT(*) AS PaymentCount FROM Payments;
EOF

echo ""
echo "Setup complete!"

