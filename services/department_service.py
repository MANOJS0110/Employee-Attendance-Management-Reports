from db import get_db_cursor
from services.audit_service import log_audit_action

def get_all_departments():
    """Retrieve list of all departments with active employee count."""
    with get_db_cursor() as cursor:
        cursor.execute(
            """SELECT d.department_id, d.department_name, d.description, d.created_at,
                      COUNT(e.employee_id) as total_employees
               FROM departments d
               LEFT JOIN employees e ON d.department_id = e.department_id AND e.status = 'ACTIVE'
               GROUP BY d.department_id, d.department_name, d.description, d.created_at
               ORDER BY d.department_name ASC;"""
        )
        return cursor.fetchall()

def add_department(name, description=None, user_id=None, username=None):
    """Create a new corporate department."""
    name = name.strip()
    if not name:
        return {'success': False, 'message': 'Department name cannot be empty.'}

    with get_db_cursor(commit=True) as cursor:
        cursor.execute("SELECT department_id FROM departments WHERE department_name = %s;", (name,))
        if cursor.fetchone():
            return {'success': False, 'message': f'Department "{name}" already exists.'}

        cursor.execute(
            "INSERT INTO departments (department_name, description) VALUES (%s, %s);",
            (name, description)
        )
        dep_id = cursor.lastrowid

        if username:
            log_audit_action(user_id, username, 'admin', 'DEPARTMENT_CREATE', f"Created department '{name}' (ID: {dep_id}).")

        return {'success': True, 'message': f'Department "{name}" created successfully.', 'department_id': dep_id}

def update_department(department_id, name, description=None, user_id=None, username=None):
    """Update department name and description."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE departments SET department_name = %s, description = %s WHERE department_id = %s;",
            (name, description, department_id)
        )
        if username:
            log_audit_action(user_id, username, 'admin', 'DEPARTMENT_UPDATE', f"Updated department ID {department_id} to '{name}'.")
        return {'success': True, 'message': 'Department updated successfully.'}

def delete_department(department_id, user_id=None, username=None):
    """Delete a department (sets employee department_id to NULL)."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM departments WHERE department_id = %s;", (department_id,))
        if username:
            log_audit_action(user_id, username, 'admin', 'DEPARTMENT_DELETE', f"Deleted department ID {department_id}.")
        return {'success': True, 'message': 'Department deleted successfully.'}
