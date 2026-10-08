"""
Seed Data Generator for Employee Leave & Attendance Management System
Populates realistic departments, employees, users, leave balances,
historical attendance records (with realistic times, late arrivals, half-days),
leave requests, holidays, and audit logs.
"""

import sys
import os
from datetime import datetime, date, time, timedelta
import random
from werkzeug.security import generate_password_hash

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db import get_db_cursor

def seed():
    print("Starting database seeding...")
    with get_db_cursor(commit=True) as cursor:
        # Disable foreign key checks for clean reload if needed
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("TRUNCATE TABLE audit_logs;")
        cursor.execute("TRUNCATE TABLE leave_requests;")
        cursor.execute("TRUNCATE TABLE attendance;")
        cursor.execute("TRUNCATE TABLE leave_balance;")
        cursor.execute("TRUNCATE TABLE users;")
        cursor.execute("TRUNCATE TABLE employees;")
        cursor.execute("TRUNCATE TABLE departments;")
        cursor.execute("TRUNCATE TABLE holidays;")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

        # 1. Insert Departments
        departments = [
            (1, "Engineering & Technology", "Software architecture, cloud infrastructure, QA, and IT support"),
            (2, "Human Resources", "People operations, talent acquisition, payroll, and employee relations"),
            (3, "Finance & Accounts", "Corporate budgeting, taxation, audit, and financial accounting"),
            (4, "Operations & Logistics", "Field workflows, enterprise operations, supply chain, and facilities"),
            (5, "Marketing & Growth", "Digital brand marketing, product growth, SEO, and client relations")
        ]
        cursor.executemany(
            "INSERT INTO departments (department_id, department_name, description) VALUES (%s, %s, %s);",
            departments
        )
        print("[OK] Inserted 5 departments.")

        # 2. Insert Holidays for 2026
        holidays_data = [
            ("New Year's Day", date(2026, 1, 1), "PUBLIC"),
            ("Republic Day", date(2026, 1, 26), "PUBLIC"),
            ("Holi Festival", date(2026, 3, 25), "PUBLIC"),
            ("May Day", date(2026, 5, 1), "PUBLIC"),
            ("Independence Day", date(2026, 8, 15), "PUBLIC"),
            ("Gandhi Jayanti", date(2026, 10, 2), "PUBLIC"),
            ("Dussehra", date(2026, 10, 20), "PUBLIC"),
            ("Diwali (Deepavali)", date(2026, 11, 8), "PUBLIC"),
            ("Christmas Day", date(2026, 12, 25), "PUBLIC")
        ]
        cursor.executemany(
            "INSERT INTO holidays (holiday_name, holiday_date, holiday_type) VALUES (%s, %s, %s);",
            holidays_data
        )
        holiday_dates = {h[1] for h in holidays_data}
        print("[OK] Inserted 9 public holidays.")

        # 3. Insert Employees
        employees_data = [
            ("EMP100", "Rajesh Kumar", "rajesh.admin@enterprise.com", "+91 98765 43200", 2, "Director & Chief Admin", date(2022, 1, 10), "ACTIVE"),
            ("EMP101", "Jestin Roy", "jestin.roy@enterprise.com", "+91 98765 43210", 1, "Lead Full-Stack Engineer", date(2023, 3, 1), "ACTIVE"),
            ("EMP102", "Priya Sharma", "priya.sharma@enterprise.com", "+91 98765 43211", 2, "Senior HR Manager", date(2023, 1, 15), "ACTIVE"),
            ("EMP103", "Rahul Verma", "rahul.verma@enterprise.com", "+91 98765 43212", 3, "Senior Financial Analyst", date(2023, 4, 10), "ACTIVE"),
            ("EMP104", "Sneha Patel", "sneha.patel@enterprise.com", "+91 98765 43213", 1, "Cloud DevOps Architect", date(2023, 6, 20), "ACTIVE"),
            ("EMP105", "Amit Singhania", "amit.s@enterprise.com", "+91 98765 43214", 5, "Head of Growth & Marketing", date(2023, 8, 1), "ACTIVE"),
            ("EMP106", "Ananya Roy", "ananya.roy@enterprise.com", "+91 98765 43215", 1, "Senior BI & Data Analyst", date(2023, 9, 15), "ACTIVE"),
            ("EMP107", "Vikram Malhotra", "vikram.m@enterprise.com", "+91 98765 43216", 4, "Enterprise Operations Lead", date(2023, 11, 1), "ACTIVE"),
            ("EMP108", "Neha Kapoor", "neha.kapoor@enterprise.com", "+91 98765 43217", 2, "Talent Acquisition Specialist", date(2024, 2, 15), "ACTIVE"),
            ("EMP109", "Suresh Nair", "suresh.nair@enterprise.com", "+91 98765 43218", 3, "Corporate Accounts Manager", date(2024, 3, 1), "ACTIVE"),
            ("EMP110", "Divya Menon", "divya.menon@enterprise.com", "+91 98765 43219", 1, "Lead UI/UX Designer", date(2024, 4, 10), "ACTIVE"),
            ("EMP111", "Rohan Gupta", "rohan.gupta@enterprise.com", "+91 98765 43220", 5, "Digital Marketing Strategist", date(2024, 5, 1), "ACTIVE"),
            ("EMP112", "Meera Joshi", "meera.joshi@enterprise.com", "+91 98765 43221", 1, "Senior QA Automation Engineer", date(2024, 6, 15), "ACTIVE"),
        ]
        cursor.executemany(
            """INSERT INTO employees 
               (employee_id, name, email, phone, department_id, designation, joining_date, status)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s);""",
            employees_data
        )
        print(f"[OK] Inserted {len(employees_data)} employees.")

        # 4. Insert Users with Secure Password Hashing
        admin_pwd = generate_password_hash("admin123")
        hr_pwd = generate_password_hash("hr123")
        emp_pwd = generate_password_hash("emp123")

        users_data = [
            ("EMP100", "admin", admin_pwd, "admin"),
            ("EMP102", "hr", hr_pwd, "hr"),
            ("EMP101", "emp101", emp_pwd, "employee"),
            ("EMP103", "emp103", emp_pwd, "employee"),
            ("EMP104", "emp104", emp_pwd, "employee"),
            ("EMP105", "emp105", emp_pwd, "employee"),
            ("EMP106", "emp106", emp_pwd, "employee"),
            ("EMP107", "emp107", emp_pwd, "employee"),
            ("EMP108", "emp108", emp_pwd, "employee"),
            ("EMP109", "emp109", emp_pwd, "employee"),
            ("EMP110", "emp110", emp_pwd, "employee"),
            ("EMP111", "emp111", emp_pwd, "employee"),
            ("EMP112", "emp112", emp_pwd, "employee"),
        ]
        cursor.executemany(
            "INSERT INTO users (employee_id, username, password_hash, role) VALUES (%s, %s, %s, %s);",
            users_data
        )
        print(f"[OK] Inserted {len(users_data)} users with hashed credentials.")

        # 5. Insert Leave Balances (Annual standard: CL 12, SL 10, EL 15, OL 3)
        balances = [
            (emp[0], 12.0, 10.0, 15.0, 3.0, 2026) for emp in employees_data
        ]
        cursor.executemany(
            """INSERT INTO leave_balance 
               (employee_id, casual_leave, sick_leave, earned_leave, optional_leave, year) 
               VALUES (%s, %s, %s, %s, %s, %s);""",
            balances
        )
        print("[OK] Initialized leave balances for all employees.")

        # 6. Seed Realistic Leave Requests
        # Let's add some approved leaves in September/October, plus pending requests for HR approval
        leave_reqs = [
            # Past approved leaves (balance deducted)
            ("EMP101", "Sick Leave", date(2026, 9, 14), date(2026, 9, 15), 2.0, "Viral fever and physician recommended rest", "APPROVED", "EMP102", "Approved. Take care and get well soon.", datetime(2026, 9, 13, 10, 30), datetime(2026, 9, 13, 11, 45)),
            ("EMP104", "Casual Leave", date(2026, 9, 21), date(2026, 9, 21), 1.0, "Family function attendance in hometown", "APPROVED", "EMP102", "Approved by HR.", datetime(2026, 9, 18, 9, 15), datetime(2026, 9, 18, 14, 0)),
            ("EMP106", "Casual Leave", date(2026, 10, 8), date(2026, 10, 8), 1.0, "Personal administrative errand", "APPROVED", "EMP102", "Approved.", datetime(2026, 10, 6, 16, 20), datetime(2026, 10, 7, 9, 30)),
            ("EMP109", "Earned Leave", date(2026, 9, 28), date(2026, 9, 30), 3.0, "Annual family vacation", "APPROVED", "EMP100", "Approved for Q3 leave cycle.", datetime(2026, 9, 20, 11, 0), datetime(2026, 9, 21, 15, 30)),
            
            # PENDING LEAVES (Active for HR approval demo!)
            ("EMP101", "Casual Leave", date(2026, 10, 15), date(2026, 10, 16), 2.0, "Attending sibling wedding ceremony", "PENDING", None, None, datetime(2026, 10, 7, 14, 15), None),
            ("EMP103", "Sick Leave", date(2026, 10, 12), date(2026, 10, 12), 1.0, "Dental root canal procedure appointment", "PENDING", None, None, datetime(2026, 10, 8, 10, 0), None),
            ("EMP107", "Earned Leave", date(2026, 10, 22), date(2026, 10, 24), 3.0, "Relocation and personal home maintenance", "PENDING", None, None, datetime(2026, 10, 8, 11, 30), None),
            ("EMP111", "Optional Holiday", date(2026, 10, 21), date(2026, 10, 21), 1.0, "Regional religious celebration", "PENDING", None, None, datetime(2026, 10, 8, 12, 10), None),

            # REJECTED LEAVE
            ("EMP105", "Earned Leave", date(2026, 9, 8), date(2026, 9, 10), 3.0, "Short notice holiday during product sprint release", "REJECTED", "EMP102", "Critical campaign launch week. Please reschedule after sprint.", datetime(2026, 9, 5, 15, 0), datetime(2026, 9, 6, 9, 0)),
        ]

        cursor.executemany(
            """INSERT INTO leave_requests 
               (employee_id, leave_type, start_date, end_date, total_days, reason, status, approved_by, admin_remarks, applied_at, action_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""",
            leave_reqs
        )
        print(f"[OK] Inserted {len(leave_reqs)} leave requests (4 Pending for live HR review).")

        # Deduct balance for approved leaves:
        cursor.execute("UPDATE leave_balance SET sick_leave = sick_leave - 2.0 WHERE employee_id = 'EMP101';")
        cursor.execute("UPDATE leave_balance SET casual_leave = casual_leave - 1.0 WHERE employee_id = 'EMP104';")
        cursor.execute("UPDATE leave_balance SET casual_leave = casual_leave - 1.0 WHERE employee_id = 'EMP106';")
        cursor.execute("UPDATE leave_balance SET earned_leave = earned_leave - 3.0 WHERE employee_id = 'EMP109';")

        # 7. Generate 35 days of Historical Attendance (Sept 1, 2026 to Oct 7, 2026 + Today Oct 8, 2026)
        start_cal_date = date(2026, 9, 1)
        today = date(2026, 10, 8)
        
        # Approved leave dates map: (emp_id, date) -> 'ON_LEAVE'
        approved_leaves_map = {
            ('EMP101', date(2026, 9, 14)): "Sick Leave",
            ('EMP101', date(2026, 9, 15)): "Sick Leave",
            ('EMP104', date(2026, 9, 21)): "Casual Leave",
            ('EMP106', date(2026, 10, 8)): "Casual Leave",
            ('EMP109', date(2026, 9, 28)): "Earned Leave",
            ('EMP109', date(2026, 9, 29)): "Earned Leave",
            ('EMP109', date(2026, 9, 30)): "Earned Leave",
        }

        attendance_records = []
        random.seed(42) # Consistent realistic data

        curr_date = start_cal_date
        emp_ids = [e[0] for e in employees_data]

        while curr_date < today:
            # Skip Saturday (5) and Sunday (6)
            if curr_date.weekday() not in (5, 6) and curr_date not in holiday_dates:
                for emp_id in emp_ids:
                    # Check if on approved leave
                    if (emp_id, curr_date) in approved_leaves_map:
                        attendance_records.append((
                            emp_id, curr_date, None, None, 0.0, 'ON_LEAVE', False, f"Approved {approved_leaves_map[(emp_id, curr_date)]}"
                        ))
                        continue

                    # Probability distribution for realistic enterprise data:
                    # 76% Present (On Time), 14% Late Arrival, 5% Half-day, 5% Absent
                    rand_val = random.random()

                    if rand_val < 0.05:
                        # ABSENT
                        attendance_records.append((
                            emp_id, curr_date, None, None, 0.0, 'ABSENT', False, 'Unplanned Absence'
                        ))
                    elif rand_val < 0.10:
                        # HALF DAY
                        check_in_h = 9
                        check_in_m = random.randint(0, 15)
                        check_in_t = time(check_in_h, check_in_m)
                        check_out_t = time(13, random.randint(20, 45))
                        hrs = round(4.0 + random.uniform(0.1, 0.6), 2)
                        attendance_records.append((
                            emp_id, curr_date, check_in_t, check_out_t, hrs, 'HALF_DAY', False, 'First half completed'
                        ))
                    elif rand_val < 0.24:
                        # LATE ARRIVAL (09:16 AM - 10:15 AM)
                        check_in_h = 9 if random.random() < 0.8 else 10
                        check_in_m = random.randint(16, 45) if check_in_h == 9 else random.randint(0, 15)
                        check_in_t = time(check_in_h, check_in_m)
                        check_out_h = 18
                        check_out_m = random.randint(15, 50)
                        check_out_t = time(check_out_h, check_out_m)
                        # working hours
                        dt_in = datetime.combine(curr_date, check_in_t)
                        dt_out = datetime.combine(curr_date, check_out_t)
                        hrs = round((dt_out - dt_in).total_seconds() / 3600.0, 2)
                        attendance_records.append((
                            emp_id, curr_date, check_in_t, check_out_t, hrs, 'LATE', True, 'Late arrival after 09:15 AM'
                        ))
                    else:
                        # PRESENT & ON TIME (08:45 AM - 09:14 AM)
                        check_in_h = 8 if random.random() < 0.4 else 9
                        check_in_m = random.randint(45, 59) if check_in_h == 8 else random.randint(0, 14)
                        check_in_t = time(check_in_h, check_in_m)
                        check_out_h = 18
                        check_out_m = random.randint(0, 40)
                        check_out_t = time(check_out_h, check_out_m)
                        dt_in = datetime.combine(curr_date, check_in_t)
                        dt_out = datetime.combine(curr_date, check_out_t)
                        hrs = round((dt_out - dt_in).total_seconds() / 3600.0, 2)
                        attendance_records.append((
                            emp_id, curr_date, check_in_t, check_out_t, hrs, 'PRESENT', False, 'Regular business hours'
                        ))
            curr_date += timedelta(days=1)

        # 8. TODAY's ATTENDANCE (2026-10-08)
        # Live status: Jestin is punched in at 09:08 AM, others punched in / out / late / on leave
        today_records = [
            ("EMP100", today, time(8, 50), None, 0.0, 'PRESENT', False, 'Admin in office'),
            ("EMP101", today, time(9, 8), None, 0.0, 'PRESENT', False, 'Checked in via web portal'), # Jestin
            ("EMP102", today, time(8, 55), None, 0.0, 'PRESENT', False, 'HR Operations active'),
            ("EMP103", today, time(9, 22), None, 0.0, 'LATE', True, 'Late arrival - traffic delay'),
            ("EMP104", today, time(9, 0), None, 0.0, 'PRESENT', False, 'Regular check-in'),
            ("EMP105", today, time(8, 50), time(18, 5), 9.25, 'PRESENT', False, 'Full day completed'),
            ("EMP106", today, None, None, 0.0, 'ON_LEAVE', False, 'Approved Casual Leave'),
            ("EMP107", today, time(9, 10), None, 0.0, 'PRESENT', False, 'Regular check-in'),
            ("EMP108", today, time(9, 35), None, 0.0, 'LATE', True, 'Late arrival after grace period'),
            ("EMP109", today, time(9, 2), None, 0.0, 'PRESENT', False, 'Regular check-in'),
            # EMP110 has not checked in yet today (demonstrates unmarked / absent candidate)
            ("EMP111", today, time(9, 12), None, 0.0, 'PRESENT', False, 'Regular check-in'),
            ("EMP112", today, time(9, 5), None, 0.0, 'PRESENT', False, 'Regular check-in'),
        ]

        all_attendance = attendance_records + today_records

        cursor.executemany(
            """INSERT INTO attendance 
               (employee_id, date, check_in, check_out, working_hours, status, is_late, remarks)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s);""",
            all_attendance
        )
        print(f"[OK] Inserted {len(all_attendance)} attendance records across September & October 2026.")

        # 9. Insert Initial Audit Logs
        audit_records = [
            (1, "admin", "admin", "SYSTEM_INIT", "127.0.0.1", "Initialized database schema and company attendance policies"),
            (1, "admin", "admin", "EMPLOYEE_CREATE", "127.0.0.1", "Enrolled 12 corporate employees across 5 departments"),
            (2, "hr", "hr", "LEAVE_APPROVAL", "192.168.1.45", "Approved 2-day Sick Leave request for EMP101 (Jestin Roy)"),
            (3, "emp101", "employee", "ATTENDANCE_CHECKIN", "192.168.1.88", "EMP101 punched in at 09:08:00 AM (Status: PRESENT)"),
            (2, "hr", "hr", "LEAVE_APPROVAL", "192.168.1.45", "Approved 1-day Casual Leave request for EMP106 (Ananya Roy)"),
        ]
        cursor.executemany(
            "INSERT INTO audit_logs (user_id, username, role, action, ip_address, description) VALUES (%s, %s, %s, %s, %s, %s);",
            audit_records
        )
        print("[OK] Inserted initial audit log entries.")

    print("\nDatabase seeding completed successfully! All tables populated.")

if __name__ == "__main__":
    seed()
