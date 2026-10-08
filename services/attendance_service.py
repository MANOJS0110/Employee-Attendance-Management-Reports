from datetime import datetime, date, time, timedelta
from db import get_db_cursor
from config import Config
from services.audit_service import log_audit_action
import logging

logger = logging.getLogger(__name__)

def record_check_in(employee_id, user_id=None, username=None, remarks=None):
    """
    Records an employee check-in for the current day.
    Evaluates late arrival against the company grace period threshold (09:15 AM).
    """
    now = datetime.now()
    today = now.date()
    current_time = now.time()

    with get_db_cursor(commit=True) as cursor:
        # Check existing record for today
        cursor.execute(
            "SELECT * FROM attendance WHERE employee_id = %s AND date = %s;",
            (employee_id, today)
        )
        existing = cursor.fetchone()

        if existing and existing['check_in'] is not None:
            return {
                'success': False,
                'message': f"Already checked in today at {existing['check_in'].strftime('%I:%M %p')}"
            }

        # Determine late status based on company policy (09:15 AM)
        is_late = current_time > Config.LATE_THRESHOLD_TIME
        status = 'LATE' if is_late else 'PRESENT'
        default_remarks = remarks or ('Late check-in after grace period' if is_late else 'Regular check-in')

        if existing:
            # Update existing placeholder/absent record
            cursor.execute(
                """UPDATE attendance 
                   SET check_in = %s, status = %s, is_late = %s, remarks = %s, updated_at = NOW()
                   WHERE attendance_id = %s;""",
                (current_time, status, is_late, default_remarks, existing['attendance_id'])
            )
        else:
            # Insert new attendance entry
            cursor.execute(
                """INSERT INTO attendance 
                   (employee_id, date, check_in, status, is_late, remarks)
                   VALUES (%s, %s, %s, %s, %s, %s);""",
                (employee_id, today, current_time, status, is_late, default_remarks)
            )

        if username:
            log_audit_action(
                user_id, username, 'employee', 'ATTENDANCE_CHECKIN',
                f"Employee {employee_id} checked in at {current_time.strftime('%I:%M:%S %p')} (Status: {status})"
            )

        return {
            'success': True,
            'message': f"Check-in recorded at {current_time.strftime('%I:%M %p')} ({'Late Arrival' if is_late else 'On Time'})",
            'check_in': current_time.strftime('%I:%M %p'),
            'status': status,
            'is_late': is_late
        }

def record_check_out(employee_id, user_id=None, username=None, remarks=None):
    """
    Records an employee check-out for the current day.
    Calculates total hours worked and updates status (Full Day, Half Day).
    """
    now = datetime.now()
    today = now.date()
    current_time = now.time()

    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "SELECT * FROM attendance WHERE employee_id = %s AND date = %s;",
            (employee_id, today)
        )
        record = cursor.fetchone()

        if not record or record['check_in'] is None:
            return {
                'success': False,
                'message': "No check-in record found for today. Please check in first."
            }

        if record['check_out'] is not None:
            return {
                'success': False,
                'message': f"Already checked out today at {record['check_out'].strftime('%I:%M %p')}"
            }

        check_in_time = record['check_in']
        # Compute working hours
        # check_in_time might be datetime.time or timedelta
        if isinstance(check_in_time, timedelta):
            # Convert timedelta to time
            total_seconds = int(check_in_time.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            check_in_dt = datetime.combine(today, time(hours, minutes, seconds))
        else:
            check_in_dt = datetime.combine(today, check_in_time)

        check_out_dt = datetime.combine(today, current_time)
        diff_seconds = max(0, (check_out_dt - check_in_dt).total_seconds())
        working_hours = round(diff_seconds / 3600.0, 2)

        # Classification based on company working hour policy
        is_late = bool(record['is_late'])
        if working_hours < Config.HALF_DAY_HOURS:
            status = 'HALF_DAY'
        elif working_hours < Config.FULL_DAY_HOURS:
            status = 'HALF_DAY'
        else:
            status = 'LATE' if is_late else 'PRESENT'

        hours_str = f"{int(diff_seconds // 3600)}h {int((diff_seconds % 3600) // 60)}m"
        updated_remarks = remarks or f"Completed {hours_str}"

        cursor.execute(
            """UPDATE attendance 
               SET check_out = %s, working_hours = %s, status = %s, remarks = %s, updated_at = NOW()
               WHERE attendance_id = %s;""",
            (current_time, working_hours, status, updated_remarks, record['attendance_id'])
        )

        if username:
            log_audit_action(
                user_id, username, 'employee', 'ATTENDANCE_CHECKOUT',
                f"Employee {employee_id} checked out at {current_time.strftime('%I:%M:%S %p')} (Duration: {hours_str})"
            )

        return {
            'success': True,
            'message': f"Check-out successful! Total working time: {hours_str}",
            'check_out': current_time.strftime('%I:%M %p'),
            'working_hours': working_hours,
            'hours_formatted': hours_str,
            'status': status
        }

def get_today_employee_attendance(employee_id):
    """
    Fetches today's attendance record for an individual employee.
    """
    today = date.today()
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT * FROM attendance WHERE employee_id = %s AND date = %s;",
            (employee_id, today)
        )
        record = cursor.fetchone()

        if not record:
            return {
                'date': today.strftime('%Y-%m-%d'),
                'is_checked_in': False,
                'is_checked_out': False,
                'check_in': None,
                'check_out': None,
                'working_hours': 0.0,
                'status': 'NOT_CHECKED_IN'
            }

        def format_time_val(t):
            if not t:
                return None
            if isinstance(t, timedelta):
                secs = int(t.total_seconds())
                h = secs // 3600
                m = (secs % 3600) // 60
                return f"{h:02d}:{m:02d}"
            return t.strftime('%I:%M %p')

        return {
            'attendance_id': record['attendance_id'],
            'date': record['date'].strftime('%Y-%m-%d'),
            'is_checked_in': record['check_in'] is not None,
            'is_checked_out': record['check_out'] is not None,
            'check_in': format_time_val(record['check_in']),
            'check_out': format_time_val(record['check_out']),
            'working_hours': float(record['working_hours'] or 0.0),
            'status': record['status'],
            'is_late': bool(record['is_late'])
        }

def get_today_dashboard_summary():
    """
    HR/Admin overview for today:
    Total Employees, Present Today, Absent Today, On Leave, Late Today.
    """
    today = date.today()
    with get_db_cursor() as cursor:
        # Total active employees
        cursor.execute("SELECT COUNT(*) as total FROM employees WHERE status = 'ACTIVE';")
        total_employees = cursor.fetchone()['total']

        # Attendance counts for today
        cursor.execute(
            """SELECT status, is_late, COUNT(*) as cnt
               FROM attendance
               WHERE date = %s
               GROUP BY status, is_late;""",
            (today,)
        )
        rows = cursor.fetchall()

        present_today = 0
        late_today = 0
        on_leave_today = 0
        half_day_today = 0
        explicit_absent = 0

        for r in rows:
            st = r['status']
            cnt = r['cnt']
            if st in ('PRESENT', 'LATE', 'HALF_DAY'):
                present_today += cnt
            if r['is_late'] or st == 'LATE':
                late_today += cnt
            if st == 'ON_LEAVE':
                on_leave_today += cnt
            if st == 'HALF_DAY':
                half_day_today += cnt
            if st == 'ABSENT':
                explicit_absent += cnt

        # Absent = total employees - present - on leave
        absent_today = max(0, total_employees - present_today - on_leave_today)

        # Recent today records
        cursor.execute(
            """SELECT a.*, e.name as employee_name, e.designation, d.department_name
               FROM attendance a
               JOIN employees e ON a.employee_id = e.employee_id
               LEFT JOIN departments d ON e.department_id = d.department_id
               WHERE a.date = %s
               ORDER BY a.check_in ASC;""",
            (today,)
        )
        logs = cursor.fetchall()

        return {
            'date': today.strftime('%A, %B %d, %Y'),
            'total_employees': total_employees,
            'present_today': present_today,
            'absent_today': absent_today,
            'late_today': late_today,
            'on_leave_today': on_leave_today,
            'half_day_today': half_day_today,
            'logs': logs
        }

def get_employee_monthly_stats(employee_id, year=None, month=None):
    """
    Calculates monthly attendance percentage and counts for an employee.
    """
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    with get_db_cursor() as cursor:
        cursor.execute(
            """SELECT status, is_late, COUNT(*) as cnt, COALESCE(SUM(working_hours), 0) as total_hours
               FROM attendance
               WHERE employee_id = %s 
                 AND YEAR(date) = %s 
                 AND MONTH(date) = %s
               GROUP BY status, is_late;""",
            (employee_id, year, month)
        )
        rows = cursor.fetchall()

        present_cnt = 0
        late_cnt = 0
        absent_cnt = 0
        leave_cnt = 0
        half_day_cnt = 0
        total_hours = 0.0

        for r in rows:
            total_hours += float(r['total_hours'])
            st = r['status']
            cnt = r['cnt']
            if st == 'PRESENT':
                present_cnt += cnt
            elif st == 'LATE':
                late_cnt += cnt
                present_cnt += cnt
            elif st == 'HALF_DAY':
                half_day_cnt += cnt
                present_cnt += cnt
            elif st == 'ABSENT':
                absent_cnt += cnt
            elif st == 'ON_LEAVE':
                leave_cnt += cnt

        total_working_days = present_cnt + absent_cnt + leave_cnt
        attendance_pct = round((present_cnt / total_working_days * 100), 1) if total_working_days > 0 else 0.0

        return {
            'year': year,
            'month': month,
            'total_working_days': total_working_days,
            'present_days': present_cnt,
            'late_days': late_cnt,
            'half_days': half_day_cnt,
            'absent_days': absent_cnt,
            'leave_days': leave_cnt,
            'total_hours': round(total_hours, 1),
            'attendance_percentage': attendance_pct,
            'avg_daily_hours': round(total_hours / present_cnt, 1) if present_cnt > 0 else 0.0
        }

def mark_absent_for_unmarked_employees(target_date=None, user_id=None, username=None):
    """
    Automated batch job:
    Finds all active employees without an attendance entry for the date.
    Checks if an approved leave exists: marks 'ON_LEAVE'.
    Else: marks 'ABSENT'.
    """
    target_date = target_date or date.today()

    with get_db_cursor(commit=True) as cursor:
        # Find active employees without attendance for target_date
        cursor.execute(
            """SELECT e.employee_id, e.name
               FROM employees e
               WHERE e.status = 'ACTIVE'
                 AND e.employee_id NOT IN (
                     SELECT employee_id FROM attendance WHERE date = %s
                 );""",
            (target_date,)
        )
        unmarked = cursor.fetchall()

        if not unmarked:
            return {'success': True, 'count': 0, 'message': 'All employees already have attendance records for this date.'}

        count_marked = 0
        for emp in unmarked:
            emp_id = emp['employee_id']
            # Check for approved leave
            cursor.execute(
                """SELECT leave_type FROM leave_requests 
                   WHERE employee_id = %s 
                     AND status = 'APPROVED'
                     AND %s BETWEEN start_date AND end_date
                   LIMIT 1;""",
                (emp_id, target_date)
            )
            leave_row = cursor.fetchone()

            if leave_row:
                cursor.execute(
                    """INSERT INTO attendance (employee_id, date, status, remarks)
                       VALUES (%s, %s, 'ON_LEAVE', %s);""",
                    (emp_id, target_date, f"Approved {leave_row['leave_type']}")
                )
            else:
                cursor.execute(
                    """INSERT INTO attendance (employee_id, date, status, remarks)
                       VALUES (%s, %s, 'ABSENT', 'Automated End-of-Day Absence Recording');""",
                    (emp_id, target_date)
                )
            count_marked += 1

        if username:
            log_audit_action(
                user_id, username, 'admin', 'BATCH_ABSENT_JOB',
                f"Batch automated attendance job processed {count_marked} employees for {target_date.strftime('%Y-%m-%d')}."
            )

        return {
            'success': True,
            'count': count_marked,
            'message': f"Successfully processed {count_marked} employees for {target_date.strftime('%Y-%m-%d')}."
        }
