-- Grant access to insurance_db for chatuser
-- This runs automatically after database initialization

GRANT ALL PRIVILEGES ON insurance_db.* TO 'chatuser'@'%';
FLUSH PRIVILEGES;

