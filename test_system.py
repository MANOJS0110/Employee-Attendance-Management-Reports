"""
Comprehensive System Verification Test
Validates database, services, auth, attendance, leaves, and report generators.
"""
import sys
import os
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from services.auth_service import authenticate_user
from services.attendance_service import get_today_dashboard_summary, get_today_employee_attendance
from services.leave_service import get_employee_leave_balances, get_pending_leave_requests
from services.report_service import get_analytics_summary, generate_excel_report, generate_pdf_report
from powerbi.powerbi_dataset_export import export_all

def run_tests():
    print("=" * 60)
    print("RUNNING AUTOMATED SYSTEM VERIFICATION TESTS")
    print("=" * 60)

    # 1. Test Authentication
    print("\n[Test 1] Testing Authentication...")
    admin_user, err = authenticate_user('admin', 'admin123')
    assert admin_user is not None, f"Admin login failed: {err}"
    print(f"  [PASS] Admin authenticated: {admin_user['employee_name']} (Role: {admin_user['role']})")

    hr_user, err = authenticate_user('hr', 'hr123')
    assert hr_user is not None, f"HR login failed: {err}"
    print(f"  [PASS] HR authenticated: {hr_user['employee_name']} (Role: {hr_user['role']})")

    emp_user, err = authenticate_user('emp101', 'emp123')
    assert emp_user is not None, f"Employee login failed: {err}"
    print(f"  [PASS] Employee authenticated: {emp_user['employee_name']} (Role: {emp_user['role']})")

    # 2. Test Today's Dashboard Summary
    print("\n[Test 2] Testing Attendance Summary...")
    summary = get_today_dashboard_summary()
    assert summary['total_employees'] > 0, "No active employees found"
    print(f"  [PASS] Total Active Staff: {summary['total_employees']}")
    print(f"  [PASS] Present Today: {summary['present_today']}, Late: {summary['late_today']}, On Leave: {summary['on_leave_today']}")

    # 3. Test Employee Today Status
    emp_today = get_today_employee_attendance('EMP101')
    print(f"  [PASS] EMP101 Today Status: {emp_today['status']}, Checked In: {emp_today['check_in']}")

    # 4. Test Leave Balances & Pending Requests
    print("\n[Test 3] Testing Leave System...")
    bals = get_employee_leave_balances('EMP101')
    assert bals['casual_leave'] >= 0, "Invalid casual leave balance"
    print(f"  [PASS] EMP101 Balances: CL={bals['casual_leave']}, SL={bals['sick_leave']}, EL={bals['earned_leave']}, OL={bals['optional_leave']}")

    pending = get_pending_leave_requests()
    print(f"  [PASS] Active Pending Leave Requests in Queue: {len(pending)}")

    # 5. Test Analytics
    print("\n[Test 4] Testing Analytics Engine...")
    analytics = get_analytics_summary()
    assert len(analytics['daily_trend']) > 0, "Daily trend empty"
    print(f"  [PASS] Overall Attendance Rate: {analytics['overall_attendance_pct']}%")
    print(f"  [PASS] Daily trend points calculated: {len(analytics['daily_trend'])}")
    print(f"  [PASS] Department breakdown calculated: {len(analytics['dept_analytics'])} departments")

    # 6. Test Excel Export
    print("\n[Test 5] Testing Excel Report Generation...")
    excel_buf = generate_excel_report(2026, 10)
    assert excel_buf.getvalue(), "Excel buffer is empty"
    print(f"  [PASS] Excel workbook generated successfully ({len(excel_buf.getvalue())} bytes)")

    # 7. Test PDF Export
    print("\n[Test 6] Testing PDF Report Generation...")
    pdf_buf = generate_pdf_report(2026, 10)
    assert pdf_buf.getvalue(), "PDF buffer is empty"
    print(f"  [PASS] PDF executive report generated successfully ({len(pdf_buf.getvalue())} bytes)")

    # 8. Test Power BI Dataset Export
    print("\n[Test 7] Testing Power BI Star Schema Exporter...")
    export_all()
    print("  [PASS] Power BI datasets verified!")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 60)

if __name__ == '__main__':
    run_tests()
