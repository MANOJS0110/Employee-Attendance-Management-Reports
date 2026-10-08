from db import get_db_cursor
from werkzeug.security import generate_password_hash
from services.audit_service import log_audit_action
from datetime import datetime

def get_all_employees(department_id=None, status=None, search=None):
    """Retrieve employees with optional department, status, and search filters."""
    query = """
        SELECT e.*, d.department_name, u.user_id, u.username, u.role, u.is_active as user_active
        FROM employees e
        LEFT JOIN departments d ON e.department_id = d.department_id
        LEFT JOIN users u ON e.employee_id = u.employee_id
        WHERE 1=1
    """
    params = []

    if department_id:
        query += " AND e.department_id = %s"
        params.append(department_id)

    if status:
        query += " AND e.status = %s"
        params.append(status)

    if search:
        query += " AND (e.name LIKE %s OR e.employee_id LIKE %s OR e.email LIKE %s OR e.designation LIKE %s)"
        search_pattern = f"%{search}%"
        params.extend([search_pattern, search_pattern, search_pattern, search_pattern])

    query += " ORDER BY e.employee_id ASC;"

    with get_db_cursor() as cursor:
        cursor.execute(query, tuple(params))
        return cursor.fetchall()

def get_employee_by_id(employee_id):
    """Retrieve full employee profile by ID."""
    with get_db_cursor() as cursor:
        cursor.execute(
            """SELECT e.*, d.department_name, u.user_id, u.username, u.role, u.is_active,
                      lb.casual_leave, lb.sick_leave, lb.earned_leave, lb.optional_leave
               FROM employees e
               LEFT JOIN departments d ON e.department_id = d.department_id
               LEFT JOIN users u ON e.employee_id = u.employee_id
               LEFT JOIN leave_balance lb ON e.employee_id = lb.employee_id
               WHERE e.employee_id = %s;""",
            (employee_id,)
        )
        return cursor.fetchone()

def create_employee(data, user_id=None, username=None):
    """
    Creates a new employee record, initializes leave balance,
    and provisions their system user account.
    """
    emp_id = data.get('employee_id', '').strip().upper()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    department_id = data.get('department_id') or None
    designation = data.get('designation', '').strip()
    joining_date = data.get('joining_date') or datetime.now().date()
    role = data.get('role', 'employee').lower()
    login_user = data.get('username', '').strip() or emp_id.lower()
    password = data.get('password', 'emp123')

    if not emp_id or not name or not email:
        return {'success': False, 'message': 'Employee ID, Name, and Email are required.'}

    with get_db_cursor(commit=True) as cursor:
        # Check duplicate employee_id or email
        cursor.execute("SELECT employee_id FROM employees WHERE employee_id = %s OR email = %s;", (emp_id, email))
        if cursor.fetchone():
            return {'success': False, 'message': f'Employee with ID "{emp_id}" or email "{email}" already exists.'}

        # Check duplicate username
        cursor.execute("SELECT user_id FROM users WHERE username = %s;", (login_user,))
        if cursor.fetchone():
            return {'success': False, 'message': f'Username "{login_user}" is already taken.'}

        # Insert Employee
        cursor.execute(
            """INSERT INTO employees (employee_id, name, email, phone, department_id, designation, joining_date, status)
               VALUES (%s, %s, %s, %s, %s, %s, %s, 'ACTIVE');""",
            (emp_id, name, email, phone, department_id, designation, joining_date)
        )

        # Provision User Account
        pwd_hash = generate_password_hash(password)
        cursor.execute(
            """INSERT INTO users (employee_id, username, password_hash, role, is_active)
               VALUES (%s, %s, %s, %s, TRUE);""",
            (emp_id, login_user, pwd_hash, role)
        )

        # Initialize standard leave balance
        cursor.execute(
            """INSERT INTO leave_balance (employee_id, casual_leave, sick_leave, earned_leave, optional_leave, year)
               VALUES (%s, 12.0, 10.0, 15.0, 3.0, YEAR(CURDATE()));""",
            (emp_id,)
        )

        if username:
            log_audit_action(
                user_id, username, 'admin', 'EMPLOYEE_CREATE',
                f"Registered new employee {emp_id} ({name}) with user account '{login_user}' and role '{role}'."
            )

        return {'success': True, 'message': f'Employee {name} ({emp_id}) enrolled successfully.'}

def update_employee(employee_id, data, user_id=None, username=None):
    """Update employee details."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """UPDATE employees 
               SET name = %s, email = %s, phone = %s, department_id = %s, 
                   designation = %s, status = %s
               WHERE employee_id = %s;""",
            (data['name'], data['email'], data['phone'], data.get('department_id'),
             data['designation'], data.get('status', 'ACTIVE'), employee_id)
        )

        # Optionally update user role if provided
        if 'role' in data:
            cursor.execute(
                "UPDATE users SET role = %s WHERE employee_id = %s;",
                (data['role'], employee_id)
            )

        if username:
            log_audit_action(
                user_id, username, 'admin', 'EMPLOYEE_UPDATE',
                f"Updated employee record for {employee_id} ({data['name']})."
            )

        return {'success': True, 'message': f'Employee {employee_id} updated successfully.'}

def deactivate_employee(employee_id, user_id=None, username=None):
    """Deactivate an employee and disable their login."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("UPDATE employees SET status = 'INACTIVE' WHERE employee_id = %s;", (employee_id,))
        cursor.execute("UPDATE users SET is_active = FALSE WHERE employee_id = %s;", (employee_id,))

        if username:
            log_audit_action(
                user_id, username, 'admin', 'EMPLOYEE_DEACTIVATE',
                f"Deactivated employee {employee_id} and disabled login access."
            )

        return {'success': True, 'message': f'Employee {employee_id} has been deactivated.'}

def get_all_users():
    """Retrieve all system user logins."""
    with get_db_cursor() as cursor:
        cursor.execute(
            """SELECT u.user_id, u.employee_id, u.username, u.role, u.is_active, u.last_login, u.created_at,
                      e.name as employee_name, d.department_name
               FROM users u
               LEFT JOIN employees e ON u.employee_id = e.employee_id
               LEFT JOIN departments d ON e.department_id = d.department_id
               ORDER BY u.user_id ASC;"""
        )
        return cursor.fetchall()
