"""
Power BI Dataset Exporter
Extracts structured Star-Schema CSVs from MySQL for instant Power BI import.
Generates:
- Dim_Employees.csv
- Dim_Departments.csv
- Fact_Attendance.csv
- Fact_LeaveRequests.csv
- Fact_LeaveBalance.csv
- Dim_Date.csv
"""

import sys
import os
import csv
from datetime import datetime, date, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db import get_db_cursor

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

def export_all():
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"Exporting Power BI datasets to: {DATA_DIR}")

    with get_db_cursor() as cursor:
        # 1. Dim_Departments
        cursor.execute("SELECT department_id, department_name, description, created_at FROM departments;")
        depts = cursor.fetchall()
        write_csv('Dim_Departments.csv', depts, ['department_id', 'department_name', 'description', 'created_at'])

        # 2. Dim_Employees
        cursor.execute(
            """SELECT employee_id, name, email, phone, department_id, designation, 
                      joining_date, status, created_at 
               FROM employees;"""
        )
        emps = cursor.fetchall()
        write_csv('Dim_Employees.csv', emps, ['employee_id', 'name', 'email', 'phone', 'department_id', 'designation', 'joining_date', 'status', 'created_at'])

        # 3. Fact_Attendance
        cursor.execute(
            """SELECT attendance_id, employee_id, date, check_in, check_out, 
                      working_hours, status, is_late, remarks, created_at 
               FROM attendance;"""
        )
        att = cursor.fetchall()
        write_csv('Fact_Attendance.csv', att, ['attendance_id', 'employee_id', 'date', 'check_in', 'check_out', 'working_hours', 'status', 'is_late', 'remarks', 'created_at'])

        # 4. Fact_LeaveRequests
        cursor.execute(
            """SELECT leave_id, employee_id, leave_type, start_date, end_date, 
                      total_days, reason, status, approved_by, applied_at, action_at 
               FROM leave_requests;"""
        )
        leaves = cursor.fetchall()
        write_csv('Fact_LeaveRequests.csv', leaves, ['leave_id', 'employee_id', 'leave_type', 'start_date', 'end_date', 'total_days', 'reason', 'status', 'approved_by', 'applied_at', 'action_at'])

        # 5. Fact_LeaveBalance
        cursor.execute(
            """SELECT balance_id, employee_id, casual_leave, sick_leave, earned_leave, 
                      optional_leave, year, updated_at 
               FROM leave_balance;"""
        )
        bals = cursor.fetchall()
        write_csv('Fact_LeaveBalance.csv', bals, ['balance_id', 'employee_id', 'casual_leave', 'sick_leave', 'earned_leave', 'optional_leave', 'year', 'updated_at'])

        # 6. Dim_Date (2026 calendar dimension)
        date_rows = []
        cur_d = date(2026, 1, 1)
        end_d = date(2026, 12, 31)
        while cur_d <= end_d:
            is_wknd = cur_d.weekday() in (5, 6)
            date_rows.append({
                'Date': cur_d.strftime('%Y-%m-%d'),
                'Year': cur_d.year,
                'Quarter': f"Q{(cur_d.month - 1) // 3 + 1}",
                'Month': cur_d.month,
                'MonthName': cur_d.strftime('%B'),
                'Day': cur_d.day,
                'DayOfWeek': cur_d.strftime('%A'),
                'IsWeekend': 'Yes' if is_wknd else 'No',
                'IsWorkingDay': 'No' if is_wknd else 'Yes'
            })
            cur_d += timedelta(days=1)
        write_csv('Dim_Date.csv', date_rows, ['Date', 'Year', 'Quarter', 'Month', 'MonthName', 'Day', 'DayOfWeek', 'IsWeekend', 'IsWorkingDay'])

    print("[OK] All Power BI Star Schema tables exported successfully!")

def write_csv(filename, rows, fieldnames):
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            # Format dates/times
            clean_r = {}
            for k in fieldnames:
                v = r.get(k)
                if isinstance(v, (datetime, date)):
                    clean_r[k] = v.strftime('%Y-%m-%d %H:%M:%S' if isinstance(v, datetime) else '%Y-%m-%d')
                elif isinstance(v, timedelta):
                    secs = int(v.total_seconds())
                    clean_r[k] = f"{secs//3600:02d}:{(secs%3600)//60:02d}:{secs%60:02d}"
                else:
                    clean_r[k] = v
            writer.writerow(clean_r)
    print(f"  -> Generated {filename} ({len(rows)} records)")

if __name__ == '__main__':
    export_all()
