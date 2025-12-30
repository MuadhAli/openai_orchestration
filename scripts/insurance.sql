
CREATE DATABASE IF NOT EXISTS insurance_db;
USE insurance_db;

CREATE TABLE Agents (
    agent_id INT PRIMARY KEY,
    agent_name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    region VARCHAR(50)
);

CREATE TABLE Customers (
    customer_id INT PRIMARY KEY,
    full_name VARCHAR(150),
    dob DATE,
    email VARCHAR(120),
    phone VARCHAR(20),
    address TEXT,
    agent_id INT,
    FOREIGN KEY (agent_id) REFERENCES Agents(agent_id)
);

CREATE TABLE Policies (
    policy_id INT PRIMARY KEY,
    customer_id INT,
    policy_type VARCHAR(50),
    start_date DATE,
    end_date DATE,
    premium_amount DECIMAL(10,2),
    coverage_amount DECIMAL(12,2),
    status VARCHAR(20),
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
);

CREATE TABLE Claims (
    claim_id INT PRIMARY KEY,
    policy_id INT,
    claim_date DATE,
    claim_amount DECIMAL(12,2),
    status VARCHAR(20),
    description TEXT,
    FOREIGN KEY (policy_id) REFERENCES Policies(policy_id)
);

CREATE TABLE Payments (
    payment_id INT PRIMARY KEY,
    policy_id INT,
    payment_date DATE,
    amount DECIMAL(10,2),
    method VARCHAR(20),
    status VARCHAR(20),
    FOREIGN KEY (policy_id) REFERENCES Policies(policy_id)
);

INSERT INTO Agents VALUES
(1, 'Rahul Verma', 'rahul@novigo.com', '+91-9999988888', 'Bangalore'),
(2, 'Fatima Ali', 'fatima@novigo.com', '+91-8888877777', 'Mumbai'),
(3, 'Aman Singh', 'aman.singh@novigo.com', '+91-7777766666', 'Delhi'),
(4, 'Mohammed Yusuf', 'yusuf@novigo.com', '+91-6666655555', 'Hyderabad'),
(5, 'Priya Nair', 'priya.nair@novigo.com', '+91-9877001100', 'Kochi'),
(6, 'James Thomas', 'james@novigo.com', '+91-9012345678', 'Chennai'),
(7, 'Sana Rahman', 'sana@novigo.com', '+91-9988776655', 'Pune'),
(8, 'Krishna Rao', 'krishna@novigo.com', '+91-9090909090', 'Vizag'),
(9, 'Aisha Khan', 'aisha@novigo.com', '+91-7007007007', 'Lucknow'),
(10, 'Rohit Shetty', 'rohit@novigo.com', '+91-8800440022', 'Goa');

INSERT INTO Customers VALUES
(101, 'John Mathew', '1985-02-10', 'john.mathew@example.com', '9876543210', 'Kochi, Kerala', 1),
(102, 'Sara Ibrahim', '1990-08-15', 'sara.ibrahim@example.com', '9822334455', 'Jeddah, Saudi Arabia', 2),
(103, 'Rahim Shaikh', '1988-01-22', 'rahim.shaikh@example.com', '9900112233', 'Mumbai, India', 3),
(104, 'Angel Thomas', '1995-11-30', 'angel.thomas@example.com', '8811223344', 'Chennai, India', 4),
(105, 'Sameer Patel', '1992-06-18', 'sameer.patel@example.com', '9911991199', 'Ahmedabad, India', 5),
(106, 'Fatima Noor', '1993-03-10', 'fatima.noor@example.com', '9080706050', 'Dubai, UAE', 6),
(107, 'Rakesh Kumar', '1986-12-05', 'rakesh.kumar@example.com', '9090908080', 'Delhi, India', 7),
(108, 'Nisha Meena', '1997-09-22', 'nisha.meena@example.com', '9812312312', 'Jaipur, India', 8),
(109, 'Imran Malik', '1989-05-11', 'imran.malik@example.com', '9888897777', 'Hyderabad, India', 9),
(110, 'Olivia George', '1998-07-07', 'olivia.george@example.com', '9712345678', 'Goa, India', 10);

INSERT INTO Policies VALUES
(1001, 101, 'Health Insurance', '2024-01-01', '2025-01-01', 12000.00, 500000.00, 'Active'),
(1002, 102, 'Car Insurance', '2024-05-01', '2025-05-01', 8000.00, 300000.00, 'Active'),
(1003, 103, 'Life Insurance', '2023-03-10', '2043-03-10', 15000.00, 2000000.00, 'Active'),
(1004, 104, 'Bike Insurance', '2024-02-01', '2025-02-01', 2500.00, 100000.00, 'Expired'),
(1005, 105, 'Travel Insurance', '2024-10-15', '2025-10-15', 5000.00, 700000.00, 'Active'),
(1006, 106, 'Home Insurance', '2023-08-20', '2024-08-20', 9000.00, 1500000.00, 'Expired'),
(1007, 107, 'Health Insurance', '2024-04-12', '2025-04-12', 14000.00, 600000.00, 'Active'),
(1008, 108, 'Car Insurance', '2024-06-05', '2025-06-05', 7500.00, 250000.00, 'Pending'),
(1009, 109, 'Life Insurance', '2022-01-01', '2042-01-01', 20000.00, 3000000.00, 'Active'),
(1010, 110, 'Travel Insurance', '2024-11-01', '2025-11-01', 4500.00, 500000.00, 'Active');

INSERT INTO Claims VALUES
(5001, 1001, '2024-03-12', 45000.00, 'Approved', 'Hospitalization due to accident'),
(5002, 1002, '2024-06-20', 8000.00, 'Pending', 'Rear bumper damage'),
(5003, 1003, '2024-01-15', 100000.00, 'Rejected', 'Incorrect documentation'),
(5004, 1004, '2024-04-10', 3000.00, 'Approved', 'Minor scratches'),
(5005, 1005, '2024-12-22', 25000.00, 'Pending', 'Flight delay compensation'),
(5006, 1006, '2024-02-13', 90000.00, 'Approved', 'Water leakage damage'),
(5007, 1007, '2024-05-18', 55000.00, 'Approved', 'Surgery coverage'),
(5008, 1008, '2024-07-25', 12000.00, 'Pending', 'Front glass replacement'),
(5009, 1009, '2023-11-30', 200000.00, 'Approved', 'Death claim processing'),
(5010, 1010, '2024-12-05', 15000.00, 'Pending', 'Lost baggage compensation');

INSERT INTO Payments VALUES
(9001, 1001, '2024-01-02', 12000.00, 'Online', 'Paid'),
(9002, 1002, '2024-05-03', 8000.00, 'Card', 'Paid'),
(9003, 1003, '2023-03-10', 15000.00, 'Online', 'Paid'),
(9004, 1004, '2024-02-02', 2500.00, 'Cash', 'Paid'),
(9005, 1005, '2024-10-16', 5000.00, 'UPI', 'Paid'),
(9006, 1006, '2023-08-22', 9000.00, 'Card', 'Paid'),
(9007, 1007, '2024-04-12', 14000.00, 'Online', 'Paid'),
(9008, 1008, '2024-06-06', 7500.00, 'Card', 'Pending'),
(9009, 1009, '2022-01-01', 20000.00, 'Online', 'Paid'),
(9010, 1010, '2024-11-02', 4500.00, 'UPI', 'Paid');
