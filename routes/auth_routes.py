from flask import Blueprint, request, jsonify, session, redirect, url_for
from services.auth_service import authenticate_user, login_required, change_user_password
from services.audit_service import log_audit_action

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required.'}), 400

    user, error = authenticate_user(username, password)
    if error:
        return jsonify({'success': False, 'message': error}), 401

    # Store user in session
    session['user_id'] = user['user_id']
    session['employee_id'] = user['employee_id']
    session['username'] = user['username']
    session['role'] = user['role']
    session['name'] = user['employee_name']
    session['email'] = user['email']
    session['department_name'] = user['department_name']
    session['designation'] = user['designation']

    # Determine redirect URL based on role
    redirect_map = {
        'admin': '/admin/dashboard',
        'hr': '/hr/dashboard',
        'employee': '/employee/dashboard'
    }
    target_url = redirect_map.get(user['role'], '/employee/dashboard')

    return jsonify({
        'success': True,
        'message': f"Welcome back, {user['employee_name']}!",
        'role': user['role'],
        'redirect_url': target_url,
        'user': {
            'user_id': user['user_id'],
            'employee_id': user['employee_id'],
            'username': user['username'],
            'role': user['role'],
            'name': user['employee_name']
        }
    })

@auth_bp.route('/api/auth/logout', methods=['POST', 'GET'])
def api_logout():
    username = session.get('username')
    user_id = session.get('user_id')
    role = session.get('role', 'user')

    if username:
        log_audit_action(user_id, username, role, 'USER_LOGOUT', f"User '{username}' logged out.")

    session.clear()

    if request.path.startswith('/api/'):
        return jsonify({'success': True, 'message': 'Logged out successfully.'})
    return redirect(url_for('web.login'))

@auth_bp.route('/api/auth/me', methods=['GET'])
@login_required
def api_me():
    return jsonify({
        'success': True,
        'user': {
            'user_id': session.get('user_id'),
            'employee_id': session.get('employee_id'),
            'username': session.get('username'),
            'role': session.get('role'),
            'name': session.get('name'),
            'email': session.get('email'),
            'department': session.get('department_name'),
            'designation': session.get('designation')
        }
    })

@auth_bp.route('/api/auth/change-password', methods=['POST'])
@login_required
def api_change_password():
    data = request.get_json() or {}
    old_pwd = data.get('old_password', '')
    new_pwd = data.get('new_password', '')

    success, message = change_user_password(session['user_id'], old_pwd, new_pwd)
    status_code = 200 if success else 400
    return jsonify({'success': success, 'message': message}), status_code
