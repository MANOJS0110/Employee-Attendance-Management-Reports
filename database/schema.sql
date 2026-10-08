-- ====================================================================
-- Employee Leave & Attendance Management System
-- Database Schema for MySQL 8.0+
-- Database: employee_attendance_db
-- ====================================================================

CREATE DATABASE IF NOT EXISTS employee_attendance_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE employee_attendance_db;

-- 1. Departments Table
CREATE TABLE IF NOT EXISTS departments (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. Employees Table
CREATE TABLE IF NOT EXISTS employees (
    employee_id VARCHAR(30) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    phone VARCHAR(20),
    department_id INT,
    designation VARCHAR(100) NOT NULL,
    joining_date DATE NOT NULL,
    status ENUM('ACTIVE', 'INACTIVE', 'ON_LEAVE', 'TERMINATED') DEFAULT 'ACTIVE',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 3. Users Table (Role-based access: admin, hr, employee)
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(30) UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'hr', 'employee') NOT NULL DEFAULT 'employee',
    is_active BOOLEAN DEFAULT TRUE,
    last_login DATETIME NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 4. Leave Balance Table
CREATE TABLE IF NOT EXISTS leave_balance (
    balance_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(30) NOT NULL UNIQUE,
    casual_leave DECIMAL(4,1) DEFAULT 12.0,
    sick_leave DECIMAL(4,1) DEFAULT 10.0,
    earned_leave DECIMAL(4,1) DEFAULT 15.0,
    optional_leave DECIMAL(4,1) DEFAULT 3.0,
    year INT NOT NULL DEFAULT 2026,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 5. Attendance Table
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(30) NOT NULL,
    date DATE NOT NULL,
    check_in TIME NULL,
    check_out TIME NULL,
    working_hours DECIMAL(5,2) DEFAULT 0.00,
    status ENUM('PRESENT', 'ABSENT', 'LATE', 'HALF_DAY', 'ON_LEAVE') NOT NULL DEFAULT 'PRESENT',
    is_late BOOLEAN DEFAULT FALSE,
    remarks VARCHAR(255) NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_emp_date (employee_id, date),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE,
    INDEX idx_attendance_date (date),
    INDEX idx_attendance_status (status)
) ENGINE=InnoDB;

-- 6. Leave Requests Table
CREATE TABLE IF NOT EXISTS leave_requests (
    leave_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(30) NOT NULL,
    leave_type ENUM('Casual Leave', 'Sick Leave', 'Earned Leave', 'Optional Holiday') NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_days DECIMAL(4,1) NOT NULL DEFAULT 1.0,
    reason TEXT NOT NULL,
    status ENUM('PENDING', 'APPROVED', 'REJECTED') DEFAULT 'PENDING',
    approved_by VARCHAR(30) NULL,
    admin_remarks TEXT NULL,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    action_at DATETIME NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE,
    FOREIGN KEY (approved_by) REFERENCES employees(employee_id) ON DELETE SET NULL,
    INDEX idx_leave_status (status),
    INDEX idx_leave_dates (start_date, end_date)
) ENGINE=InnoDB;

-- 7. Audit Logs Table
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    username VARCHAR(50) NOT NULL,
    role VARCHAR(20) NOT NULL,
    action VARCHAR(100) NOT NULL,
    ip_address VARCHAR(50) DEFAULT '127.0.0.1',
    description TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_audit_created (created_at)
) ENGINE=InnoDB;

-- 8. Holidays Table
CREATE TABLE IF NOT EXISTS holidays (
    holiday_id INT AUTO_INCREMENT PRIMARY KEY,
    holiday_name VARCHAR(100) NOT NULL,
    holiday_date DATE NOT NULL UNIQUE,
    holiday_type ENUM('PUBLIC', 'REGIONAL', 'RESTRICTED') DEFAULT 'PUBLIC'
) ENGINE=InnoDB;
