from flask import Blueprint, render_template, session, redirect, url_for
from services.auth_service import login_required, role_required
from services.attendance_service import (
    get_today_dashboard_summary, get_today_employee_attendance,
    get_employee_monthly_stats
)
from services.leave_service import (
    get_employee_leave_balances, get_pending_leave_requests,
    get_employee_leave_history
)
from services.employee_service import get_all_employees, get_all_users
from services.department_service import get_all_departments
from services.report_service import get_analytics_summary
from datetime import datetime

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def index():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('web.admin_dashboard'))
        elif role == 'hr':
            return redirect(url_for('web.hr_dashboard'))
        else:
            return redirect(url_for('web.employee_dashboard'))
    return redirect(url_for('web.login'))

@web_bp.route('/login')
def login():
    if 'user_id' in session:
        return redirect(url_for('web.index'))
    return render_template('login.html')

@web_bp.route('/employee/dashboard')
@login_required
def employee_dashboard():
    emp_id = session.get('employee_id')
    today_att = get_today_employee_attendance(emp_id)
    monthly_stats = get_employee_monthly_stats(emp_id)
    leave_balance = get_employee_leave_balances(emp_id)
    leave_history = get_employee_leave_history(emp_id, limit=5)

    return render_template(
        'employee_dashboard.html',
        today_att=today_att,
        monthly_stats=monthly_stats,
        leave_balance=leave_balance,
        leave_history=leave_history,
        current_time=datetime.now()
    )

@web_bp.route('/hr/dashboard')
@role_required('admin', 'hr')
def hr_dashboard():
    summary = get_today_dashboard_summary()
    pending_leaves = get_pending_leave_requests()
    analytics = get_analytics_summary()
    departments = get_all_departments()

    return render_template(
        'hr_dashboard.html',
        summary=summary,
        pending_leaves=pending_leaves,
        analytics=analytics,
        departments=departments,
        current_date=datetime.now().strftime('%A, %B %d, %Y')
    )

@web_bp.route('/admin/dashboard')
@role_required('admin')
def admin_dashboard():
    employees = get_all_employees()
    departments = get_all_departments()
    users = get_all_users()
    summary = get_today_dashboard_summary()
    analytics = get_analytics_summary()

    return render_template(
        'admin_dashboard.html',
        employees=employees,
        departments=departments,
        users=users,
        summary=summary,
        analytics=analytics
    )

@web_bp.route('/reports')
@login_required
def reports_page():
    now = datetime.now()
    departments = get_all_departments()
    analytics = get_analytics_summary(now.year, now.month)

    return render_template(
        'reports.html',
        departments=departments,
        analytics=analytics,
        current_year=now.year,
        current_month=now.month
    )

@web_bp.route('/powerbi')
@login_required
def powerbi_page():
    return render_template('powerbi.html')
