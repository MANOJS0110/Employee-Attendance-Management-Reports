# Enterprise Employee Leave, Attendance & Workforce Analytics Management System

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://mysql.com)
[![Power BI](https://img.shields.io/badge/Power_BI-Desktop-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)](https://powerbi.microsoft.com)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)](https://getbootstrap.com)

---

## 📌 Project Overview
The **Enterprise Employee Leave, Attendance & Workforce Analytics Management System** is a production-ready, full-stack HR tech platform. It combines real-time digital attendance tracking, rule-based punctuality scoring, dynamic leave balances, multi-stage approval workflows, and executive analytics via **Chart.js**, **Excel**, **PDF**, and **Power BI**.

### 💼 Strong Resume Headline & Bullet Points
> **Project Title:** *Enterprise Employee Leave, Attendance and Workforce Analytics Management System*

- *Developed a full-stack Enterprise Workforce Management System with Python (Flask), MySQL, and Power BI, automating attendance logs, leave balances, and multi-tier approval workflows.*
- *Implemented real-time punch-clock logic with automated 15-minute grace period classification (Present, Late, Half-Day, Absent, On-Leave) and working hours computation.*
- *Architected a Star-Schema dimensional data model (Fact_Attendance, Fact_LeaveRequests, Dim_Employees, Dim_Date) with custom DAX measures for Power BI executive dashboards.*
- *Engineered an automated end-of-day batch processing job to dynamically detect and classify unrecorded staff absences while preserving approved leave records.*
- *Integrated automated multi-sheet styled Excel (`openpyxl`) and executive PDF (`reportlab`) report generators for C-level HR audits.*

---

## 🏗️ Architecture & Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | HTML5, CSS3, Bootstrap 5.3, JavaScript | Modern corporate UI, responsive sidebar, glassmorphic widgets |
| **Data Viz** | Chart.js 4.4 | Real-time trend line charts, department performance bars, leave doughnut |
| **Backend** | Python 3.14 / Flask 3.1 | Modular Blueprints, REST API endpoints, business rules engine |
| **Database** | MySQL Server 8.0 + PyMySQL | Relational schema, transactions, DictCursor connection management |
| **Security** | Werkzeug Hashing, Session Auth | Role-Based Access Control (`Admin`, `HR Manager`, `Employee`) |
| **Analytics & BI**| Power BI Desktop, DAX, Pandas | Star-Schema dimensional modeling, KPI cards, slicers |
| **Reporting** | OpenPyXL & ReportLab | Formatted multi-tab `.xlsx` workbooks and vector `.pdf` downloads |

---

## 🔐 Default Demo Accounts & Logins

The application features 1-click test credential fill buttons directly on the login screen:

| Role | Username | Password | Access Privileges |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `admin123` | Full control: Employee CRUD, Departments, User Roles, Audit Logs, Batch Jobs |
| **HR Manager** | `hr` | `hr123` | Leave Approvals/Rejections, Attendance Monitoring, Analytics, Exports |
| **Employee** | `emp101` | `emp123` | Digital Punch In/Out, Live Clock, Leave Applications, Balance Tracking |
| **Staff Members** | `emp102` to `emp112`| `emp123` | Team members across Engineering, HR, Finance, Operations, Marketing |

---

## 🚀 Key Modules & Business Logic

### 1. Punctuality & Working Hours Classification
- **Official Office Start:** `09:00 AM`
- **Grace Period Threshold:** `09:15 AM`
  - Punch before `09:15 AM` ➔ Classified as **ON TIME / PRESENT**.
  - Punch after `09:15 AM` ➔ Classified as **LATE ARRIVAL** (`is_late = TRUE`).
- **Working Hours Thresholds:**
  - $\ge 8.0 \text{ hours}$ ➔ **Full Day (PRESENT)**
  - $4.0 - 7.9 \text{ hours}$ ➔ **Half Day (HALF_DAY)**
  - $< 4.0 \text{ hours}$ ➔ **Short Day / Half Day**

### 2. Automated End-of-Day Absence Marking
- An automated batch background job sweeps all active employees at shift end:
  - If a staff member has an approved leave request for the date ➔ Recorded as **ON_LEAVE**.
  - If no check-in exists and no approved leave ➔ Recorded as **ABSENT**.

### 3. Dynamic Leave Management & Deductions
- **Annual Allowance:** Casual Leave (12), Sick Leave (10), Earned Leave (15), Optional Holiday (3).
- **Date Calculation:** Automatically excludes Saturdays, Sundays, and public holidays from applied days.
- **Approval Workflow:**
  - When an HR manager clicks **Approve**, the corresponding days are atomically deducted from `leave_balance`, and the attendance records for those dates are populated with `status = 'ON_LEAVE'`.
  - Rejection requires an HR remark and preserves the employee's balance.

### 4. Audit Trail & Compliance
- Every administrative action, login, employee creation, and leave approval is recorded with user ID, role, client IP address, and timestamp in `audit_logs`.

---

## 📊 Power BI & Business Intelligence Integration

The project includes ready-to-load datasets in `powerbi/data/`:
- `Dim_Departments.csv`
- `Dim_Employees.csv`
- `Fact_Attendance.csv` (350+ records across September & October)
- `Fact_LeaveRequests.csv`
- `Fact_LeaveBalance.csv`
- `Dim_Date.csv` (Calendar dimension for Time Intelligence)

### Core DAX Measures Included
```dax
-- Attendance Percentage
Attendance % = 
DIVIDE(
    CALCULATE(COUNTROWS(Fact_Attendance), Fact_Attendance[status] IN {"PRESENT", "LATE", "HALF_DAY"}),
    COUNTROWS(Fact_Attendance),
    0
)

-- Late Arrival Rate
Late Arrival Rate = 
DIVIDE(
    CALCULATE(COUNTROWS(Fact_Attendance), Fact_Attendance[is_late] = TRUE()),
    CALCULATE(COUNTROWS(Fact_Attendance), Fact_Attendance[status] IN {"PRESENT", "LATE", "HALF_DAY"}),
    0
)

-- Average Daily Hours
Avg Daily Working Hours = 
AVERAGEX(
    FILTER(Fact_Attendance, Fact_Attendance[working_hours] > 0),
    Fact_Attendance[working_hours]
)
```

See [PowerBI_Setup_Guide.md](file:///c:/Users/DELL/Downloads/Employee%20Attendance%20Management%20Reports/powerbi/PowerBI_Setup_Guide.md) for direct MySQL connector steps and dashboard wireframes.

---

## 🛠️ Installation & Setup Guide

### 1. Prerequisites
- **Python 3.11+** installed
- **MySQL Server 8.0+** running on `localhost:3306`

### 2. Configure Database Credentials
Database configuration is set in [config.py](file:///c:/Users/DELL/Downloads/Employee%20Attendance%20Management%20Reports/config.py):
```python
DB_HOST = 'localhost'
DB_PORT = 3306
DB_USER = 'root'
DB_PASSWORD = 'YOUR_MYSQL_PASSWORD'
DB_NAME = 'employee_attendance_db'
```

### 3. Initialize & Seed Database
Execute the automated database seed script:
```powershell
py database/seed_data.py
```
This initializes all 8 tables, departments, 13 employees, hashed credentials, leave balances, 350+ attendance records, and audit logs.

### 4. Run the Web Application
Launch the Flask development server:
```powershell
py run.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 📡 REST API Reference

| Method | Endpoint | Description | Access |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/login` | Authenticate user & start session | Public |
| `GET` | `/api/auth/logout` | Terminate session | Authenticated |
| `POST` | `/api/attendance/check-in` | Punch in for today | Employee |
| `POST` | `/api/attendance/check-out` | Punch out & calculate hours | Employee |
| `GET` | `/api/attendance/today` | Current employee today's status | Employee |
| `GET` | `/api/attendance/today-summary` | Real-time headcount & punch logs | HR, Admin |
| `POST` | `/api/attendance/batch-absent` | Trigger end-of-day absence job | HR, Admin |
| `POST` | `/api/leaves/apply` | Submit leave request with balance check | Employee |
| `GET` | `/api/leaves/pending` | List pending requests | HR, Admin |
| `POST` | `/api/leaves/<id>/approve` | Approve leave & auto-update attendance | HR, Admin |
| `POST` | `/api/leaves/<id>/reject` | Reject leave request | HR, Admin |
| `GET` | `/api/employees` | List/search staff with department filters | Authenticated |
| `POST` | `/api/employees` | Enroll new staff & provision login account | Admin |
| `GET` | `/reports/excel/monthly` | Download styled corporate `.xlsx` report | Authenticated |
| `GET` | `/reports/pdf/monthly` | Download executive summary `.pdf` report | Authenticated |
| `POST` | `/api/powerbi/export-sync` | Refresh star-schema CSV datasets | HR, Admin |
