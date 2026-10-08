import os
from datetime import time
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'enterprise_attendance_secret_jwt_key_2026')
    
    # MySQL Database Configuration
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'ManojS@0311')
    DB_NAME = os.environ.get('DB_NAME', 'employee_attendance_db')
    
    # Company Attendance Policy Rules
    WORK_START_TIME = time(9, 0, 0)       # 09:00 AM
    GRACE_PERIOD_MINUTES = 15             # Up to 09:15 AM is ON TIME, after is LATE
    LATE_THRESHOLD_TIME = time(9, 15, 0)  # 09:15 AM
    WORK_END_TIME = time(18, 0, 0)        # 06:00 PM
    
    FULL_DAY_HOURS = 8.0                  # >= 8 hrs is Full Day (PRESENT)
    HALF_DAY_HOURS = 4.0                  # 4 to 8 hrs is Half Day
    SHORT_DAY_HOURS = 4.0                 # < 4 hrs is Short Day / Absent
    
    # Session Configuration
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400    # 24 hours
