import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
from config import Config
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    """Create and return a new connection to MySQL database."""
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset='utf8mb4',
        cursorclass=DictCursor,
        autocommit=False
    )

@contextmanager
def get_db_cursor(commit=False):
    """
    Context manager for database operations.
    Yields a cursor and automatically handles commit/rollback and connection closing.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        if commit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error occurred: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()

def execute_query(sql, params=None, fetchone=False, fetchall=True, commit=False):
    """
    Helper function to execute SQL queries easily.
    """
    with get_db_cursor(commit=commit) as cursor:
        cursor.execute(sql, params or ())
        if commit:
            return cursor.lastrowid
        if fetchone:
            return cursor.fetchone()
        if fetchall:
            return cursor.fetchall()
        return None
