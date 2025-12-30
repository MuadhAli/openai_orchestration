-- Grant access to chatuser for insurance_db database
-- Run this script as root user: mysql -u root -p < grant_insurance_db_access.sql

GRANT ALL PRIVILEGES ON insurance_db.* TO 'chatuser'@'%';
FLUSH PRIVILEGES;

-- Verify the tables exist in insurance_db
USE insurance_db;
SHOW TABLES;

