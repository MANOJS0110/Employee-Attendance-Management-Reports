from flask import Blueprint, request, jsonify, session
from services.auth_service import login_required, role_required
from services.leave_service import (
    apply_leave, approve_leave_request, reject_leave_request,
    get_employee_leave_balances, get_pending_leave_requests,
    get_employee_leave_history
)

leave_bp = Blueprint('leave', __name__)

@leave_bp.route('/api/leaves/apply', methods=['POST'])
@login_required
def api_apply_leave():
    emp_id = session.get('employee_id')
    if not emp_id:
        return jsonify({'success': False, 'message': 'No employee profile linked.'}), 400

    data = request.get_json() or {}
    leave_type = data.get('leave_type')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    reason = data.get('reason', '').strip()

    if not leave_type or not start_date or not end_date or not reason:
        return jsonify({'success': False, 'message': 'Leave type, start date, end date, and reason are required.'}), 400

    res = apply_leave(
        employee_id=emp_id,
        leave_type=leave_type,
        start_date_str=start_date,
        end_date_str=end_date,
        reason=reason,
        user_id=session.get('user_id'),
        username=session.get('username')
    )
    status_code = 200 if res['success'] else 400
    return jsonify(res), status_code

@leave_bp.route('/api/leaves/balance', methods=['GET'])
@login_required
def api_leave_balance():
    emp_id = request.args.get('employee_id') or session.get('employee_id')
    if emp_id != session.get('employee_id') and session.get('role') not in ('admin', 'hr'):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403

    balances = get_employee_leave_balances(emp_id)
    return jsonify({'success': True, 'balance': balances})

@leave_bp.route('/api/leaves/my-leaves', methods=['GET'])
@login_required
def api_my_leaves():
    emp_id = session.get('employee_id')
    leaves = get_employee_leave_history(emp_id)
    for l in leaves:
        l['start_date'] = l['start_date'].strftime('%Y-%m-%d')
        l['end_date'] = l['end_date'].strftime('%Y-%m-%d')
        l['applied_at'] = l['applied_at'].strftime('%Y-%m-%d %I:%M %p') if l.get('applied_at') else None
        l['total_days'] = float(l['total_days'])
    return jsonify({'success': True, 'leaves': leaves})

@leave_bp.route('/api/leaves/pending', methods=['GET'])
@role_required('admin', 'hr')
def api_pending_leaves():
    pending = get_pending_leave_requests()
    for l in pending:
        l['start_date'] = l['start_date'].strftime('%Y-%m-%d')
        l['end_date'] = l['end_date'].strftime('%Y-%m-%d')
        l['applied_at'] = l['applied_at'].strftime('%Y-%m-%d %I:%M %p') if l.get('applied_at') else None
        l['total_days'] = float(l['total_days'])
    return jsonify({'success': True, 'pending_leaves': pending})

@leave_bp.route('/api/leaves/<int:leave_id>/approve', methods=['POST'])
@role_required('admin', 'hr')
def api_approve_leave(leave_id):
    data = request.get_json() or {}
    admin_remarks = data.get('remarks', 'Approved by HR/Management')
    reviewer_emp_id = session.get('employee_id')

    res = approve_leave_request(
        leave_id=leave_id,
        reviewer_emp_id=reviewer_emp_id,
        admin_remarks=admin_remarks,
        user_id=session.get('user_id'),
        username=session.get('username')
    )
    status_code = 200 if res['success'] else 400
    return jsonify(res), status_code

@leave_bp.route('/api/leaves/<int:leave_id>/reject', methods=['POST'])
@role_required('admin', 'hr')
def api_reject_leave(leave_id):
    data = request.get_json() or {}
    admin_remarks = data.get('remarks', 'Rejected by HR/Management')
    reviewer_emp_id = session.get('employee_id')

    res = reject_leave_request(
        leave_id=leave_id,
        reviewer_emp_id=reviewer_emp_id,
        admin_remarks=admin_remarks,
        user_id=session.get('user_id'),
        username=session.get('username')
    )
    status_code = 200 if res['success'] else 400
    return jsonify(res), status_code
