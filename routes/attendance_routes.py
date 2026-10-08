from flask import Blueprint, request, jsonify, session
from services.auth_service import login_required, role_required
from services.attendance_service import (
    record_check_in, record_check_out, get_today_employee_attendance,
    get_today_dashboard_summary, get_employee_monthly_stats,
    mark_absent_for_unmarked_employees
)
from db import get_db_cursor
from datetime import date

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/api/attendance/check-in', methods=['POST'])
@login_required
def api_check_in():
    emp_id = session.get('employee_id')
    if not emp_id:
        return jsonify({'success': False, 'message': 'No employee associated with this account.'}), 400

    data = request.get_json() or {}
    remarks = data.get('remarks')
    result = record_check_in(
        emp_id,
        user_id=session.get('user_id'),
        username=session.get('username'),
        remarks=remarks
    )
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code

@attendance_bp.route('/api/attendance/check-out', methods=['POST'])
@login_required
def api_check_out():
    emp_id = session.get('employee_id')
    if not emp_id:
        return jsonify({'success': False, 'message': 'No employee associated with this account.'}), 400

    data = request.get_json() or {}
    remarks = data.get('remarks')
    result = record_check_out(
        emp_id,
        user_id=session.get('user_id'),
        username=session.get('username'),
        remarks=remarks
    )
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code

@attendance_bp.route('/api/attendance/today', methods=['GET'])
@login_required
def api_today_status():
    emp_id = request.args.get('employee_id') or session.get('employee_id')
    
    # If checking another employee, require HR or admin
    if emp_id != session.get('employee_id') and session.get('role') not in ('admin', 'hr'):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403

    status_data = get_today_employee_attendance(emp_id)
    return jsonify({'success': True, 'attendance': status_data})

@attendance_bp.route('/api/attendance/today-summary', methods=['GET'])
@role_required('admin', 'hr')
def api_today_summary():
    summary = get_today_dashboard_summary()
    return jsonify({'success': True, 'summary': summary})

@attendance_bp.route('/api/attendance/history', methods=['GET'])
@login_required
def api_attendance_history():
    emp_id = request.args.get('employee_id') or session.get('employee_id')

    if emp_id != session.get('employee_id') and session.get('role') not in ('admin', 'hr'):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403

    limit = int(request.args.get('limit', 30))

    with get_db_cursor() as cursor:
        cursor.execute(
            """SELECT a.*, e.name as employee_name, d.department_name
               FROM attendance a
               JOIN employees e ON a.employee_id = e.employee_id
               LEFT JOIN departments d ON e.department_id = d.department_id
               WHERE a.employee_id = %s
               ORDER BY a.date DESC
               LIMIT %s;""",
            (emp_id, limit)
        )
        records = cursor.fetchall()

    for r in records:
        r['date'] = r['date'].strftime('%Y-%m-%d')
        if r['check_in']:
            r['check_in'] = str(r['check_in'])
        if r['check_out']:
            r['check_out'] = str(r['check_out'])
        r['working_hours'] = float(r['working_hours'] or 0.0)

    return jsonify({'success': True, 'records': records})

@attendance_bp.route('/api/attendance/batch-absent', methods=['POST'])
@role_required('admin', 'hr')
def api_batch_absent():
    data = request.get_json() or {}
    target_date_str = data.get('date')
    target_date = None
    if target_date_str:
        try:
            target_date = date.fromisoformat(target_date_str)
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format'}), 400

    result = mark_absent_for_unmarked_employees(
        target_date=target_date,
        user_id=session.get('user_id'),
        username=session.get('username')
    )
    return jsonify(result)
