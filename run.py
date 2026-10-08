"""
Entry-point launcher for Employee Leave & Attendance Management System
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("  EMPLOYEE ATTENDANCE & WORKFORCE MANAGEMENT SYSTEM")
    print("  Flask REST API & Web Dashboard Active")
    print("  URL: http://127.0.0.1:5000")
    print("=" * 70 + "\n")
    app.run(host='127.0.0.1', port=5000, debug=False)
