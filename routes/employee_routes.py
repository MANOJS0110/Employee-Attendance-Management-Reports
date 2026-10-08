from flask import Blueprint, request, jsonify, session
from services.auth_service import login_required, role_required
from services.employee_service import (
    get_all_employees, get_employee_by_id, create_employee,
    update_employee, deactivate_employee, get_all_users
)
from services.department_service import (
    get_all_departments, add_department, update_department, delete_department
)

emp_bp = Blueprint('employee', __name__)

# --- Employee Endpoints ---
@emp_bp.route('/api/employees', methods=['GET'])
@login_required
def api_get_employees():
    dept_id = request.args.get('department_id')
    status = request.args.get('status')
    search = request.args.get('search')

    employees = get_all_employees(department_id=dept_id, status=status, search=search)
    for e in employees:
        e['joining_date'] = e['joining_date'].strftime('%Y-%m-%d')
    return jsonify({'success': True, 'employees': employees})

@emp_bp.route('/api/employees/<string:emp_id>', methods=['GET'])
@login_required
def api_get_employee_single(emp_id):
    emp = get_employee_by_id(emp_id)
    if not emp:
        return jsonify({'success': False, 'message': 'Employee not found'}), 404
    emp['joining_date'] = emp['joining_date'].strftime('%Y-%m-%d')
    return jsonify({'success': True, 'employee': emp})

@emp_bp.route('/api/employees', methods=['POST'])
@role_required('admin')
def api_create_employee():
    data = request.get_json() or {}
    res = create_employee(
        data,
        user_id=session.get('user_id'),
        username=session.get('username')
    )
    status_code = 201 if res['success'] else 400
    return jsonify(res), status_code

@emp_bp.route('/api/employees/<string:emp_id>', methods=['PUT'])
@role_required('admin')
def api_update_employee(emp_id):
    data = request.get_json() or {}
    res = update_employee(
        emp_id,
        data,
        user_id=session.get('user_id'),
        username=session.get('username')
    )
    status_code = 200 if res['success'] else 400
    return jsonify(res), status_code

@emp_bp.route('/api/employees/<string:emp_id>', methods=['DELETE'])
@role_required('admin')
def api_deactivate_employee(emp_id):
    res = deactivate_employee(
        emp_id,
        user_id=session.get('user_id'),
        username=session.get('username')
    )
    status_code = 200 if res['success'] else 400
    return jsonify(res), status_code

# --- Department Endpoints ---
@emp_bp.route('/api/departments', methods=['GET'])
@login_required
def api_get_departments():
    depts = get_all_departments()
    return jsonify({'success': True, 'departments': depts})

@emp_bp.route('/api/departments', methods=['POST'])
@role_required('admin')
def api_add_department():
    data = request.get_json() or {}
    name = data.get('department_name')
    desc = data.get('description')
    res = add_department(name, desc, user_id=session.get('user_id'), username=session.get('username'))
    status_code = 201 if res['success'] else 400
    return jsonify(res), status_code

@emp_bp.route('/api/departments/<int:dept_id>', methods=['PUT'])
@role_required('admin')
def api_update_department(dept_id):
    data = request.get_json() or {}
    name = data.get('department_name')
    desc = data.get('description')
    res = update_department(dept_id, name, desc, user_id=session.get('user_id'), username=session.get('username'))
    status_code = 200 if res['success'] else 400
    return jsonify(res), status_code

@emp_bp.route('/api/departments/<int:dept_id>', methods=['DELETE'])
@role_required('admin')
def api_delete_department(dept_id):
    res = delete_department(dept_id, user_id=session.get('user_id'), username=session.get('username'))
    status_code = 200 if res['success'] else 400
    return jsonify(res), status_code

# --- User Accounts Endpoint ---
@emp_bp.route('/api/users', methods=['GET'])
@role_required('admin')
def api_get_users():
    users = get_all_users()
    for u in users:
        if u.get('last_login'):
            u['last_login'] = u['last_login'].strftime('%Y-%m-%d %I:%M %p')
    return jsonify({'success': True, 'users': users})
