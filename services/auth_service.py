from functools import wraps
from flask import session, redirect, url_for, flash, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash
from db import get_db_cursor
from datetime import datetime
from services.audit_service import log_audit_action

def authenticate_user(username_or_email, password):
    """
    Validates user credentials against MySQL database.
    Supports login via username or email.
    """
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """SELECT u.user_id, u.employee_id, u.username, u.password_hash, u.role, u.is_active,
                      e.name as employee_name, e.email, e.designation, e.department_id, d.department_name
               FROM users u
               LEFT JOIN employees e ON u.employee_id = e.employee_id
               LEFT JOIN departments d ON e.department_id = d.department_id
               WHERE (u.username = %s OR e.email = %s);""",
            (username_or_email, username_or_email)
        )
        user = cursor.fetchone()

        if not user:
            return None, "Invalid username or password"

        if not user['is_active']:
            return None, "Account is deactivated. Please contact your administrator."

        if not check_password_hash(user['password_hash'], password):
            return None, "Invalid username or password"

        # Update last login timestamp
        cursor.execute(
            "UPDATE users SET last_login = %s WHERE user_id = %s;",
            (datetime.now(), user['user_id'])
        )

        # Log audit entry
        log_audit_action(
            user['user_id'],
            user['username'],
            user['role'],
            'USER_LOGIN',
            f"User '{user['username']}' logged in successfully as {user['role']}."
        )

        return user, None

def login_required(f):
    """Decorator to require login for views."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': 'Authentication required'}), 401
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('web.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    """Decorator to restrict access to specific roles (e.g. admin, hr)."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'message': 'Authentication required'}), 401
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('web.login'))

            user_role = session.get('role')
            if user_role not in allowed_roles:
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'message': 'Permission denied: unauthorized role'}), 403
                flash('Access denied. You do not have permissions for this section.', 'danger')
                return redirect(url_for('web.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def change_user_password(user_id, old_password, new_password):
    """Allow an authenticated user to update their password."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("SELECT password_hash, username, role FROM users WHERE user_id = %s;", (user_id,))
        row = cursor.fetchone()
        if not row:
            return False, "User not found"

        if not check_password_hash(row['password_hash'], old_password):
            return False, "Current password does not match"

        if len(new_password) < 6:
            return False, "Password must be at least 6 characters"

        new_hash = generate_password_hash(new_password)
        cursor.execute("UPDATE users SET password_hash = %s WHERE user_id = %s;", (new_hash, user_id))
        
        log_audit_action(user_id, row['username'], row['role'], 'PASSWORD_CHANGE', "User updated password")
        return True, "Password successfully updated"
