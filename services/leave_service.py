from datetime import datetime, date, timedelta
from db import get_db_cursor
from services.audit_service import log_audit_action
import logging

logger = logging.getLogger(__name__)

LEAVE_COLUMN_MAP = {
    'Casual Leave': 'casual_leave',
    'Sick Leave': 'sick_leave',
    'Earned Leave': 'earned_leave',
    'Optional Holiday': 'optional_leave'
}

def get_employee_leave_balances(employee_id):
    """Fetch current remaining leave balances for an employee."""
    with get_db_cursor() as cursor:
        cursor.execute(
            """SELECT casual_leave, sick_leave, earned_leave, optional_leave, year, updated_at
               FROM leave_balance
               WHERE employee_id = %s;""",
            (employee_id,)
        )
        row = cursor.fetchone()
        if not row:
            return {
                'casual_leave': 12.0,
                'sick_leave': 10.0,
                'earned_leave': 15.0,
                'optional_leave': 3.0,
                'total_remaining': 40.0
            }

        total_rem = (
            float(row['casual_leave']) + 
            float(row['sick_leave']) + 
            float(row['earned_leave']) + 
            float(row['optional_leave'])
        )

        return {
            'casual_leave': float(row['casual_leave']),
            'sick_leave': float(row['sick_leave']),
            'earned_leave': float(row['earned_leave']),
            'optional_leave': float(row['optional_leave']),
            'total_remaining': round(total_rem, 1),
            'year': row['year']
        }

def calculate_leave_days(start_date, end_date):
    """
    Calculate working days between two dates, excluding weekends and official public holidays.
    """
    with get_db_cursor() as cursor:
        cursor.execute("SELECT holiday_date FROM holidays;")
        holiday_rows = cursor.fetchall()
        holidays = {h['holiday_date'] for h in holiday_rows}

    cur = start_date
    working_days = 0.0
    while cur <= end_date:
        if cur.weekday() not in (5, 6) and cur not in holidays:
            working_days += 1.0
        cur += timedelta(days=1)
    return working_days

def apply_leave(employee_id, leave_type, start_date_str, end_date_str, reason, user_id=None, username=None):
    """
    Employee submits a new leave request.
    Validates date ranges, ensures no overlapping requests, and checks balance.
    """
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        return {'success': False, 'message': 'Invalid date format. Expected YYYY-MM-DD.'}

    if start_date > end_date:
        return {'success': False, 'message': 'Start date cannot be after end date.'}

    if leave_type not in LEAVE_COLUMN_MAP:
        return {'success': False, 'message': f"Invalid leave type: {leave_type}"}

    total_days = calculate_leave_days(start_date, end_date)
    if total_days <= 0:
        return {'success': False, 'message': 'Selected date range contains 0 working days (weekends or public holidays).'}

    balance_column = LEAVE_COLUMN_MAP[leave_type]

    with get_db_cursor(commit=True) as cursor:
        # Check for overlapping requests
        cursor.execute(
            """SELECT leave_id, start_date, end_date, status FROM leave_requests
               WHERE employee_id = %s
                 AND status IN ('PENDING', 'APPROVED')
                 AND (
                     (start_date <= %s AND end_date >= %s) OR
                     (start_date <= %s AND end_date >= %s) OR
                     (start_date >= %s AND end_date <= %s)
                 );""",
            (employee_id, start_date, start_date, end_date, end_date, start_date, end_date)
        )
        overlap = cursor.fetchone()
        if overlap:
            return {
                'success': False,
                'message': f"You already have an existing {overlap['status']} leave request covering these dates ({overlap['start_date']} to {overlap['end_date']})."
            }

        # Check balance
        cursor.execute(
            f"SELECT {balance_column} as current_bal FROM leave_balance WHERE employee_id = %s;",
            (employee_id,)
        )
        bal_row = cursor.fetchone()
        current_bal = float(bal_row['current_bal']) if bal_row else 0.0

        if total_days > current_bal:
            return {
                'success': False,
                'message': f"Insufficient {leave_type} balance! Requested: {total_days} days, Available: {current_bal} days."
            }

        # Insert leave request
        cursor.execute(
            """INSERT INTO leave_requests 
               (employee_id, leave_type, start_date, end_date, total_days, reason, status)
               VALUES (%s, %s, %s, %s, %s, %s, 'PENDING');""",
            (employee_id, leave_type, start_date, end_date, total_days, reason)
        )
        leave_id = cursor.lastrowid

        if username:
            log_audit_action(
                user_id, username, 'employee', 'LEAVE_APPLICATION',
                f"Employee {employee_id} submitted {leave_type} application for {total_days} days ({start_date} to {end_date})."
            )

        return {
            'success': True,
            'message': f"Leave application submitted successfully for {total_days} days (Status: Pending Approval).",
            'leave_id': leave_id,
            'total_days': total_days
        }

def approve_leave_request(leave_id, reviewer_emp_id, admin_remarks=None, user_id=None, username=None):
    """
    HR / Manager approves a pending leave request:
    - Deducts leave balance
    - Marks request APPROVED
    - Auto-updates attendance table with 'ON_LEAVE' status
    - Logs audit trail
    """
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("SELECT * FROM leave_requests WHERE leave_id = %s;", (leave_id,))
        req = cursor.fetchone()

        if not req:
            return {'success': False, 'message': 'Leave request not found.'}

        if req['status'] != 'PENDING':
            return {'success': False, 'message': f"Cannot approve request. Current status is already {req['status']}."}

        employee_id = req['employee_id']
        leave_type = req['leave_type']
        total_days = float(req['total_days'])
        balance_col = LEAVE_COLUMN_MAP.get(leave_type)

        # Ensure sufficient balance still exists
        cursor.execute(f"SELECT {balance_col} as bal FROM leave_balance WHERE employee_id = %s;", (employee_id,))
        bal_row = cursor.fetchone()
        current_bal = float(bal_row['bal']) if bal_row else 0.0

        if total_days > current_bal:
            return {'success': False, 'message': f"Cannot approve: Employee only has {current_bal} days of {leave_type} remaining."}

        # Deduct balance
        cursor.execute(
            f"UPDATE leave_balance SET {balance_col} = {balance_col} - %s WHERE employee_id = %s;",
            (total_days, employee_id)
        )

        # Update leave request status
        cursor.execute(
            """UPDATE leave_requests 
               SET status = 'APPROVED', approved_by = %s, admin_remarks = %s, action_at = NOW()
               WHERE leave_id = %s;""",
            (reviewer_emp_id, admin_remarks or 'Approved by HR', leave_id)
        )

        # Auto-create or update attendance records for working days in date range
        cur = req['start_date']
        end_date = req['end_date']
        while cur <= end_date:
            if cur.weekday() not in (5, 6): # Exclude weekends
                cursor.execute(
                    """INSERT INTO attendance (employee_id, date, status, remarks)
                       VALUES (%s, %s, 'ON_LEAVE', %s)
                       ON DUPLICATE KEY UPDATE status = 'ON_LEAVE', remarks = %s;""",
                    (employee_id, cur, f"Approved {leave_type}", f"Approved {leave_type}")
                )
            cur += timedelta(days=1)

        if username:
            log_audit_action(
                user_id, username, 'hr', 'LEAVE_APPROVAL',
                f"HR approved Leave Request #{leave_id} for {employee_id} ({total_days} days of {leave_type})."
            )

        return {
            'success': True,
            'message': f"Leave Request #{leave_id} approved. Balance deducted and attendance updated."
        }

def reject_leave_request(leave_id, reviewer_emp_id, admin_remarks=None, user_id=None, username=None):
    """
    HR / Manager rejects a pending leave request.
    Balance remains unchanged.
    """
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("SELECT * FROM leave_requests WHERE leave_id = %s;", (leave_id,))
        req = cursor.fetchone()

        if not req:
            return {'success': False, 'message': 'Leave request not found.'}

        if req['status'] != 'PENDING':
            return {'success': False, 'message': f"Cannot reject request. Current status is already {req['status']}."}

        cursor.execute(
            """UPDATE leave_requests 
               SET status = 'REJECTED', approved_by = %s, admin_remarks = %s, action_at = NOW()
               WHERE leave_id = %s;""",
            (reviewer_emp_id, admin_remarks or 'Rejected by HR/Management', leave_id)
        )

        if username:
            log_audit_action(
                user_id, username, 'hr', 'LEAVE_REJECTION',
                f"HR rejected Leave Request #{leave_id} for {req['employee_id']}. Reason: {admin_remarks}"
            )

        return {
            'success': True,
            'message': f"Leave Request #{leave_id} has been rejected."
        }

def get_pending_leave_requests():
    """Retrieve all pending leave requests for HR review."""
    with get_db_cursor() as cursor:
        cursor.execute(
            """SELECT lr.*, e.name as employee_name, e.designation, d.department_name,
                      lb.casual_leave, lb.sick_leave, lb.earned_leave, lb.optional_leave
               FROM leave_requests lr
               JOIN employees e ON lr.employee_id = e.employee_id
               LEFT JOIN departments d ON e.department_id = d.department_id
               LEFT JOIN leave_balance lb ON e.employee_id = lb.employee_id
               WHERE lr.status = 'PENDING'
               ORDER BY lr.applied_at ASC;"""
        )
        return cursor.fetchall()

def get_employee_leave_history(employee_id, limit=50):
    """Fetch leave application history for an employee."""
    with get_db_cursor() as cursor:
        cursor.execute(
            """SELECT lr.*, approver.name as approver_name
               FROM leave_requests lr
               LEFT JOIN employees approver ON lr.approved_by = approver.employee_id
               WHERE lr.employee_id = %s
               ORDER BY lr.applied_at DESC
               LIMIT %s;""",
            (employee_id, limit)
        )
        return cursor.fetchall()
