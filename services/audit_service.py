from db import get_db_cursor
from flask import request
import logging

logger = logging.getLogger(__name__)

def log_audit_action(user_id, username, role, action, description, ip_address=None):
    """
    Log an event or administrative action into audit_logs.
    """
    if not ip_address:
        try:
            ip_address = request.remote_addr or '127.0.0.1'
        except Exception:
            ip_address = '127.0.0.1'

    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                """INSERT INTO audit_logs (user_id, username, role, action, ip_address, description)
                   VALUES (%s, %s, %s, %s, %s, %s);""",
                (user_id, username, role, action, ip_address, description)
            )
    except Exception as e:
        logger.error(f"Failed to record audit log: {e}")

def get_recent_audit_logs(limit=50):
    """
    Retrieve the most recent audit logs for admin review.
    """
    with get_db_cursor() as cursor:
        cursor.execute(
            """SELECT log_id, user_id, username, role, action, ip_address, description, created_at
               FROM audit_logs
               ORDER BY created_at DESC
               LIMIT %s;""",
            (limit,)
        )
        return cursor.fetchall()
